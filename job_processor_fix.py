"""
Solução definitiva para o problema de jobs que ficam em "running"
Implementa processamento direto sem dependência de threads externas
"""

import logging
import json
import time
from datetime import datetime
from models import DownloadJob as DBDownloadJob, db

logger = logging.getLogger(__name__)

def process_job_immediately(job_id, user_id):
    """
    Processa o job imediatamente no mesmo contexto da requisição
    Elimina problemas de threading e isolamento de sessão
    """
    try:
        logger.info(f"[IMMEDIATE PROCESSOR] Starting job {job_id} for user {user_id}")
        
        # Buscar job no banco
        db_job = DBDownloadJob.query.filter_by(job_id=job_id, user_id=user_id).first()
        if not db_job:
            logger.error(f"[IMMEDIATE PROCESSOR] Job {job_id} not found")
            return False
        
        # Atualizar status para running
        db_job.status = 'running'
        db_job.started_at = datetime.utcnow()
        db.session.commit()
        
        # Processar as chaves
        invoice_keys = json.loads(db_job.invoice_keys or '[]')
        logger.info(f"[IMMEDIATE PROCESSOR] Processing {len(invoice_keys)} keys")
        
        # Simular processamento para teste
        for i, key in enumerate(invoice_keys):
            logger.info(f"[IMMEDIATE PROCESSOR] Processing key {i+1}/{len(invoice_keys)}: {key}")
            
            # Atualizar progresso
            db_job.processed = i + 1
            
            # Simular download (substitua pela lógica real)
            try:
                # Aqui seria chamada a automação real
                time.sleep(2)  # Simular tempo de processamento
                
                db_job.successful += 1
                
                # Salvar arquivo fictício para teste
                downloaded_files = json.loads(db_job.downloaded_files or '[]')
                downloaded_files.append({
                    'filename': f'{key}.xml',
                    'size': 4750,
                    'downloaded_at': datetime.utcnow().isoformat()
                })
                db_job.downloaded_files = json.dumps(downloaded_files)
                
            except Exception as e:
                logger.error(f"[IMMEDIATE PROCESSOR] Error processing key {key}: {e}")
                db_job.failed += 1
                
                errors = json.loads(db_job.errors or '[]')
                errors.append({
                    'key': key,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                })
                db_job.errors = json.dumps(errors)
            
            # Salvar progresso no banco
            db.session.commit()
            logger.info(f"[IMMEDIATE PROCESSOR] Progress: {db_job.processed}/{db_job.total_keys}")
        
        # Marcar como completado
        db_job.status = 'completed'
        db_job.completed_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"[IMMEDIATE PROCESSOR] Job {job_id} completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"[IMMEDIATE PROCESSOR] Fatal error in job {job_id}: {e}")
        
        # Marcar job como falhou
        try:
            if db_job:
                db_job.status = 'failed'
                db_job.completed_at = datetime.utcnow()
                
                errors = json.loads(db_job.errors or '[]')
                errors.append({
                    'error': f'Fatal error: {str(e)}',
                    'timestamp': datetime.utcnow().isoformat()
                })
                db_job.errors = json.dumps(errors)
                
                db.session.commit()
        except Exception as commit_error:
            logger.error(f"[IMMEDIATE PROCESSOR] Error updating failed job: {commit_error}")
        
        return False

def process_job_with_real_automation(job_id, user_id):
    """
    Versão que usa a automação real do sistema
    """
    try:
        from automation_fixed import InvoiceDownloader
        
        logger.info(f"[REAL AUTOMATION] Starting job {job_id} for user {user_id}")
        
        # Buscar job no banco
        db_job = DBDownloadJob.query.filter_by(job_id=job_id, user_id=user_id).first()
        if not db_job:
            logger.error(f"[REAL AUTOMATION] Job {job_id} not found")
            return False
        
        # Atualizar status
        db_job.status = 'running'
        db_job.started_at = datetime.utcnow()
        db.session.commit()
        
        # Processar com automação real
        invoice_keys = json.loads(db_job.invoice_keys or '[]')
        downloader = InvoiceDownloader()
        
        results = downloader.download_xmls(invoice_keys, user_id)
        
        # Atualizar resultados no banco
        db_job.processed = len(invoice_keys)
        db_job.successful = len([r for r in results if r.get('success')])
        db_job.failed = len([r for r in results if not r.get('success')])
        
        # Salvar arquivos e erros
        downloaded_files = [r for r in results if r.get('success')]
        errors = [r for r in results if not r.get('success')]
        
        db_job.downloaded_files = json.dumps(downloaded_files)
        db_job.errors = json.dumps(errors)
        db_job.status = 'completed'
        db_job.completed_at = datetime.utcnow()
        db.session.commit()
        
        logger.info(f"[REAL AUTOMATION] Job {job_id} completed: {db_job.successful} success, {db_job.failed} failed")
        return True
        
    except Exception as e:
        logger.error(f"[REAL AUTOMATION] Error in job {job_id}: {e}")
        return False