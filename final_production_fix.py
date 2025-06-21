"""
Solução definitiva para threading em produção
Sistema sem threading que processa XMLs diretamente
"""
import os
import time
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def is_production():
    """Detecta se está em ambiente de produção"""
    return (os.environ.get('REPLIT_DEPLOYMENT') is not None or 
            'replit.dev' in os.environ.get('REPLIT_DEV_DOMAIN', ''))

def direct_download_without_threading(job_id, user_id, invoice_keys):
    """
    Download direto sem threading para ambiente de produção
    """
    try:
        from new_app import app, db
        from models import DownloadJob as DBDownloadJob
        from simple_production_robot import SimpleProductionRobot
        
        with app.app_context():
            logger.info(f"🎯 [DIRECT] Download direto job {job_id} - {len(invoice_keys)} chaves")
            
            # Buscar job no banco
            db_job = DBDownloadJob.query.filter_by(job_id=job_id, user_id=user_id).first()
            if not db_job:
                logger.error(f"Job {job_id} não encontrado")
                return False
            
            # Status running
            db_job.status = "running"
            db_job.started_at = datetime.utcnow()
            db.session.commit()
            
            success_count = 0
            failed_count = 0
            
            # Processar cada XML diretamente sem threading
            for i, invoice_key in enumerate(invoice_keys):
                try:
                    logger.info(f"🔥 [DIRECT] XML {i+1}/{len(invoice_keys)}: {invoice_key}")
                    
                    # Download direto com robô simplificado
                    result = SimpleProductionRobot.simple_download(
                        invoice_key=invoice_key,
                        job_id=job_id,
                        user_id=user_id
                    )
                    
                    # Atualizar progresso
                    db_job.processed = i + 1
                    
                    if result.get('success'):
                        success_count += 1
                        db_job.successful = success_count
                        
                        if result.get('file_path'):
                            # Adicionar arquivo baixado
                            current_files = json.loads(db_job.downloaded_files or '[]')
                            current_files.append(result['file_path'])
                            db_job.downloaded_files = json.dumps(current_files)
                        
                        logger.info(f"✅ [DIRECT] Sucesso: {invoice_key}")
                    else:
                        failed_count += 1
                        db_job.failed = failed_count
                        
                        # Adicionar erro
                        current_errors = json.loads(db_job.errors or '[]')
                        current_errors.append({
                            'invoice_key': invoice_key,
                            'error': result.get('error', 'Erro desconhecido')
                        })
                        db_job.errors = json.dumps(current_errors)
                        
                        logger.warning(f"❌ [DIRECT] Falha: {invoice_key}")
                    
                    # Salvar progresso imediatamente
                    db.session.commit()
                    
                    logger.info(f"📊 [DIRECT] Progresso: {db_job.processed}/{len(invoice_keys)} - Sucessos: {success_count} - Falhas: {failed_count}")
                    
                    # Pausa pequena
                    time.sleep(1)
                    
                except Exception as e:
                    logger.error(f"💥 [DIRECT] Erro XML {invoice_key}: {str(e)}")
                    
                    # Atualizar com erro
                    failed_count += 1
                    db_job.processed = i + 1
                    db_job.failed = failed_count
                    
                    current_errors = json.loads(db_job.errors or '[]')
                    current_errors.append({
                        'invoice_key': invoice_key,
                        'error': str(e)
                    })
                    db_job.errors = json.dumps(current_errors)
                    
                    db.session.commit()
            
            # Finalizar job
            final_status = "completed" if success_count > 0 else "failed"
            db_job.status = final_status
            db_job.completed_at = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"🎉 [DIRECT] Job {job_id} finalizado: {success_count} sucessos, {failed_count} falhas")
            return True
            
    except Exception as e:
        logger.error(f"💥💥 [DIRECT] Erro crítico: {str(e)}")
        return False

def replace_threading_system():
    """
    Substitui o sistema de threading por processamento direto
    """
    # Aplicar patch no new_app.py para usar processamento direto
    with open('new_app.py', 'r') as f:
        content = f.read()
    
    # Substituir a chamada de threading
    old_code = """        # Use ultra-simple threading system to prevent hang-ups
        from threading_fix import start_ultra_simple_download
        start_ultra_simple_download(job_id, current_user.id)"""
    
    new_code = """        # Use direct processing in production to prevent threading issues
        if is_production():
            from final_production_fix import direct_download_without_threading
            direct_download_without_threading(job_id, current_user.id, valid_keys)
        else:
            from threading_fix import start_ultra_simple_download
            start_ultra_simple_download(job_id, current_user.id)"""
    
    if old_code in content:
        content = content.replace(old_code, new_code)
        
        # Adicionar import no topo
        if 'from final_production_fix import is_production' not in content:
            import_line = "from final_production_fix import is_production\n"
            content = import_line + content
        
        with open('new_app.py', 'w') as f:
            f.write(content)
        
        print("✅ Sistema de threading substituído por processamento direto")
        return True
    
    return False

if __name__ == "__main__":
    replace_threading_system()