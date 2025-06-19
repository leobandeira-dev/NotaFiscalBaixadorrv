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
    Extrai dados estruturados do XML NFe para geração de etiquetas
    """
    try:
        # Parse do XML
        root = ET.fromstring(xml_content)
        
        # Namespaces comuns da NFe
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        
        # Dados da nota fiscal
        nf_data = {}
        
        # Identificação da NFe
        ide = root.find('.//nfe:ide', ns)
        if ide is not None:
            nf_data['numero_nf'] = ide.find('nfe:nNF', ns).text if ide.find('nfe:nNF', ns) is not None else ''
            nf_data['serie_nf'] = ide.find('nfe:serie', ns).text if ide.find('nfe:serie', ns) is not None else ''
            
        # Emitente
        emit = root.find('.//nfe:emit', ns)
        if emit is not None:
            nf_data['cnpj_emitente'] = emit.find('nfe:CNPJ', ns).text if emit.find('nfe:CNPJ', ns) is not None else ''
            nf_data['nome_emitente'] = emit.find('nfe:xNome', ns).text if emit.find('nfe:xNome', ns) is not None else ''
            
            # Endereço do emitente
            enderEmit = emit.find('nfe:enderEmit', ns)
            if enderEmit is not None:
                nf_data['uf_emitente'] = enderEmit.find('nfe:UF', ns).text if enderEmit.find('nfe:UF', ns) is not None else ''
                nf_data['cidade_emitente'] = enderEmit.find('nfe:xMun', ns).text if enderEmit.find('nfe:xMun', ns) is not None else ''
        
        # Destinatário
        dest = root.find('.//nfe:dest', ns)
        if dest is not None:
            nf_data['cnpj_destinatario'] = dest.find('nfe:CNPJ', ns).text if dest.find('nfe:CNPJ', ns) is not None else ''
            nf_data['nome_destinatario'] = dest.find('nfe:xNome', ns).text if dest.find('nfe:xNome', ns) is not None else ''
            
            # Endereço do destinatário
            enderDest = dest.find('nfe:enderDest', ns)
            if enderDest is not None:
                nf_data['endereco_destinatario'] = enderDest.find('nfe:xLgr', ns).text if enderDest.find('nfe:xLgr', ns) is not None else ''
                nf_data['numero_destinatario'] = enderDest.find('nfe:nro', ns).text if enderDest.find('nfe:nro', ns) is not None else ''
                nf_data['bairro_destinatario'] = enderDest.find('nfe:xBairro', ns).text if enderDest.find('nfe:xBairro', ns) is not None else ''
                nf_data['cidade_destinatario'] = enderDest.find('nfe:xMun', ns).text if enderDest.find('nfe:xMun', ns) is not None else ''
                nf_data['uf_destinatario'] = enderDest.find('nfe:UF', ns).text if enderDest.find('nfe:UF', ns) is not None else ''
                nf_data['cep_destinatario'] = enderDest.find('nfe:CEP', ns).text if enderDest.find('nfe:CEP', ns) is not None else ''
        
        # Totais da NFe
        total = root.find('.//nfe:total/nfe:ICMSTot', ns)
        if total is not None:
            nf_data['valor_total'] = float(total.find('nfe:vNF', ns).text) if total.find('nfe:vNF', ns) is not None else 0.0
        
        # Informações de transporte
        transp = root.find('.//nfe:transp', ns)
        if transp is not None:
            # Transportadora
            transporta = transp.find('nfe:transporta', ns)
            if transporta is not None:
                nf_data['transportadora'] = transporta.find('nfe:xNome', ns).text if transporta.find('nfe:xNome', ns) is not None else ''
            
            # Volumes
            vol = transp.find('nfe:vol', ns)
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