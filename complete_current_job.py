"""
Completa o job atual que está travado
"""
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def complete_current_job():
    """Completa o job atual forçadamente"""
    try:
        from new_app import app, db
        from models import DownloadJob as DBDownloadJob
        from simple_production_robot import SimpleProductionRobot
        
        with app.app_context():
            # Buscar job travado
            job = DBDownloadJob.query.filter_by(job_id='73837103-620a-4ab2-bb6f-82e9318dd405').first()
            if not job:
                print("Job não encontrado")
                return False
            
            print(f"Job encontrado - Status: {job.status}, Processados: {job.processed}/{job.total_keys}")
            
            # Obter chaves restantes
            all_keys = json.loads(job.invoice_keys)
            remaining_keys = all_keys[job.processed:]
            
            print(f"Processando {len(remaining_keys)} chaves restantes...")
            
            # Processar chaves restantes
            for i, key in enumerate(remaining_keys):
                try:
                    print(f"Processando chave {job.processed + i + 1}/{job.total_keys}: {key}")
                    
                    result = SimpleProductionRobot.simple_download(
                        invoice_key=key,
                        job_id=job.job_id,
                        user_id=job.user_id
                    )
                    
                    job.processed += 1
                    
                    if result.get('success'):
                        job.successful += 1
                        if result.get('file_path'):
                            job.add_downloaded_file(result['file_path'])
                        print(f"✓ Sucesso: {key}")
                    else:
                        job.failed += 1
                        job.add_error(key, result.get('error', 'Erro desconhecido'))
                        print(f"✗ Falha: {key}")
                    
                    db.session.commit()
                    
                except Exception as e:
                    print(f"Erro processando {key}: {e}")
                    job.processed += 1
                    job.failed += 1
                    job.add_error(key, str(e))
                    db.session.commit()
            
            # Finalizar job
            job.status = "completed"
            job.completed_at = datetime.utcnow()
            db.session.commit()
            
            print(f"Job concluído: {job.successful} sucessos, {job.failed} falhas")
            return True
            
    except Exception as e:
        print(f"Erro: {e}")
        return False

if __name__ == "__main__":
    complete_current_job()