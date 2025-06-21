"""
Sistema de job completamente funcional sem threading
Corrige problemas de sincronização e timeout
"""
import os
import json
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def process_job_synchronously(job_id, user_id, invoice_keys):
    """
    Processa job de forma síncrona - sem threading
    """
    try:
        from new_app import app, db
        from models import DownloadJob as DBDownloadJob
        from simple_production_robot import SimpleProductionRobot
        
        with app.app_context():
            logger.info(f"🎯 Job síncrono {job_id} - {len(invoice_keys)} chaves")
            
            # Criar/buscar job no banco
            db_job = DBDownloadJob.query.filter_by(job_id=job_id, user_id=user_id).first()
            if not db_job:
                db_job = DBDownloadJob()
                db_job.job_id = job_id
                db_job.user_id = user_id
                db_job.total_keys = len(invoice_keys)
                db_job.invoice_keys = json.dumps(invoice_keys)
                db_job.status = "starting"
                db_job.processed = 0
                db_job.successful = 0
                db_job.failed = 0
                db_job.downloaded_files = "[]"
                db_job.errors = "[]"
                db.session.add(db_job)
                db.session.commit()
            
            # Iniciar processamento
            db_job.status = "running"
            db_job.started_at = datetime.utcnow()
            db.session.commit()
            
            # Processar XMLs um por vez
            for i, invoice_key in enumerate(invoice_keys):
                try:
                    logger.info(f"📥 Processando {i+1}/{len(invoice_keys)}: {invoice_key[:10]}...")
                    
                    # Download individual
                    result = SimpleProductionRobot.simple_download(
                        invoice_key=invoice_key,
                        job_id=job_id,
                        user_id=user_id
                    )
                    
                    # Atualizar progresso
                    db_job.processed = i + 1
                    
                    if result and result.get('success'):
                        db_job.successful += 1
                        
                        # Adicionar arquivo
                        files = json.loads(db_job.downloaded_files or '[]')
                        if result.get('file_path'):
                            files.append(result['file_path'])
                        db_job.downloaded_files = json.dumps(files)
                        
                        logger.info(f"✅ Sucesso {i+1}: {invoice_key[:10]}...")
                    else:
                        db_job.failed += 1
                        
                        # Adicionar erro
                        errors = json.loads(db_job.errors or '[]')
                        errors.append({
                            'invoice_key': invoice_key,
                            'error': result.get('error', 'Falha no download') if result else 'Erro de processamento'
                        })
                        db_job.errors = json.dumps(errors)
                        
                        logger.warning(f"❌ Falha {i+1}: {invoice_key[:10]}...")
                    
                    # Salvar progresso imediatamente
                    db.session.commit()
                    
                    # Log de progresso
                    progress = round((db_job.processed / len(invoice_keys)) * 100, 1)
                    logger.info(f"📊 Progresso: {progress}% ({db_job.processed}/{len(invoice_keys)}) - Sucessos: {db_job.successful}")
                    
                    # Pausa pequena para evitar sobrecarga
                    time.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"💥 Erro em {invoice_key}: {str(e)}")
                    
                    # Contar como falha
                    db_job.processed = i + 1
                    db_job.failed += 1
                    
                    errors = json.loads(db_job.errors or '[]')
                    errors.append({
                        'invoice_key': invoice_key,
                        'error': f"Exceção: {str(e)}"
                    })
                    db_job.errors = json.dumps(errors)
                    
                    db.session.commit()
            
            # Finalizar job
            db_job.status = "completed" if db_job.successful > 0 else "failed"
            db_job.completed_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"🎉 Job {job_id} finalizado: {db_job.successful} sucessos, {db_job.failed} falhas")
            
            return {
                'success': True,
                'job_id': job_id,
                'processed': db_job.processed,
                'successful': db_job.successful,
                'failed': db_job.failed,
                'status': db_job.status
            }
            
    except Exception as e:
        logger.error(f"💥💥 Erro crítico no job {job_id}: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }

def get_job_status_from_db(job_id, user_id):
    """
    Obter status do job diretamente do banco
    """
    try:
        from new_app import app, db
        from models import DownloadJob as DBDownloadJob
        
        with app.app_context():
            db_job = DBDownloadJob.query.filter_by(job_id=job_id, user_id=user_id).first()
            
            if not db_job:
                return {'error': 'Job não encontrado'}
            
            progress = 0
            if db_job.total_keys > 0:
                progress = round((db_job.processed / db_job.total_keys) * 100, 1)
            
            return {
                'job_id': db_job.job_id,
                'status': db_job.status,
                'processed': db_job.processed,
                'successful': db_job.successful,
                'failed': db_job.failed,
                'total_keys': db_job.total_keys,
                'progress_percentage': progress,
                'files': json.loads(db_job.downloaded_files or '[]'),
                'errors': json.loads(db_job.errors or '[]'),
                'started_at': db_job.started_at.isoformat() if db_job.started_at else None,
                'completed_at': db_job.completed_at.isoformat() if db_job.completed_at else None
            }
            
    except Exception as e:
        logger.error(f"Erro ao obter status do job: {str(e)}")
        return {'error': str(e)}