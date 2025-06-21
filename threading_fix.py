"""
Correção definitiva para sistema de threading
Robô ultra-simplificado que processa XMLs sequencialmente sem travar
"""
import time
import logging
import threading
from datetime import datetime
import json
import os

logger = logging.getLogger(__name__)

def process_download_job_ultra_simple(job_id, user_id):
    """
    Processamento ultra-simplificado sem travamentos
    """
    try:
        from new_app import app, db, download_jobs, jobs_lock
        from models import DownloadJob as DBDownloadJob
        from simple_production_robot import SimpleProductionRobot
        
        with app.app_context():
            logger.info(f"🚀 [ULTRA-SIMPLE] Iniciando job {job_id}")
            
            # Buscar job no banco
            db_job = DBDownloadJob.query.filter_by(job_id=job_id, user_id=user_id).first()
            if not db_job:
                logger.error(f"Job {job_id} não encontrado")
                return
            
            # Obter chaves da nota
            invoice_keys = json.loads(db_job.invoice_keys or '[]')
            
            # Atualizar status para running
            db_job.status = "running"
            db_job.started_at = datetime.utcnow()
            db.session.commit()
            
            # Processar cada XML individualmente com múltiplas tentativas
            for i, invoice_key in enumerate(invoice_keys):
                try:
                    logger.info(f"🔄 [ULTRA-SIMPLE] Processando {i+1}/{len(invoice_keys)}: {invoice_key}")
                    
                    # Tentar download com robô simplificado
                    result = SimpleProductionRobot.simple_download(
                        invoice_key=invoice_key,
                        job_id=job_id,
                        user_id=user_id
                    )
                    
                    # Se falhar, tentar com robô principal
                    if not result.get('success'):
                        logger.warning(f"⚠️ [ULTRA-SIMPLE] Robô simples falhou, tentando robô principal...")
                        from automation_fixed import InvoiceDownloader
                        downloader = InvoiceDownloader()
                        try:
                            result = downloader.download_invoice_xml(
                                invoice_key=invoice_key,
                                job_id=job_id,
                                download_type='xml',
                                user_id=user_id
                            )
                        finally:
                            downloader.cleanup()
                    
                    # Atualizar progresso no banco
                    db_job.processed = i + 1
                    
                    if result.get('success'):
                        db_job.successful += 1
                        if result.get('file_path'):
                            db_job.add_downloaded_file(result['file_path'])
                        logger.info(f"✅ [ULTRA-SIMPLE] Sucesso: {invoice_key}")
                    else:
                        db_job.failed += 1
                        error_msg = result.get('error', 'Erro desconhecido')
                        db_job.add_error(invoice_key, error_msg)
                        logger.warning(f"❌ [ULTRA-SIMPLE] Falha: {invoice_key} - {error_msg}")
                    
                    # Salvar progresso imediatamente
                    db.session.commit()
                    
                    # Atualizar job em memória se existir
                    with jobs_lock:
                        if job_id in download_jobs:
                            memory_job = download_jobs[job_id]
                            memory_job.processed = db_job.processed
                            memory_job.successful = db_job.successful
                            memory_job.failed = db_job.failed
                            memory_job.status = "running"
                    
                    logger.info(f"📊 [ULTRA-SIMPLE] Progresso: {db_job.processed}/{len(invoice_keys)} - Sucessos: {db_job.successful} - Falhas: {db_job.failed}")
                    
                    # Pausa entre downloads
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"💥 [ULTRA-SIMPLE] Erro processando {invoice_key}: {str(e)}")
                    
                    db_job.processed += 1
                    db_job.failed += 1
                    db_job.add_error(invoice_key, str(e))
                    db.session.commit()
            
            # Finalizar job
            final_status = "completed" if db_job.successful > 0 else "failed"
            db_job.status = final_status
            db_job.completed_at = datetime.utcnow()
            db.session.commit()
            
            # Atualizar memória
            with jobs_lock:
                if job_id in download_jobs:
                    download_jobs[job_id].status = final_status
                    download_jobs[job_id].end_time = datetime.utcnow()
            
            logger.info(f"🎉 [ULTRA-SIMPLE] Job {job_id} concluído: {db_job.successful} sucessos, {db_job.failed} falhas")
            
    except Exception as e:
        logger.error(f"💥💥 [ULTRA-SIMPLE] Erro crítico no job {job_id}: {str(e)}")
        
        # Marcar job como falha
        try:
            with app.app_context():
                db_job = DBDownloadJob.query.filter_by(job_id=job_id).first()
                if db_job:
                    db_job.status = "failed"
                    db_job.completed_at = datetime.utcnow()
                    db.session.commit()
        except:
            pass

def start_ultra_simple_download(job_id, user_id):
    """
    Inicia download com threading ultra-simplificado
    """
    thread = threading.Thread(
        target=process_download_job_ultra_simple,
        args=(job_id, user_id),
        daemon=True
    )
    thread.start()
    logger.info(f"🚀 [ULTRA-SIMPLE] Thread iniciada para job {job_id}")
    return thread