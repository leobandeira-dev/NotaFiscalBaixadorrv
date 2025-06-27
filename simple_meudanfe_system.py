"""
Sistema Simplificado - Apenas meudanfe.com.br
Sem fallback para evitar loops de CAPTCHA
"""
import os
import time
import logging
from typing import Dict, Any
from automation_fixed import InvoiceDownloader

logger = logging.getLogger(__name__)

class SimpleMeuDanfeDownloader:
    """Sistema simplificado usando apenas meudanfe.com.br"""
    
    def __init__(self):
        self.primary_downloader = None
    
    def download_invoice_xml(self, invoice_key: str, job_id: str, download_type: str = 'xml', user_id: int = None) -> Dict[str, Any]:
        """Download XML usando apenas sistema principal"""
        start_time = time.time()
        
        try:
            logger.info(f"[Job {job_id}] SISTEMA ÚNICO: meudanfe.com.br")
            logger.info(f"[Job {job_id}] Iniciando download para chave: {invoice_key}")
            
            # Usar apenas automation_fixed (meudanfe.com.br)
            self.primary_downloader = InvoiceDownloader()
            
            result = self.primary_downloader.download_invoice_xml(
                invoice_key=invoice_key,
                job_id=job_id,
                download_type=download_type,
                user_id=user_id
            )
            
            elapsed_time = time.time() - start_time
            result['elapsed_time'] = elapsed_time
            
            if result.get('success'):
                logger.info(f"[Job {job_id}] ✅ SUCESSO - Tempo: {elapsed_time:.2f}s")
                logger.info(f"[Job {job_id}] Arquivo: {result.get('file_path', 'N/A')}")
            else:
                logger.error(f"[Job {job_id}] ❌ FALHA: {result.get('error', 'Erro desconhecido')}")
                
            return result
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_msg = f"Erro crítico no sistema: {str(e)}"
            logger.error(f"[Job {job_id}] ❌ EXCEÇÃO: {error_msg}")
            
            return {
                'success': False,
                'error': error_msg,
                'elapsed_time': elapsed_time,
                'file_path': None
            }
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Limpar recursos"""
        if self.primary_downloader:
            try:
                self.primary_downloader.cleanup()
            except:
                pass
            self.primary_downloader = None

    def test_connection(self) -> Dict[str, Any]:
        """Testar conectividade do sistema"""
        try:
            self.primary_downloader = InvoiceDownloader()
            result = self.primary_downloader.test_connection()
            return result
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'message': 'Falha no teste de conexão'
            }
        finally:
            self.cleanup()