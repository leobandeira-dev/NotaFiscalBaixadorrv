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
        
        # Identificação da NFe
        ide = root.find('.//nfe:ide', ns)
        if ide is not None:
            nf_data['numero_nf'] = ide.find('nfe:nNF', ns).text if ide.find('nfe:nNF', ns) is not None else ''
            nf_data['serie_nf'] = ide.find('nfe:serie', ns).text if ide.find('nfe:serie', ns) is not None else ''
            
            # Data de emissão
            dhEmi = ide.find('nfe:dhEmi', ns)
            if dhEmi is not None and dhEmi.text:
                try:
                    # Formato: 2025-06-19T12:00:00-03:00
                    date_str = dhEmi.text.split('T')[0]  # Pega apenas a data
                    nf_data['data_emissao'] = datetime.strptime(date_str, '%Y-%m-%d').date()
                except:
                    nf_data['data_emissao'] = None
            else:
                nf_data['data_emissao'] = None
            
        # Emitente (Remetente)
        emit = root.find('.//nfe:emit', ns)
        if emit is not None:
            nf_data['cnpj_emitente'] = emit.find('nfe:CNPJ', ns).text if emit.find('nfe:CNPJ', ns) is not None else ''
            nf_data['nome_emitente'] = emit.find('nfe:xNome', ns).text if emit.find('nfe:xNome', ns) is not None else ''
            nf_data['remetente_razao'] = emit.find('nfe:xNome', ns).text if emit.find('nfe:xNome', ns) is not None else ''
            
            # Endereço do emitente/remetente
            enderEmit = emit.find('nfe:enderEmit', ns)
            if enderEmit is not None:
                nf_data['remetente_uf'] = enderEmit.find('nfe:UF', ns).text if enderEmit.find('nfe:UF', ns) is not None else ''
                nf_data['remetente_cidade'] = enderEmit.find('nfe:xMun', ns).text if enderEmit.find('nfe:xMun', ns) is not None else ''
                
                # Endereço completo
                logradouro = enderEmit.find('nfe:xLgr', ns).text if enderEmit.find('nfe:xLgr', ns) is not None else ''
                numero = enderEmit.find('nfe:nro', ns).text if enderEmit.find('nfe:nro', ns) is not None else ''
                bairro = enderEmit.find('nfe:xBairro', ns).text if enderEmit.find('nfe:xBairro', ns) is not None else ''
                
                endereco_parts = [logradouro, numero, bairro]
                nf_data['remetente_endereco'] = ', '.join([p for p in endereco_parts if p])
                
                cep = enderEmit.find('nfe:CEP', ns)
                nf_data['remetente_cep'] = cep.text if cep is not None and cep.text else ''
        
        # Destinatário
        dest = root.find('.//nfe:dest', ns)
        if dest is not None:
            # CNPJ ou CPF
            cnpj = dest.find('nfe:CNPJ', ns)
            cpf = dest.find('nfe:CPF', ns)
            nf_data['destinatario_cnpj_cpf'] = cnpj.text if cnpj is not None and cnpj.text else (cpf.text if cpf is not None and cpf.text else '')
            
            nf_data['destinatario_razao'] = dest.find('nfe:xNome', ns).text if dest.find('nfe:xNome', ns) is not None else ''
            
            # Endereço do destinatário
            enderDest = dest.find('nfe:enderDest', ns)
            if enderDest is not None:
                nf_data['destinatario_uf'] = enderDest.find('nfe:UF', ns).text if enderDest.find('nfe:UF', ns) is not None else ''
                nf_data['destinatario_cidade'] = enderDest.find('nfe:xMun', ns).text if enderDest.find('nfe:xMun', ns) is not None else ''
                
                # Endereço completo do destinatário
                logradouro = enderDest.find('nfe:xLgr', ns).text if enderDest.find('nfe:xLgr', ns) is not None else ''
                numero = enderDest.find('nfe:nro', ns).text if enderDest.find('nfe:nro', ns) is not None else ''
                bairro = enderDest.find('nfe:xBairro', ns).text if enderDest.find('nfe:xBairro', ns) is not None else ''
                
                endereco_parts = [logradouro, numero, bairro]
                nf_data['destinatario_endereco'] = ', '.join([p for p in endereco_parts if p])
                
                cep = enderDest.find('nfe:CEP', ns)
                nf_data['destinatario_cep'] = cep.text if cep is not None and cep.text else ''
        
        # Totais da NFe
        total = root.find('.//nfe:total/nfe:ICMSTot', ns)
        if total is not None:
            vNF = total.find('nfe:vNF', ns)
            nf_data['valor_total'] = float(vNF.text) if vNF is not None and vNF.text else 0.0
        else:
            nf_data['valor_total'] = 0.0
        
        # Informações de transporte
        transp = root.find('.//nfe:transp', ns)
        if transp is not None:
            # Volumes
            vol = transp.find('nfe:vol', ns)
            if vol is not None:
                # Peso bruto
                pesoB = vol.find('nfe:pesoB', ns)
                nf_data['peso_bruto'] = float(pesoB.text) if pesoB is not None and pesoB.text else 0.0
                
                # Quantidade de volumes
                qVol = vol.find('nfe:qVol', ns)
                nf_data['quantidade_volumes'] = int(qVol.text) if qVol is not None and qVol.text else 0
            else:
                nf_data['peso_bruto'] = 0.0
                nf_data['quantidade_volumes'] = 0
        else:
            nf_data['peso_bruto'] = 0.0
            nf_data['quantidade_volumes'] = 0
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