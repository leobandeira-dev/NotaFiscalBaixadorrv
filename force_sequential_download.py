"""
Sistema de download sequencial forçado
Força o progresso XML por XML sem travamentos
"""
import time
import logging
import os
from datetime import datetime

logger = logging.getLogger(__name__)

def force_sequential_download(job_id, user_id, invoice_keys):
    """
    Force download sequencial sem threading complexo
    """
    try:
        from new_app import app, db
        from models import DownloadJob as DBDownloadJob
        from simple_production_robot import SimpleProductionRobot
        from automation_fixed import InvoiceDownloader
        
        with app.app_context():
            logger.info(f"🎯 [FORCE] Iniciando download forçado para job {job_id}")
            
            # Buscar job no banco
            db_job = DBDownloadJob.query.filter_by(job_id=job_id, user_id=user_id).first()
            if not db_job:
                logger.error(f"Job {job_id} não encontrado")
                return False
            
            # Forçar status running
            db_job.status = "running"
            db_job.started_at = datetime.utcnow()
            db.session.commit()
            
            successful_downloads = 0
            failed_downloads = 0
            
            # Processar cada XML com instância nova do robô
            for i, invoice_key in enumerate(invoice_keys):
                try:
                    logger.info(f"🔥 [FORCE] Processando XML {i+1}/{len(invoice_keys)}: {invoice_key}")
                    
                    # Tentar com robô simplificado primeiro
                    result = SimpleProductionRobot.simple_download(
                        invoice_key=invoice_key,
                        job_id=job_id,
                        user_id=user_id
                    )
                    
                    if not result.get('success'):
                        # Se falhar, tentar com robô principal
                        logger.warning(f"⚠️ [FORCE] Robô simples falhou, tentando robô principal...")
                        downloader = InvoiceDownloader()
                        result = downloader.download_invoice_xml(
                            invoice_key=invoice_key,
                            job_id=job_id,
                            download_type='xml',
                            user_id=user_id
                        )
                        downloader.cleanup()
                    
                    # Atualizar progresso imediatamente
                    db_job.processed = i + 1
                    
                    if result.get('success'):
                        successful_downloads += 1
                        db_job.successful = successful_downloads
                        
                        if result.get('file_path'):
                            db_job.add_downloaded_file(result['file_path'])
                        
                        logger.info(f"✅ [FORCE] Sucesso XML {i+1}: {invoice_key}")
                    else:
                        failed_downloads += 1
                        db_job.failed = failed_downloads
                        
                        error_msg = result.get('error', 'Erro desconhecido')
                        db_job.add_error(invoice_key, error_msg)
                        
                        logger.warning(f"❌ [FORCE] Falha XML {i+1}: {invoice_key} - {error_msg}")
                    
                    # Salvar progresso após cada XML
                    db.session.commit()
                    
                    logger.info(f"📊 [FORCE] Progresso: {db_job.processed}/{len(invoice_keys)} - Sucessos: {successful_downloads} - Falhas: {failed_downloads}")
                    
                    # Pausa pequena entre downloads
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"💥 [FORCE] Erro processando {invoice_key}: {str(e)}")
                    
                    failed_downloads += 1
                    db_job.processed = i + 1
                    db_job.failed = failed_downloads
                    db_job.add_error(invoice_key, str(e))
                    db.session.commit()
            
            # Finalizar job
            final_status = "completed" if successful_downloads > 0 else "failed"
            db_job.status = final_status
            db_job.completed_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"🎉 [FORCE] Job {job_id} finalizado: {successful_downloads} sucessos, {failed_downloads} falhas")
            return True
            
    except Exception as e:
        logger.error(f"💥💥 [FORCE] Erro crítico: {str(e)}")
        return False

def test_force_download():
    """Teste do sistema de download forçado"""
    test_keys = [
        "42250485179240000239550020004175331780623268",
        "42250485179240000239550020004175361171503396", 
        "35250513516247000107550010000113401146202508",
        "11111111111111111111111111111111111111111111",
        "22222222222222222222222222222222222222222222"
    ]
    
    job_id = "test-force-download"
    user_id = 2
    
    return force_sequential_download(job_id, user_id, test_keys)

if __name__ == "__main__":
    test_force_download()