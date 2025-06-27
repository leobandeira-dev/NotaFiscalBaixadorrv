"""
Sistema de Automação Ultra-Otimizado
Integração do UltraFastDownloader com o sistema existente
"""
import os
import time
import logging
import threading
from typing import Dict, Any, List
from ultra_fast_downloader import UltraFastDownloader

logger = logging.getLogger(__name__)

class OptimizedDownloadManager:
    """Gerenciador de downloads ultra-otimizado"""
    
    def __init__(self):
        self.active_jobs = {}
        self.downloader = None
        self._lock = threading.Lock()
    
    def get_downloader(self):
        """Get or create downloader instance"""
        if not self.downloader:
            self.downloader = UltraFastDownloader()
        return self.downloader
    
    def process_download_job_optimized(self, job_id: str, invoice_keys: List[str], user_id: int) -> Dict[str, Any]:
        """Processar job de download com velocidade ultra-otimizada"""
        start_time = time.time()
        
        try:
            with self._lock:
                self.active_jobs[job_id] = {
                    'status': 'running',
                    'progress': 0,
                    'total': len(invoice_keys),
                    'successful': 0,
                    'failed': 0,
                    'start_time': start_time,
                    'files': [],
                    'errors': []
                }
            
            logger.info(f"[Job {job_id}] Iniciando download ultra-otimizado de {len(invoice_keys)} XMLs")
            
            # Usar batch download ultra-rápido
            downloader = self.get_downloader()
            batch_result = downloader.batch_download_ultra_fast(invoice_keys, job_id, user_id)
            
            # Processar resultados
            successful_files = []
            error_list = []
            
            for result in batch_result['results']:
                invoice_key = result['invoice_key']
                
                if result['success']:
                    file_info = {
                        'filename': result.get('filename', f"{invoice_key}.xml"),
                        'size': result.get('size', 0),
                        'download_time': result.get('download_time', 0)
                    }
                    successful_files.append(file_info)
                    
                    # Cobrar pelo download se não estiver em trial
                    self._charge_for_download(user_id, invoice_key)
                    
                else:
                    error_info = {
                        'invoice_key': invoice_key,
                        'error': result.get('error', 'Erro desconhecido')
                    }
                    error_list.append(error_info)
            
            # Atualizar status final
            elapsed_time = time.time() - start_time
            
            with self._lock:
                self.active_jobs[job_id].update({
                    'status': 'completed',
                    'progress': 100,
                    'successful': len(successful_files),
                    'failed': len(error_list),
                    'completion_time': elapsed_time,
                    'files': successful_files,
                    'errors': error_list
                })
            
            logger.info(f"[Job {job_id}] Concluído: {len(successful_files)}/{len(invoice_keys)} sucessos em {elapsed_time:.2f}s")
            
            return {
                'success': True,
                'job_id': job_id,
                'total_time': elapsed_time,
                'successful_count': len(successful_files),
                'total_count': len(invoice_keys),
                'files': successful_files,
                'errors': error_list
            }
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"[Job {job_id}] Erro após {elapsed_time:.2f}s: {str(e)}")
            
            with self._lock:
                self.active_jobs[job_id].update({
                    'status': 'failed',
                    'error': str(e),
                    'completion_time': elapsed_time
                })
            
            return {
                'success': False,
                'job_id': job_id,
                'error': str(e),
                'total_time': elapsed_time
            }
    
    def _charge_for_download(self, user_id: int, invoice_key: str):
        """Cobrar pelo download usando sistema simplificado"""
        try:
            # Verificar se usuário está em trial
            from models import User
            from datetime import datetime
            
            user = User.query.get(user_id)
            if user and user.trial_expires_at and user.trial_expires_at > datetime.utcnow():
                logger.info(f"Usuário {user_id} em trial - download gratuito de {invoice_key}")
                return True
            
            # Cobrar usando sistema simplificado
            from simple_credit_system import consume_xml_credit
            return consume_xml_credit(
                user_id=user_id,
                description=f"Download XML: {invoice_key[:10]}..."
            )
            
        except Exception as e:
            logger.error(f"Erro ao cobrar download: {str(e)}")
            return False
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """Obter status de um job"""
        with self._lock:
            if job_id in self.active_jobs:
                return self.active_jobs[job_id].copy()
            else:
                return {'status': 'not_found'}
    
    def cleanup_job(self, job_id: str):
        """Limpar job após conclusão"""
        with self._lock:
            if job_id in self.active_jobs:
                del self.active_jobs[job_id]
    
    def cleanup_downloader(self):
        """Limpar recursos do downloader"""
        if self.downloader:
            self.downloader.cleanup()
            self.downloader = None

# Instância global do gerenciador otimizado
optimized_manager = OptimizedDownloadManager()

def process_download_job_ultra_fast(job_id: str, invoice_keys: List[str], user_id: int) -> Dict[str, Any]:
    """Função de entrada para processamento ultra-rápido de downloads"""
    return optimized_manager.process_download_job_optimized(job_id, invoice_keys, user_id)

def get_optimized_job_status(job_id: str) -> Dict[str, Any]:
    """Obter status de job otimizado"""
    return optimized_manager.get_job_status(job_id)

def cleanup_optimized_resources():
    """Limpar recursos otimizados"""
    optimized_manager.cleanup_downloader()