"""
XML Processor for database operations
Handles XML storage and processing for the system
"""
import logging
import xml.etree.ElementTree as ET
from datetime import datetime
from models import db, XMLFile
import re

logger = logging.getLogger(__name__)

def find_element_flexible(parent, tag_name, ns=None):
    """
    Busca um elemento de forma flexível, com e sem namespace
    """
    if ns:
        elem = parent.find(f'nfe:{tag_name}', ns)
        if elem is not None:
            return elem
    
    # Busca sem namespace
    elem = parent.find(tag_name)
    if elem is not None:
        return elem
    
    # Busca flexível por tag que contenha o nome
    for elem in parent.iter():
        if tag_name in elem.tag:
            return elem
    
    return None

def extract_xml_data(xml_content: str) -> dict:
    """
    Extrai dados estruturados do XML NFe para armazenamento completo no banco
    """
    try:
        # Parse do XML
        root = ET.fromstring(xml_content)
        
        # Namespaces comuns da NFe
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        
        # Dados da nota fiscal
        nf_data = {}
        
        # Encontrar o elemento infNFe com múltiplas estratégias
        infNFe = None
        
        # Estratégia 1: Busca com namespace completo
        infNFe = root.find('.//nfe:NFe/nfe:infNFe', ns)
        
        # Estratégia 2: Busca direta com namespace
        if infNFe is None:
            infNFe = root.find('.//nfe:infNFe', ns)
        
        # Estratégia 3: Busca sem namespace
        if infNFe is None:
            infNFe = root.find('.//infNFe')
            
        # Estratégia 4: Busca por tag que contenha 'infNFe'
        if infNFe is None:
            for elem in root.iter():
                if 'infNFe' in elem.tag:
                    infNFe = elem
                    break
                    
        # Log para debug
        if infNFe is None:
            logger.warning("Elemento infNFe não encontrado no XML")
            # Listar elementos encontrados para debug
            for elem in root.iter():
                logger.debug(f"Elemento encontrado: {elem.tag}")
        else:
            logger.info(f"infNFe encontrado: {infNFe.tag}")
        
        if infNFe is not None:
            # Identificação da NFe
            ide = infNFe.find('nfe:ide', ns)
            if ide is None:
                ide = infNFe.find('ide')  # Busca sem namespace
            if ide is None:
                # Busca flexível
                for elem in infNFe.iter():
                    if 'ide' in elem.tag:
                        ide = elem
                        break
                        
            if ide is not None:
                # Número da nota fiscal
                nNF = find_element_flexible(ide, 'nNF', ns)
                nf_data['numero_nf'] = nNF.text if nNF is not None else ''
                
                # Série da nota fiscal
                serie = find_element_flexible(ide, 'serie', ns)
                nf_data['serie_nf'] = serie.text if serie is not None else ''
                
                # Data de emissão
                dhEmi = find_element_flexible(ide, 'dhEmi', ns)
                if dhEmi is not None and dhEmi.text:
                    try:
                        # Formato: 2025-04-17T17:30:00-03:00
                        date_str = dhEmi.text.split('T')[0]  # Pega apenas a data
                        nf_data['data_emissao'] = datetime.strptime(date_str, '%Y-%m-%d').date()
                        logger.info(f"Data de emissão extraída: {nf_data['data_emissao']}")
                    except Exception as date_error:
                        logger.warning(f"Error parsing date: {date_error}")
                        nf_data['data_emissao'] = None
                else:
                    nf_data['data_emissao'] = None
                    logger.warning("Data de emissão não encontrada")
            
            # Emitente (Remetente) - busca flexível
            emit = find_element_flexible(infNFe, 'emit', ns)
            if emit is not None:
                logger.info("Emitente encontrado")
                
                # CNPJ do emitente
                cnpj = find_element_flexible(emit, 'CNPJ', ns)
                nf_data['cnpj_emitente'] = cnpj.text if cnpj is not None else ''
                if cnpj is not None:
                    logger.info(f"CNPJ extraído: {cnpj.text}")
                
                # Nome do emitente
                xNome = find_element_flexible(emit, 'xNome', ns)
                nome_emitente = xNome.text if xNome is not None else ''
                nf_data['nome_emitente'] = nome_emitente
                nf_data['remetente_razao'] = nome_emitente
                if xNome is not None:
                    logger.info(f"Nome emitente extraído: {nome_emitente}")
            else:
                logger.warning("Emitente não encontrado no XML")
                
                # Endereço do emitente/remetente
                enderEmit = emit.find('nfe:enderEmit', ns)
                if enderEmit is not None:
                    # UF
                    uf = enderEmit.find('nfe:UF', ns)
                    nf_data['remetente_uf'] = uf.text if uf is not None else ''
                    
                    # Município
                    xMun = enderEmit.find('nfe:xMun', ns)
                    nf_data['remetente_cidade'] = xMun.text if xMun is not None else ''
                    
                    # Endereço completo
                    xLgr = enderEmit.find('nfe:xLgr', ns)
                    nro = enderEmit.find('nfe:nro', ns)
                    xBairro = enderEmit.find('nfe:xBairro', ns)
                    
                    logradouro = xLgr.text if xLgr is not None else ''
                    numero = nro.text if nro is not None else ''
                    bairro = xBairro.text if xBairro is not None else ''
                    
                    endereco_parts = [p for p in [logradouro, numero, bairro] if p]
                    nf_data['remetente_endereco'] = ', '.join(endereco_parts)
                    
                    # CEP
                    cep = enderEmit.find('nfe:CEP', ns)
                    nf_data['remetente_cep'] = cep.text if cep is not None else ''
            
            # Destinatário
            dest = infNFe.find('nfe:dest', ns)
            if dest is not None:
                # CNPJ ou CPF do destinatário
                cnpj = dest.find('nfe:CNPJ', ns)
                cpf = dest.find('nfe:CPF', ns)
                nf_data['destinatario_cnpj_cpf'] = cnpj.text if cnpj is not None else (cpf.text if cpf is not None else '')
                
                # Nome do destinatário
                xNome = dest.find('nfe:xNome', ns)
                nf_data['destinatario_razao'] = xNome.text if xNome is not None else ''
                
                # Endereço do destinatário
                enderDest = dest.find('nfe:enderDest', ns)
                if enderDest is not None:
                    # UF
                    uf = enderDest.find('nfe:UF', ns)
                    nf_data['destinatario_uf'] = uf.text if uf is not None else ''
                    
                    # Município
                    xMun = enderDest.find('nfe:xMun', ns)
                    nf_data['destinatario_cidade'] = xMun.text if xMun is not None else ''
                    
                    # Endereço completo
                    xLgr = enderDest.find('nfe:xLgr', ns)
                    nro = enderDest.find('nfe:nro', ns)
                    xBairro = enderDest.find('nfe:xBairro', ns)
                    
                    logradouro = xLgr.text if xLgr is not None else ''
                    numero = nro.text if nro is not None else ''
                    bairro = xBairro.text if xBairro is not None else ''
                    
                    # Campos separados para uso na etiqueta
                    nf_data['destinatario_logradouro'] = logradouro
                    nf_data['destinatario_numero'] = numero
                    nf_data['destinatario_bairro'] = bairro
                    
                    endereco_parts = [p for p in [logradouro, numero, bairro] if p]
                    nf_data['destinatario_endereco'] = ', '.join(endereco_parts)
                    
                    # CEP
                    cep = enderDest.find('nfe:CEP', ns)
                    nf_data['destinatario_cep'] = cep.text if cep is not None else ''
            
            # Totais da NFe - busca flexível
            total = find_element_flexible(infNFe, 'total', ns)
            if total is not None:
                icms_tot = find_element_flexible(total, 'ICMSTot', ns)
                if icms_tot is not None:
                    vNF = find_element_flexible(icms_tot, 'vNF', ns)
                    if vNF is not None and vNF.text:
                        try:
                            nf_data['valor_total'] = float(vNF.text)
                            logger.info(f"Valor total extraído: R$ {vNF.text}")
                        except:
                            nf_data['valor_total'] = 0.0
                    else:
                        nf_data['valor_total'] = 0.0
                        logger.warning("vNF não encontrado")
                else:
                    nf_data['valor_total'] = 0.0
                    logger.warning("ICMSTot não encontrado")
            else:
                nf_data['valor_total'] = 0.0
                logger.warning("Total não encontrado")
            
            # Informações de transporte
            transp = infNFe.find('nfe:transp', ns)
            if transp is not None:
                # Buscar todos os volumes
                volumes = transp.findall('nfe:vol', ns)
                total_volumes = len(volumes)
                total_peso = 0.0
                
                for vol in volumes:
                    # Peso bruto
                    pesoB = vol.find('nfe:pesoB', ns)
                    if pesoB is not None and pesoB.text:
                        try:
                            total_peso += float(pesoB.text)
                        except:
                            pass
                    
                    # Quantidade de volumes (individual)
                    qVol = vol.find('nfe:qVol', ns)
                    if qVol is not None and qVol.text:
                        try:
                            vol_qty = int(float(qVol.text))
                            total_volumes = max(total_volumes, vol_qty)
                        except:
                            pass
                
                nf_data['peso_bruto'] = total_peso
                nf_data['volumes'] = total_volumes if total_volumes > 0 else 1
                nf_data['quantidade_volumes'] = total_volumes if total_volumes > 0 else 1
                
                # Transportadora
                transporta = transp.find('nfe:transporta', ns)
                if transporta is not None:
                    transp_nome = transporta.find('nfe:xNome', ns)
                    if transp_nome is not None and transp_nome.text:
                        nf_data['transportadora'] = transp_nome.text
                    
                    transp_cnpj = transporta.find('nfe:CNPJ', ns)
                    if transp_cnpj is not None and transp_cnpj.text:
                        nf_data['transportadora_cnpj'] = transp_cnpj.text
            else:
                nf_data['peso_bruto'] = 0.0
                nf_data['volumes'] = 0
                nf_data['quantidade_volumes'] = 0
        
        # Preencher campos padrão se não encontrados
        default_fields = {
            'numero_nf': '',
            'serie_nf': '',
            'data_emissao': None,
            'cnpj_emitente': '',
            'nome_emitente': '',
            'remetente_razao': '',
            'remetente_cidade': '',
            'remetente_uf': '',
            'remetente_endereco': '',
            'remetente_cep': '',
            'destinatario_cnpj_cpf': '',
            'destinatario_razao': '',
            'destinatario_cidade': '',
            'destinatario_uf': '',
            'destinatario_endereco': '',
            'destinatario_cep': '',
            'valor_total': 0.0,
            'peso_bruto': 0.0,
            'quantidade_volumes': 0
        }
        
        for field, default_value in default_fields.items():
            if field not in nf_data:
                nf_data[field] = default_value
        
        # Extrair dados de volume se disponível
        vol = transp.find('.//nfe:vol', ns) if transp is not None else None
        if vol is not None:
            qvol_elem = vol.find('nfe:qVol', ns)
            pesob_elem = vol.find('nfe:pesoB', ns)
            pesol_elem = vol.find('nfe:pesoL', ns)
            
            nf_data['quantidade_volumes'] = int(qvol_elem.text) if qvol_elem is not None and qvol_elem.text else 1
            nf_data['peso_bruto'] = float(pesob_elem.text) if pesob_elem is not None and pesob_elem.text else 0.0
            nf_data['peso_liquido'] = float(pesol_elem.text) if pesol_elem is not None and pesol_elem.text else 0.0
        
        # Chave de acesso
        chave_element = root.find('.//nfe:infNFe', ns)
        if chave_element is not None:
            nf_data['chave_acesso'] = chave_element.get('Id', '').replace('NFe', '') if chave_element.get('Id') else ''
        
        return nf_data
        
    except Exception as e:
        logger.error(f"Erro ao extrair dados do XML: {e}")
        return {}

def save_xml_to_database(user_id: int, invoice_key: str, xml_content: str, 
                        file_path: str, import_type: str = 'SISTEMA', job_id: str = None) -> int:
    """
    Save XML data to database with extracted information
    
    Args:
        user_id: ID do usuário
        invoice_key: Chave da nota fiscal
        xml_content: Conteúdo XML
        file_path: Caminho do arquivo
        import_type: Tipo de importação
        job_id: ID do job de download
        
    Returns:
        ID do XML salvo no banco
    """
    try:
        from models import XMLFile
        from new_app import db
        
        # Permitir downloads múltiplos - cada download gera registro único
        logger.info(f"Processando novo download para chave {invoice_key}")
        
        # Extrair dados do XML
        xml_data = extract_xml_data(xml_content)
        logger.info(f"Dados extraídos do XML: NF {xml_data.get('numero_nf')}, Valor R$ {xml_data.get('valor_total', 0):.2f}")
        
        # Criar novo registro com todos os dados extraídos
        xml_file = XMLFile(
            user_id=user_id,
            filename=f"{invoice_key}.xml",
            invoice_key=invoice_key,
            file_path=file_path,
            xml_content=xml_content,
            import_type=import_type,
            job_id=job_id,
            # Dados extraídos do XML
            cnpj_emitente=xml_data.get('cnpj_emitente', ''),
            nome_emitente=xml_data.get('nome_emitente', ''),
            numero_nf=xml_data.get('numero_nf', ''),
            serie_nf=xml_data.get('serie_nf', ''),
            data_emissao=xml_data.get('data_emissao'),
            valor_total=xml_data.get('valor_total', 0.0),
            peso_bruto=xml_data.get('peso_bruto', 0.0),
            quantidade_volumes=xml_data.get('quantidade_volumes', 1),
            remetente_razao=xml_data.get('remetente_razao', ''),
            remetente_cidade=xml_data.get('remetente_cidade', ''),
            remetente_uf=xml_data.get('remetente_uf', ''),
            remetente_endereco=xml_data.get('remetente_endereco', ''),
            remetente_cep=xml_data.get('remetente_cep', ''),
            destinatario_cnpj_cpf=xml_data.get('destinatario_cnpj_cpf', ''),
            destinatario_razao=xml_data.get('destinatario_razao', ''),
            destinatario_cidade=xml_data.get('destinatario_cidade', ''),
            destinatario_uf=xml_data.get('destinatario_uf', ''),
            destinatario_endereco=xml_data.get('destinatario_endereco', ''),
            destinatario_cep=xml_data.get('destinatario_cep', ''),
            danfe_generated=False,
            label_generated=False
        )
        
        db.session.add(xml_file)
        db.session.commit()
        
        logger.info(f"XML salvo com ID {xml_file.id} para usuário {user_id}")
        logger.info(f"Dados extraídos: NF {xml_data.get('numero_nf', 'N/A')}, Emitente: {xml_data.get('nome_emitente', 'N/A')}")
        
        return xml_file.id
        
    except Exception as e:
        logger.error(f"Erro ao salvar XML no banco: {e}")
        db.session.rollback()
        raise