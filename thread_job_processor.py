"""
Sistema robusto de processamento de jobs em thread
Corrige problemas de execução de threads com logging detalhado
"""

import threading
import time
import logging
import traceback
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ThreadJobProcessor:
    """Processador robusto de jobs em thread com monitoramento"""
    
    def __init__(self, app):
        self.app = app
        self.active_threads = {}
        self.thread_lock = threading.Lock()
    
    def start_job_thread(self, job_id, user_id, target_function):
        """Inicia thread de processamento com monitoramento robusto"""
        
        def thread_wrapper():
            """Wrapper que garante execução da função target"""
            thread_id = threading.current_thread().ident
            logger.info(f"[THREAD {thread_id}] Iniciando processamento do job {job_id}")
            
            try:
                with self.app.app_context():
                    logger.info(f"[THREAD {thread_id}] Contexto Flask configurado")
                    
                    # Chamar função target
                    logger.info(f"[THREAD {thread_id}] Chamando função target...")
                    result = target_function(job_id, user_id)
                    
                    logger.info(f"[THREAD {thread_id}] Função target concluída: {result}")
                    
            except Exception as e:
                logger.error(f"[THREAD {thread_id}] Erro na execução: {e}")
                logger.error(f"[THREAD {thread_id}] Traceback: {traceback.format_exc()}")
            
            finally:
                # Remover thread da lista de ativas
                with self.thread_lock:
                    if job_id in self.active_threads:
                        del self.active_threads[job_id]
                logger.info(f"[THREAD {thread_id}] Thread finalizada para job {job_id}")
        
        try:
            # Criar e iniciar thread
            thread = threading.Thread(target=thread_wrapper, name=f"job-{job_id}")
            thread.daemon = True
            
            # Registrar thread
            with self.thread_lock:
                self.active_threads[job_id] = {
                    'thread': thread,
                    'started_at': time.time(),
                    'user_id': user_id
                }
            
            thread.start()
            logger.info(f"[PROCESSOR] Thread iniciada para job {job_id}, thread_id={thread.ident}")
            
            return True
            
        except Exception as e:
            logger.error(f"[PROCESSOR] Erro ao iniciar thread para job {job_id}: {e}")
            return False
    
    def get_active_threads(self):
        """Retorna informações sobre threads ativas"""
        with self.thread_lock:
            return {
                job_id: {
                    'thread_id': info['thread'].ident,
                    'is_alive': info['thread'].is_alive(),
                    'started_at': info['started_at'],
                    'user_id': info['user_id']
                }
                for job_id, info in self.active_threads.items()
            }
    
    def cleanup_finished_threads(self):
        """Remove threads finalizadas da lista"""
        with self.thread_lock:
            finished_jobs = [
                job_id for job_id, info in self.active_threads.items()
                if not info['thread'].is_alive()
            ]
            
            for job_id in finished_jobs:
                del self.active_threads[job_id]
            
            return finished_jobs

# Instância global
thread_processor = None

def init_thread_processor(app):
    """Inicializa o processador de threads"""
    global thread_processor
    thread_processor = ThreadJobProcessor(app)
    return thread_processor

def get_thread_processor():
    """Retorna a instância do processador"""
    return thread_processor