"""
Download Service - Centralized XML processing and database integration
Handles XML processing, database saving, and user charging for both development and production environments
"""

import os
import logging
from datetime import datetime
from flask import current_app

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_xml_download(user_id: int, invoice_key: str, xml_content: str, job_id: str):
    """
    Centralized XML processing function that handles:
    - XML parsing and data extraction
    - Database storage
    - User charging
    - Error handling
    """
    try:
        # Import models within function to avoid circular imports
        from models import XMLFile, User, UsageRecord, db
        from xml_processor import XMLProcessor
        
        logger.info(f"[Job {job_id}] Processing XML for user {user_id}, key: {invoice_key}")
        
        # Check if XML already exists for this user
        existing_xml = XMLFile.query.filter_by(
            user_id=user_id,
            chave_nfe=invoice_key
        ).first()
        
        if existing_xml:
            logger.info(f"[Job {job_id}] XML already exists for user {user_id}: {invoice_key}")
            return {
                "success": True,
                "message": "XML already exists",
                "xml_id": existing_xml.id
            }
        
        # Process XML content
        processor = XMLProcessor()
        xml_data = processor.process_xml_content(xml_content)
        
        if not xml_data:
            logger.error(f"[Job {job_id}] Failed to process XML content: {invoice_key}")
            return {
                "success": False,
                "message": "Failed to process XML content"
            }
        
        # Create XMLFile record
        xml_file = XMLFile(
            user_id=user_id,
            filename=f"{invoice_key}.xml",
            chave_nfe=invoice_key,
            import_type='SISTEMA',
            file_size=len(xml_content),
            
            # NFe identification data
            numero_nf=xml_data.get('numero_nf', 'N/A'),
            serie_nf=xml_data.get('serie_nf', 'N/A'),
            data_emissao=xml_data.get('data_emissao'),
            valor_total=xml_data.get('valor_total', 0.0),
            peso_bruto=xml_data.get('peso_bruto', 0.0),
            quantidade_volumes=xml_data.get('quantidade_volumes', 1),
            
            # Emitente data
            nome_emitente=xml_data.get('nome_emitente', 'N/A'),
            cnpj_emitente=xml_data.get('cnpj_emitente', 'N/A'),
            cidade_emitente=xml_data.get('cidade_emitente', 'N/A'),
            uf_emitente=xml_data.get('uf_emitente', 'N/A'),
            endereco_emitente=xml_data.get('endereco_emitente', 'N/A'),
            cep_emitente=xml_data.get('cep_emitente', 'N/A'),
            
            # Destinatário data
            nome_destinatario=xml_data.get('nome_destinatario', 'N/A'),
            cnpj_destinatario=xml_data.get('cnpj_destinatario', 'N/A'),
            cidade_destinatario=xml_data.get('cidade_destinatario', 'N/A'),
            uf_destinatario=xml_data.get('uf_destinatario', 'N/A'),
            endereco_destinatario=xml_data.get('endereco_destinatario', 'N/A'),
            cep_destinatario=xml_data.get('cep_destinatario', 'N/A'),
            
            # Remetente data (fallback to emitente if not present)
            nome_remetente=xml_data.get('nome_remetente') or xml_data.get('nome_emitente', 'N/A'),
            cidade_remetente=xml_data.get('cidade_remetente') or xml_data.get('cidade_emitente', 'N/A'),
            uf_remetente=xml_data.get('uf_remetente') or xml_data.get('uf_emitente', 'N/A'),
            endereco_remetente=xml_data.get('endereco_remetente') or xml_data.get('endereco_emitente', 'N/A'),
            
            # Transportadora data
            nome_transportadora=xml_data.get('nome_transportadora', 'N/A'),
            
            created_at=datetime.utcnow()
        )
        
        # Save to database
        db.session.add(xml_file)
        db.session.flush()  # Get the ID without committing
        
        # Charge user for download
        _charge_user_for_download(user_id, invoice_key, job_id)
        
        # Commit transaction
        db.session.commit()
        
        logger.info(f"[Job {job_id}] XML successfully processed and saved: {invoice_key}")
        return {
            "success": True,
            "message": "XML processed successfully",
            "xml_id": xml_file.id
        }
        
    except Exception as e:
        logger.error(f"[Job {job_id}] Error processing XML download: {e}")
        if 'db' in locals():
            db.session.rollback()
        return {
            "success": False,
            "message": f"Processing error: {str(e)}"
        }

def _charge_user_for_download(user_id: int, invoice_key: str, job_id: str):
    """Charge user for XML download if not in trial period"""
    try:
        from models import User, UsageRecord, db
        from pricing import get_xml_download_cost
        
        user = User.query.get(user_id)
        if not user:
            logger.error(f"[Job {job_id}] User not found: {user_id}")
            return
        
        # Check if user is in trial period
        if user.trial_active and user.trial_expires_at and user.trial_expires_at > datetime.utcnow():
            logger.info(f"[Job {job_id}] User {user_id} in trial period - no charge for XML: {invoice_key}")
            
            # Still record usage for trial tracking
            usage_record = UsageRecord(
                user_id=user_id,
                module_name='xml_download',
                description=f'XML Download (Trial): {invoice_key}',
                cost=0.0,
                credits_before=user.balance,
                credits_after=user.balance,
                created_at=datetime.utcnow()
            )
            db.session.add(usage_record)
            return
        
        # Get cost based on user's current volume
        cost = get_xml_download_cost(user_id)
        
        if user.balance < cost:
            logger.warning(f"[Job {job_id}] Insufficient balance for user {user_id}: {user.balance} < {cost}")
            # Don't fail the download, just log the usage
            usage_record = UsageRecord(
                user_id=user_id,
                module_name='xml_download',
                description=f'XML Download (Insufficient Balance): {invoice_key}',
                cost=cost,
                credits_before=user.balance,
                credits_after=user.balance,
                created_at=datetime.utcnow()
            )
            db.session.add(usage_record)
            return
        
        # Charge user
        user.balance -= cost
        
        # Record usage
        usage_record = UsageRecord(
            user_id=user_id,
            module_name='xml_download',
            description=f'XML Download: {invoice_key}',
            cost=cost,
            credits_before=user.balance + cost,
            credits_after=user.balance,
            created_at=datetime.utcnow()
        )
        db.session.add(usage_record)
        
        logger.info(f"[Job {job_id}] Charged user {user_id} R${cost:.2f} for XML: {invoice_key}")
        
    except Exception as e:
        logger.error(f"[Job {job_id}] Error charging user for download: {e}")
        # Don't fail the download process for charging errors