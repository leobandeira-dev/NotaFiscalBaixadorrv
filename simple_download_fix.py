"""
Sistema de download simplificado que funciona imediatamente
Resolve o problema de threading e status que não finaliza
"""
import os
import json
import time
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def process_download_immediately(job_id, user_id, invoice_keys):
    """
    Processa download imediatamente - sem threading
    """
    try:
        from new_app import app, db
        from models import DownloadJob as DBDownloadJob
        
        # Log inicial
        logger.info(f"🚀 INICIANDO download direto: {job_id} - {len(invoice_keys)} chaves")
        
        with app.app_context():
            # Buscar/criar job
            db_job = DBDownloadJob.query.filter_by(job_id=job_id, user_id=user_id).first()
            if not db_job:
                db_job = DBDownloadJob()
                db_job.job_id = job_id
                db_job.user_id = user_id
                db_job.total_keys = len(invoice_keys)
                db_job.invoice_keys = json.dumps(invoice_keys)
                db_job.status = "running"  # Direto para running
                db_job.processed = 0
                db_job.successful = 0
                db_job.failed = 0
                db_job.downloaded_files = "[]"
                db_job.errors = "[]"
                db_job.started_at = datetime.utcnow()
                db.session.add(db_job)
                db.session.commit()
                logger.info(f"✅ Job criado no banco: {job_id}")
            
            # Status running
            db_job.status = "running"
            db_job.started_at = datetime.utcnow()
            db.session.commit()
            
            # Simular processamento rápido para teste
            for i, invoice_key in enumerate(invoice_keys):
                logger.info(f"🔥 Processando {i+1}/{len(invoice_keys)}: {invoice_key[:10]}...")
                
                # Usar robô real se disponível
                try:
                    from simple_production_robot import SimpleProductionRobot
                    result = SimpleProductionRobot.simple_download(
                        invoice_key=invoice_key,
                        job_id=job_id,
                        user_id=user_id
                    )
                    logger.info(f"📥 Resultado robô: {result}")
                except Exception as robot_error:
                    logger.warning(f"⚠️ Robô falhou: {robot_error}")
                    result = {'success': False, 'error': str(robot_error)}
                
                # Atualizar progresso
                db_job.processed = i + 1
                
                if result and result.get('success'):
                    db_job.successful += 1
                    # Adicionar arquivo se disponível
                    if result.get('file_path'):
                        files = json.loads(db_job.downloaded_files or '[]')
                        files.append(result['file_path'])
                        db_job.downloaded_files = json.dumps(files)
                    logger.info(f"✅ Sucesso {i+1}")
                else:
                    db_job.failed += 1
                    # Adicionar erro
                    errors = json.loads(db_job.errors or '[]')
                    errors.append({
                        'invoice_key': invoice_key,
                        'error': result.get('error', 'Falha no download') if result else 'Erro de processamento'
                    })
                    db_job.errors = json.dumps(errors)
                    logger.warning(f"❌ Falha {i+1}")
                
                # Salvar progresso a cada XML
                db.session.commit()
                logger.info(f"💾 Progresso salvo: {db_job.processed}/{len(invoice_keys)}")
                
                # Pausa pequena
                time.sleep(0.2)
            
            # Finalizar
            db_job.status = "completed" if db_job.successful > 0 else "failed"
            db_job.completed_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"🎉 JOB FINALIZADO: {job_id} - Sucessos: {db_job.successful}, Falhas: {db_job.failed}")
            
            return True
            
    except Exception as e:
        logger.error(f"💥 ERRO CRÍTICO no download: {str(e)}")
        
        # Tentar marcar como falha no banco
        try:
            with app.app_context():
                db_job = DBDownloadJob.query.filter_by(job_id=job_id, user_id=user_id).first()
                if db_job:
                    db_job.status = "failed"
                    db_job.completed_at = datetime.utcnow()
                    db.session.commit()
        except:
            pass
        
        return False

def start_simple_download(job_id, user_id, invoice_keys):
    """
    Inicia download de forma simplificada
    """
    from threading import Thread
    
    def run():
        try:
            logger.info(f"🎯 Thread iniciada para job {job_id}")
            result = process_download_immediately(job_id, user_id, invoice_keys)
            logger.info(f"🏁 Thread finalizada para job {job_id}: {result}")
        except Exception as e:
            logger.error(f"💥 Erro na thread do job {job_id}: {str(e)}")
    
    # Executar em thread separada
    thread = Thread(target=run)
    thread.daemon = True
    thread.start()
    logger.info(f"🚀 Thread iniciada para job {job_id}")
    
    return True

def get_simple_job_status(job_id, user_id):
    """
    Obter status do job do banco de dados de forma simples
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
            
            import json
            return {
                'job_id': db_job.job_id,
                'status': db_job.status,
                'total_keys': db_job.total_keys,
                'processed': db_job.processed,
                'successful': db_job.successful,
                'failed': db_job.failed,
                'progress_percentage': progress,
                'percentage': progress,  # alias para compatibilidade
                'files': json.loads(db_job.downloaded_files or '[]'),
                'downloaded_files': json.loads(db_job.downloaded_files or '[]'),
                'errors': json.loads(db_job.errors or '[]'),
                'start_time': db_job.started_at.isoformat() if db_job.started_at else None,
                'created_at': db_job.created_at.isoformat() if db_job.created_at else None,
                'completed_at': db_job.completed_at.isoformat() if db_job.completed_at else None
            }
            
    except Exception as e:
        logger.error(f"Erro ao obter status simples do job: {str(e)}")
        return {'error': str(e)}