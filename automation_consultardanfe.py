"""
Sistema de Automação Integrado com Consultardanfe.com
Sistema principal: consultardanfe.com
Sistema fallback: meudanfe.com.br (via automation_fixed.py)
"""
import os
import time
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class InvoiceDownloader:
    """Sistema integrado de download usando consultardanfe.com como principal"""
    
    def __init__(self):
        self.primary_downloader = None
        self.fallback_downloader = None
    
    def download_invoice_xml(self, invoice_key: str, job_id: str, download_type: str = 'xml', user_id: int = None) -> Dict[str, Any]:
        """Download XML com sistema principal + fallback"""
        start_time = time.time()
        
        try:
            logger.info(f"[Job {job_id}] Iniciando download para chave: {invoice_key}")
            
            # SISTEMA PRINCIPAL: consultardanfe.com
            logger.info(f"[Job {job_id}] Sistema Principal: consultardanfe.com")
            
            from consultardanfe_automation import ConsultarDanfeAutomation
            
            try:
                primary_downloader = ConsultarDanfeAutomation()
                result = primary_downloader.download_xml(invoice_key, job_id, user_id)
                
                if result.get('success'):
                    # Processar sucesso através do sistema de billing
                    if user_id:
                        processed = self._process_successful_download(
                            user_id=user_id,
                            invoice_key=invoice_key,
                            file_path=result.get('file_path'),
                            job_id=job_id
                        )
                        
                        if processed:
                            logger.info(f"[Job {job_id}] ✅ SUCESSO - Sistema Principal - Tempo: {time.time() - start_time:.2f}s")
                            return result
                    else:
                        logger.info(f"[Job {job_id}] ✅ SUCESSO - Sistema Principal - Tempo: {time.time() - start_time:.2f}s")
                        return result
                else:
                    logger.warning(f"[Job {job_id}] Sistema principal falhou: {result.get('error', 'Erro desconhecido')}")
                    
            except Exception as primary_error:
                logger.warning(f"[Job {job_id}] Exceção no sistema principal: {str(primary_error)[:200]}")
            
            finally:
                if 'primary_downloader' in locals():
                    try:
                        primary_downloader.cleanup()
                    except:
                        pass
            
            # SISTEMA FALLBACK: meudanfe.com.br
            logger.info(f"[Job {job_id}] Sistema Backup: meudanfe.com.br")
            
            try:
                from automation_fixed import InvoiceDownloader as FallbackDownloader
                fallback_downloader = FallbackDownloader()
                
                result = fallback_downloader.download_invoice_xml(
                    invoice_key=invoice_key,
                    job_id=job_id,
                    download_type=download_type,
                    user_id=user_id
                )
                
                if result.get('success'):
                    logger.info(f"[Job {job_id}] ✅ SUCESSO - Sistema Backup - Tempo: {time.time() - start_time:.2f}s")
                    return result
                else:
                    logger.error(f"[Job {job_id}] Sistema backup também falhou: {result.get('error', 'Erro desconhecido')}")
                    
            except Exception as fallback_error:
                logger.error(f"[Job {job_id}] Exceção no sistema backup: {str(fallback_error)[:200]}")
            
            finally:
                if 'fallback_downloader' in locals():
                    try:
                        fallback_downloader.cleanup()
                    except:
                        pass
            
            # Ambos sistemas falharam
            elapsed_time = time.time() - start_time
            logger.error(f"[Job {job_id}] ❌ FALHA TOTAL - Ambos sistemas falharam - Tempo: {elapsed_time:.2f}s")
            
            return {
                'success': False,
                'error': 'Todos os sistemas de download falharam. Tente novamente em alguns minutos.',
                'elapsed_time': elapsed_time
            }
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"[Job {job_id}] Erro crítico no sistema de download: {str(e)}")
            return {
                'success': False,
                'error': f'Erro crítico: {str(e)}',
                'elapsed_time': elapsed_time
            }
    
    def _process_successful_download(self, user_id: int, invoice_key: str, file_path: str, job_id: str) -> bool:
        """Processar download bem-sucedido no sistema de billing"""
        try:
            from download_service import DownloadService
            
            # Ler conteúdo do XML baixado
            if file_path and os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    xml_content = f.read()
                
                # Processar através do sistema de cobrança
                processed = DownloadService.process_successful_download(
                    user_id=user_id,
                    invoice_key=invoice_key,
                    xml_content=xml_content,
                    file_path=file_path,
                    job_id=job_id
                )
                
                if processed:
                    logger.info(f"[Job {job_id}] XML processado e salvo no banco")
                    return True
                else:
                    logger.warning(f"[Job {job_id}] Falha ao processar XML no banco")
                    return False
            else:
                logger.error(f"[Job {job_id}] Arquivo XML não encontrado: {file_path}")
                return False
                
        except Exception as e:
            logger.error(f"[Job {job_id}] Erro ao processar download: {e}")
            return False
    
    def cleanup(self):
        """Limpar recursos"""
        try:
            if self.primary_downloader:
                self.primary_downloader.cleanup()
        except:
            pass
        
        try:
            if self.fallback_downloader:
                self.fallback_downloader.cleanup()
        except:
            pass