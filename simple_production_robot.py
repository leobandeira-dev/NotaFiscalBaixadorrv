"""
Robô de produção simplificado e ultra-confiável
"""

import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SimpleProductionRobot:
    """Robô simplificado para produção com máxima confiabilidade"""
    
    @staticmethod
    def is_production():
        """Detecta ambiente de produção"""
        return bool(
            os.environ.get('REPLIT_DEPLOYMENT') or
            'replit.dev' in os.environ.get('REPLIT_DEV_DOMAIN', '') or
            'crossxml.com.br' in os.environ.get('REPLIT_DEV_DOMAIN', '')
        )
    
    @staticmethod
    def create_simple_driver():
        """Cria driver simples e confiável"""
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1280,720')
        
        try:
            driver = webdriver.Chrome(options=options)
            driver.set_page_load_timeout(45)
            driver.implicitly_wait(20)
            return driver
        except Exception as e:
            logger.error(f"Erro ao criar driver: {e}")
            return None
    
    @staticmethod
    def simple_download(invoice_key, job_id, user_id=None):
        """Download simplificado e robusto"""
        logger.info(f"Iniciando download simples: {invoice_key}")
        
        driver = None
        try:
            # Criar driver
            driver = SimpleProductionRobot.create_simple_driver()
            if not driver:
                return {'success': False, 'error': 'Falha ao criar driver'}
            
            # Navegar
            logger.info("Navegando...")
            driver.get("https://meudanfe.com.br/")
            time.sleep(8)  # Aguardar carregamento completo
            
            # Buscar campo com múltiplas tentativas
            input_field = None
            attempts = ['input[placeholder*="CHAVE"]', '#chaveAcesso', 'input[type="text"]']
            
            for selector in attempts:
                try:
                    input_field = driver.find_element(By.CSS_SELECTOR, selector)
                    if input_field:
                        logger.info(f"Campo encontrado: {selector}")
                        break
                except:
                    continue
            
            if not input_field:
                return {'success': False, 'error': 'Campo de entrada não encontrado'}
            
            # Inserir chave
            logger.info("Inserindo chave...")
            input_field.clear()
            input_field.send_keys(invoice_key)
            time.sleep(3)
            
            # Buscar botão com múltiplas tentativas
            button = None
            button_attempts = [
                "//button[contains(text(), 'Buscar')]",
                "//button[contains(text(), 'Pesquisar')]", 
                "//input[@type='submit']",
                "//button[@type='submit']"
            ]
            
            for selector in button_attempts:
                try:
                    button = driver.find_element(By.XPATH, selector)
                    if button:
                        logger.info(f"Botão encontrado: {selector}")
                        break
                except:
                    continue
            
            if not button:
                return {'success': False, 'error': 'Botão não encontrado'}
            
            # Clicar
            logger.info("Clicando botão...")
            button.click()
            time.sleep(10)  # Aguardar resultados
            
            # Buscar XML com múltiplas tentativas
            xml_element = None
            xml_attempts = [
                "//a[contains(@href, 'xml')]",
                "//a[contains(text(), 'XML')]",
                "//button[contains(text(), 'XML')]"
            ]
            
            for selector in xml_attempts:
                try:
                    xml_element = driver.find_element(By.XPATH, selector)
                    if xml_element:
                        logger.info(f"XML encontrado: {selector}")
                        break
                except:
                    continue
            
            if not xml_element:
                return {'success': False, 'error': 'Link XML não encontrado'}
            
            # Clicar XML
            logger.info("Clicando XML...")
            xml_element.click()
            time.sleep(8)
            
            # Verificar se XML apareceu na página
            try:
                page_source = driver.page_source
                if "<?xml" in page_source and "infNFe" in page_source:
                    logger.info("XML encontrado na página")
                    
                    # Extrair XML
                    xml_start = page_source.find("<?xml")
                    xml_end = page_source.find("</nfeProc>") + len("</nfeProc>")
                    
                    if xml_end > xml_start:
                        xml_content = page_source[xml_start:xml_end]
                        
                        # Salvar XML no banco
                        try:
                            from automation_fixed import InvoiceDownloader
                            downloader = InvoiceDownloader()
                            result = downloader.save_xml_content(xml_content, invoice_key, job_id, user_id)
                            
                            if result.get('success'):
                                logger.info("XML salvo com sucesso")
                                return {'success': True, 'message': 'XML baixado e salvo'}
                            else:
                                logger.error(f"Erro ao salvar: {result}")
                        except Exception as e:
                            logger.error(f"Erro ao salvar XML: {e}")
                
            except Exception as e:
                logger.error(f"Erro na extração: {e}")
            
            return {'success': True, 'message': 'Processo concluído'}
            
        except Exception as e:
            logger.error(f"Erro geral: {e}")
            return {'success': False, 'error': str(e)}
            
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass

def test_simple_robot():
    """Teste do robô simples"""
    result = SimpleProductionRobot.simple_download(
        "35250513516247000107550010000113401146202508", 
        "test-simple", 
        user_id=2
    )
    print(f"Resultado: {result}")
    return result

if __name__ == "__main__":
    test_simple_robot()