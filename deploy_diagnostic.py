"""
Sistema de diagnóstico em tempo real para problemas de deploy
"""

import logging
import threading
import time
import os
from deploy_robot_fix import DeployRobotFix
from automation_fixed import InvoiceDownloader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeployDiagnostic:
    """Sistema de diagnóstico para problemas de deploy"""
    
    def __init__(self):
        self.is_running = False
        self.results = {}
    
    def diagnose_stuck_download(self, job_id="diagnostic-test"):
        """Diagnostica problemas de download travado"""
        logger.info("🔍 Iniciando diagnóstico de download travado...")
        
        # Verificar ambiente
        is_deploy = DeployRobotFix.is_deploy_environment()
        logger.info(f"📍 Ambiente detectado: {'Deploy' if is_deploy else 'Desenvolvimento'}")
        
        # Testar conectividade básica
        logger.info("🌐 Testando conectividade...")
        try:
            import requests
            response = requests.get("https://meudanfe.com.br/", timeout=10)
            logger.info(f"✅ Conectividade OK: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ Erro de conectividade: {e}")
            return False
        
        # Testar criação do driver
        logger.info("🚗 Testando criação do Chrome driver...")
        try:
            if is_deploy:
                driver = DeployRobotFix.create_deploy_driver()
                timeouts = DeployRobotFix.get_deploy_timeouts()
            else:
                from ultra_performance_deploy import ChromeDriverManager
                driver = ChromeDriverManager.get_optimized_driver()
                timeouts = {'element_wait': 3, 'xml_button': 2}
            
            if driver:
                logger.info("✅ Driver criado com sucesso")
                logger.info(f"⏱️ Timeouts configurados: {timeouts}")
                
                # Testar navegação
                logger.info("🔗 Testando navegação para meudanfe.com.br...")
                driver.get("https://meudanfe.com.br/")
                time.sleep(3)
                
                current_url = driver.current_url
                logger.info(f"📍 URL atual: {current_url}")
                
                if "meudanfe" in current_url.lower():
                    logger.info("✅ Navegação bem-sucedida")
                else:
                    logger.error(f"❌ Navegação falhou - URL inesperada: {current_url}")
                
                driver.quit()
                return True
            else:
                logger.error("❌ Falha na criação do driver")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro no teste do driver: {e}")
            return False
    
    def test_full_download_process(self):
        """Testa processo completo de download com logs detalhados"""
        logger.info("🧪 Iniciando teste completo de download...")
        
        try:
            downloader = InvoiceDownloader()
            logger.info("✅ InvoiceDownloader criado")
            
            # Testar com chave conhecida
            test_key = "35250513516247000107550010000113401146202508"
            logger.info(f"🔑 Testando com chave: {test_key}")
            
            # Configurar timeout mais longo para diagnóstico
            logger.info("⏱️ Executando download com timeout estendido...")
            
            result = downloader.download_invoice_xml(test_key, "diagnostic-test", user_id=2)
            
            logger.info(f"📊 Resultado do download: {result}")
            
            if result.get('success'):
                logger.info("✅ Download bem-sucedido!")
                return True
            else:
                logger.error(f"❌ Download falhou: {result.get('error', 'Erro desconhecido')}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erro no teste de download: {e}")
            return False
        finally:
            try:
                if 'downloader' in locals():
                    downloader.cleanup()
                    logger.info("🧹 Cleanup executado")
            except:
                pass
    
    def monitor_job_status(self, job_id, max_time=120):
        """Monitora status de job em tempo real"""
        logger.info(f"👁️ Monitorando job {job_id} por até {max_time} segundos...")
        
        start_time = time.time()
        
        while time.time() - start_time < max_time:
            try:
                # Importar e verificar status do job
                from new_app import DownloadJob, db, app
                
                with app.app_context():
                    job = DownloadJob.query.filter_by(job_id=job_id).first()
                    
                    if job:
                        logger.info(f"📊 Job {job_id}: {job.status} - {job.processed}/{job.total_keys} processados")
                        
                        if job.status in ['completed', 'failed']:
                            logger.info(f"🏁 Job finalizado com status: {job.status}")
                            return job.status
                    else:
                        logger.warning(f"⚠️ Job {job_id} não encontrado no banco")
                
                time.sleep(5)  # Verificar a cada 5 segundos
                
            except Exception as e:
                logger.error(f"❌ Erro ao monitorar job: {e}")
                time.sleep(5)
        
        logger.error(f"⏰ Timeout: Job {job_id} não finalizou em {max_time} segundos")
        return "timeout"
    
    def run_comprehensive_diagnostic(self):
        """Executa diagnóstico completo"""
        logger.info("=" * 60)
        logger.info("DIAGNÓSTICO COMPLETO DE DEPLOY")
        logger.info("=" * 60)
        
        # Teste 1: Diagnóstico básico
        logger.info("\n🔍 TESTE 1: Diagnóstico básico")
        basic_ok = self.diagnose_stuck_download()
        
        # Teste 2: Processo completo
        logger.info("\n🔍 TESTE 2: Processo completo de download")
        download_ok = self.test_full_download_process()
        
        # Resumo
        logger.info("\n" + "=" * 60)
        logger.info("RESUMO DO DIAGNÓSTICO")
        logger.info("=" * 60)
        logger.info(f"Diagnóstico básico: {'✅ OK' if basic_ok else '❌ FALHOU'}")
        logger.info(f"Download completo: {'✅ OK' if download_ok else '❌ FALHOU'}")
        
        if basic_ok and download_ok:
            logger.info("🎉 SISTEMA FUNCIONANDO CORRETAMENTE")
        else:
            logger.error("⚠️ PROBLEMAS DETECTADOS - Implementando correções...")
        
        return basic_ok and download_ok

if __name__ == "__main__":
    diagnostic = DeployDiagnostic()
    diagnostic.run_comprehensive_diagnostic()