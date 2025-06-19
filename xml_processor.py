"""
XML Processor for database operations
Handles XML storage and processing for the system
"""
import logging
from datetime import datetime
from models import db, XMLFile

logger = logging.getLogger(__name__)

def save_xml_to_database(user_id: int, invoice_key: str, xml_content: str, 
                        file_path: str, import_type: str = 'SISTEMA', job_id: str = None) -> int:
    """
    Save XML data to database
    
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
        return xml_file.id
        
    except Exception as e:
        logger.error(f"Erro ao salvar XML no banco: {e}")
        db.session.rollback()
        raise