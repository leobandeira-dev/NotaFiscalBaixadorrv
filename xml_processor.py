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
        
        # Encontrar o elemento infNFe dentro de NFe
        infNFe = root.find('.//nfe:NFe/nfe:infNFe', ns)
        if infNFe is None:
            infNFe = root.find('.//nfe:infNFe', ns)
        
        if infNFe is not None:
            # Identificação da NFe
            ide = infNFe.find('nfe:ide', ns)
            if ide is not None:
                # Número da nota fiscal
                nNF = ide.find('nfe:nNF', ns)
                nf_data['numero_nf'] = nNF.text if nNF is not None else ''
                
                # Série da nota fiscal
                serie = ide.find('nfe:serie', ns)
                nf_data['serie_nf'] = serie.text if serie is not None else ''
                
                # Data de emissão
                dhEmi = ide.find('nfe:dhEmi', ns)
                if dhEmi is not None and dhEmi.text:
                    try:
                        # Formato: 2025-04-17T17:30:00-03:00
                        date_str = dhEmi.text.split('T')[0]  # Pega apenas a data
                        nf_data['data_emissao'] = datetime.strptime(date_str, '%Y-%m-%d').date()
                    except Exception as date_error:
                        logger.warning(f"Error parsing date: {date_error}")
                        nf_data['data_emissao'] = None
                else:
                    nf_data['data_emissao'] = None
            
            # Emitente (Remetente)
            emit = infNFe.find('nfe:emit', ns)
            if emit is not None:
                # CNPJ do emitente
                cnpj = emit.find('nfe:CNPJ', ns)
                nf_data['cnpj_emitente'] = cnpj.text if cnpj is not None else ''
                
                # Nome do emitente
                xNome = emit.find('nfe:xNome', ns)
                nome_emitente = xNome.text if xNome is not None else ''
                nf_data['nome_emitente'] = nome_emitente
                nf_data['remetente_razao'] = nome_emitente
                
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
                    
                    endereco_parts = [p for p in [logradouro, numero, bairro] if p]
                    nf_data['destinatario_endereco'] = ', '.join(endereco_parts)
                    
                    # CEP
                    cep = enderDest.find('nfe:CEP', ns)
                    nf_data['destinatario_cep'] = cep.text if cep is not None else ''
            
            # Totais da NFe
            total = infNFe.find('nfe:total/nfe:ICMSTot', ns)
            if total is not None:
                vNF = total.find('nfe:vNF', ns)
                if vNF is not None and vNF.text:
                    try:
                        nf_data['valor_total'] = float(vNF.text)
                    except:
                        nf_data['valor_total'] = 0.0
                else:
                    nf_data['valor_total'] = 0.0
            else:
                nf_data['valor_total'] = 0.0
            
            # Informações de transporte
            transp = infNFe.find('nfe:transp', ns)
            if transp is not None:
                # Volumes
                vol = transp.find('nfe:vol', ns)
                if vol is not None:
                    # Peso bruto
                    pesoB = vol.find('nfe:pesoB', ns)
                    if pesoB is not None and pesoB.text:
                        try:
                            nf_data['peso_bruto'] = float(pesoB.text)
                        except:
                            nf_data['peso_bruto'] = 0.0
                    else:
                        nf_data['peso_bruto'] = 0.0
                    
                    # Quantidade de volumes
                    qVol = vol.find('nfe:qVol', ns)
                    if qVol is not None and qVol.text:
                        try:
                            nf_data['quantidade_volumes'] = int(float(qVol.text))
                        except:
                            nf_data['quantidade_volumes'] = 0
                    else:
                        nf_data['quantidade_volumes'] = 0
                else:
                    nf_data['peso_bruto'] = 0.0
                    nf_data['quantidade_volumes'] = 0
            else:
                nf_data['peso_bruto'] = 0.0
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
            if vol is not None:
                nf_data['quantidade_volumes'] = vol.find('nfe:qVol', ns).text if vol.find('nfe:qVol', ns) is not None else ''
                nf_data['peso_bruto'] = vol.find('nfe:pesoB', ns).text if vol.find('nfe:pesoB', ns) is not None else ''
                nf_data['peso_liquido'] = vol.find('nfe:pesoL', ns).text if vol.find('nfe:pesoL', ns) is not None else ''
        
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
        # Verificar se XML já existe
        existing_xml = XMLFile.query.filter_by(
            user_id=user_id,
            invoice_key=invoice_key
        ).first()
        
        if existing_xml:
            logger.info(f"XML já existe no banco para chave {invoice_key}")
            return existing_xml.id
        
        # Extrair dados do XML
        xml_data = extract_xml_data(xml_content)
        
        # Criar novo registro XML
        xml_file = XMLFile(
            user_id=user_id,
            filename=f"{invoice_key}.xml",
            invoice_key=invoice_key,
            file_path=file_path,
            xml_content=xml_content,
            import_type=import_type,
            imported_at=datetime.utcnow(),
            job_id=job_id
        )
        
        db.session.add(xml_file)
        db.session.commit()
        
        logger.info(f"XML salvo no banco com ID {xml_file.id} para usuário {user_id}")
        logger.info(f"Dados extraídos: NF {xml_data.get('numero_nf', 'N/A')}, Emitente: {xml_data.get('nome_emitente', 'N/A')}")
        
        return xml_file.id
        
    except Exception as e:
        logger.error(f"Erro ao salvar XML no banco: {e}")
        db.session.rollback()
        raise