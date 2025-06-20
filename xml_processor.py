"""
Processador de XMLs para extração de dados de NFe
Compatível com XMLs importados via email, upload ou sistema automático
"""

import os
import xml.etree.ElementTree as ET
from datetime import datetime
import re
import logging
from models import db, XMLFile

logger = logging.getLogger(__name__)

def extract_xml_data(xml_content, filename=None):
    """
    Extrai dados completos do XML da NFe
    
    Args:
        xml_content (str): Conteúdo do XML
        filename (str): Nome do arquivo (opcional)
    
    Returns:
        dict: Dados extraídos do XML
    """
    try:
        # Parse do XML
        root = ET.fromstring(xml_content)
        
        # Namespaces comuns da NFe
        namespaces = {
            'nfe': 'http://www.portalfiscal.inf.br/nfe'
        }
        
        # Tentar encontrar o namespace automaticamente
        if root.tag.startswith('{'):
            namespace = root.tag.split('}')[0][1:]
            namespaces['nfe'] = namespace
        
        # Função auxiliar para buscar elementos com namespace
        def find_element(parent, path):
            # Tentar com namespace
            for ns_prefix, ns_uri in namespaces.items():
                full_path = path.replace('nfe:', f'{{{ns_uri}}}')
                element = parent.find(full_path)
                if element is not None:
                    return element
            
            # Tentar sem namespace
            simple_path = path.replace('nfe:', '')
            return parent.find(simple_path)
        
        # Função auxiliar para buscar texto de elemento
        def get_element_text(parent, path, default=''):
            element = find_element(parent, path)
            return element.text if element is not None and element.text else default
        
        # Extrair chave da NFe
        chave_nfe = ''
        infnfe = find_element(root, './/nfe:infNFe')
        if infnfe is not None and 'Id' in infnfe.attrib:
            chave_nfe = infnfe.attrib['Id'].replace('NFe', '')
        
        # Se não encontrou a chave, tentar extrair do nome do arquivo
        if not chave_nfe and filename:
            # Tentar extrair chave de 44 dígitos do nome do arquivo
            match = re.search(r'\d{44}', filename)
            if match:
                chave_nfe = match.group()
        
        # Dados do emitente
        emit = find_element(root, './/nfe:emit')
        cnpj_emitente = get_element_text(emit, 'nfe:CNPJ') if emit else ''
        nome_emitente = get_element_text(emit, 'nfe:xNome') if emit else ''
        
        # Endereço do emitente
        endereco_emit = find_element(emit, 'nfe:enderEmit') if emit else None
        emit_endereco = ''
        emit_cidade = ''
        emit_uf = ''
        emit_cep = ''
        
        if endereco_emit is not None:
            logradouro = get_element_text(endereco_emit, 'nfe:xLgr')
            numero = get_element_text(endereco_emit, 'nfe:nro')
            bairro = get_element_text(endereco_emit, 'nfe:xBairro')
            emit_cidade = get_element_text(endereco_emit, 'nfe:xMun')
            emit_uf = get_element_text(endereco_emit, 'nfe:UF')
            emit_cep = get_element_text(endereco_emit, 'nfe:CEP')
            
            # Montar endereço completo
            endereco_parts = [logradouro, numero, bairro]
            emit_endereco = ', '.join([part for part in endereco_parts if part])
        
        # Dados da NFe
        ide = find_element(root, './/nfe:ide')
        numero_nf = get_element_text(ide, 'nfe:nNF') if ide else ''
        serie_nf = get_element_text(ide, 'nfe:serie') if ide else ''
        
        # Data de emissão
        data_emissao = None
        if ide is not None:
            dhemi = get_element_text(ide, 'nfe:dhEmi')
            if dhemi:
                try:
                    # Formato: 2025-06-19T15:34:21-03:00
                    data_emissao = datetime.fromisoformat(dhemi.replace('Z', '+00:00').split('T')[0])
                except:
                    try:
                        # Formato alternativo: 2025-06-19
                        data_emissao = datetime.strptime(dhemi[:10], '%Y-%m-%d')
                    except:
                        logger.warning(f"Erro ao parsear data de emissão: {dhemi}")
        
        # Valor total
        total = find_element(root, './/nfe:total/nfe:ICMSTot')
        valor_total = 0.0
        if total is not None:
            vnf = get_element_text(total, 'nfe:vNF')
            try:
                valor_total = float(vnf) if vnf else 0.0
            except:
                valor_total = 0.0
        
        # Dados de transporte
        transp = find_element(root, './/nfe:transp')
        peso_bruto = 0.0
        quantidade_volumes = 0
        
        if transp is not None:
            # Peso bruto
            peso_liquido = get_element_text(transp, './/nfe:pesoL')
            peso_bruto_xml = get_element_text(transp, './/nfe:pesoB')
            
            if peso_bruto_xml:
                try:
                    peso_bruto = float(peso_bruto_xml)
                except:
                    pass
            elif peso_liquido:
                try:
                    peso_bruto = float(peso_liquido)
                except:
                    pass
            
            # Quantidade de volumes
            volumes = find_element(transp, './/nfe:vol')
            if volumes is not None:
                qvol = get_element_text(volumes, 'nfe:qVol')
                try:
                    quantidade_volumes = int(float(qvol)) if qvol else 1
                except:
                    quantidade_volumes = 1
            else:
                # Se não especificado, assume 1 volume
                quantidade_volumes = 1
        
        # Dados do destinatário
        dest = find_element(root, './/nfe:dest')
        destinatario_cnpj_cpf = ''
        destinatario_razao = ''
        destinatario_cidade = ''
        destinatario_uf = ''
        destinatario_endereco = ''
        destinatario_cep = ''
        
        if dest is not None:
            # CNPJ ou CPF
            cnpj_dest = get_element_text(dest, 'nfe:CNPJ')
            cpf_dest = get_element_text(dest, 'nfe:CPF')
            destinatario_cnpj_cpf = cnpj_dest or cpf_dest
            
            # Nome/Razão social
            destinatario_razao = get_element_text(dest, 'nfe:xNome')
            
            # Endereço do destinatário
            endereco_dest = find_element(dest, 'nfe:enderDest')
            if endereco_dest is not None:
                logradouro = get_element_text(endereco_dest, 'nfe:xLgr')
                numero = get_element_text(endereco_dest, 'nfe:nro')
                bairro = get_element_text(endereco_dest, 'nfe:xBairro')
                destinatario_cidade = get_element_text(endereco_dest, 'nfe:xMun')
                destinatario_uf = get_element_text(endereco_dest, 'nfe:UF')
                destinatario_cep = get_element_text(endereco_dest, 'nfe:CEP')
                
                # Montar endereço completo
                endereco_parts = [logradouro, numero, bairro]
                destinatario_endereco = ', '.join([part for part in endereco_parts if part])
        
        return {
            'invoice_key': chave_nfe,
            'cnpj_emitente': cnpj_emitente,
            'nome_emitente': nome_emitente,
            'numero_nf': numero_nf,
            'serie_nf': serie_nf,
            'data_emissao': data_emissao,
            'valor_total': valor_total,
            'peso_bruto': peso_bruto,
            'quantidade_volumes': quantidade_volumes,
            'remetente_razao': nome_emitente,  # Usar emitente como remetente
            'remetente_cidade': emit_cidade,
            'remetente_uf': emit_uf,
            'remetente_endereco': emit_endereco,
            'remetente_cep': emit_cep,
            'destinatario_cnpj_cpf': destinatario_cnpj_cpf,
            'destinatario_razao': destinatario_razao,
            'destinatario_cidade': destinatario_cidade,
            'destinatario_uf': destinatario_uf,
            'destinatario_endereco': destinatario_endereco,
            'destinatario_cep': destinatario_cep
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar XML: {e}")
        raise


def save_xml_to_database(user_id, xml_content, filename, import_type='UPLOAD'):
    """
    Salva XML no banco de dados após extrair os dados
    
    Args:
        user_id (int): ID do usuário
        xml_content (str): Conteúdo do XML
        filename (str): Nome do arquivo
        import_type (str): Tipo de importação (UPLOAD, EMAIL, SISTEMA)
    
    Returns:
        XMLFile: Objeto XMLFile criado
    """
    try:
        # Extrair dados do XML
        xml_data = extract_xml_data(xml_content, filename)
        
        # Verificar se já existe um XML com a mesma chave para este usuário
        existing_xml = XMLFile.query.filter_by(
            user_id=user_id,
            invoice_key=xml_data['invoice_key']
        ).first()
        
        if existing_xml:
            logger.warning(f"XML já existe no banco: {xml_data['invoice_key']}")
            return existing_xml
        
        # Definir caminho do arquivo
        upload_dir = f"uploads/xmls/{user_id}"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Gerar nome único para o arquivo
        safe_filename = re.sub(r'[^\w\-_\.]', '_', filename)
        file_path = os.path.join(upload_dir, safe_filename)
        
        # Salvar arquivo fisicamente
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(xml_content)
        
        # Criar registro no banco
        xml_file = XMLFile(
            user_id=user_id,
            filename=safe_filename,
            invoice_key=xml_data['invoice_key'],
            file_path=file_path,
            xml_content=xml_content,
            import_type=import_type,
            cnpj_emitente=xml_data['cnpj_emitente'][:14] if xml_data['cnpj_emitente'] else None,
            nome_emitente=xml_data['nome_emitente'][:255] if xml_data['nome_emitente'] else None,
            numero_nf=xml_data['numero_nf'][:50] if xml_data['numero_nf'] else None,
            serie_nf=xml_data['serie_nf'][:10] if xml_data['serie_nf'] else None,
            data_emissao=xml_data['data_emissao'],
            valor_total=xml_data['valor_total'],
            peso_bruto=xml_data['peso_bruto'],
            quantidade_volumes=xml_data['quantidade_volumes'],
            remetente_razao=xml_data['remetente_razao'][:255] if xml_data['remetente_razao'] else None,
            remetente_cidade=xml_data['remetente_cidade'][:100] if xml_data['remetente_cidade'] else None,
            remetente_uf=xml_data['remetente_uf'][:2] if xml_data['remetente_uf'] else None,
            remetente_endereco=xml_data['remetente_endereco'][:500] if xml_data['remetente_endereco'] else None,
            remetente_cep=xml_data['remetente_cep'][:8] if xml_data['remetente_cep'] else None,
            destinatario_cnpj_cpf=xml_data['destinatario_cnpj_cpf'][:14] if xml_data['destinatario_cnpj_cpf'] else None,
            destinatario_razao=xml_data['destinatario_razao'][:255] if xml_data['destinatario_razao'] else None,
            destinatario_cidade=xml_data['destinatario_cidade'][:100] if xml_data['destinatario_cidade'] else None,
            destinatario_uf=xml_data['destinatario_uf'][:2] if xml_data['destinatario_uf'] else None,
            destinatario_endereco=xml_data['destinatario_endereco'][:500] if xml_data['destinatario_endereco'] else None,
            destinatario_cep=xml_data['destinatario_cep'][:8] if xml_data['destinatario_cep'] else None
        )
        
        db.session.add(xml_file)
        db.session.commit()
        
        logger.info(f"XML salvo com sucesso: {xml_data['invoice_key']} via {import_type}")
        return xml_file
        
    except Exception as e:
        logger.error(f"Erro ao salvar XML no banco: {e}")
        db.session.rollback()
        raise