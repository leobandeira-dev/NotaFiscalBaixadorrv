"""
Correção definitiva do robô XML para ambiente de deploy
Resolve problema identificado: seletores CSS e timeouts inadequados
"""

import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def create_robust_xml_downloader():
    """Cria robô XML robusto para todos os ambientes"""
    
    class RobustXMLDownloader:
        def __init__(self):
            self.driver = None
            self.logger = logging.getLogger(__name__)
            
        def setup_driver(self):
            """Configuração robusta do Chrome para qualquer ambiente"""
            options = Options()
            
            # Configurações universais que funcionam em dev e deploy
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1024,768')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--single-process')
            
            # Configurações de download
            downloads_dir = os.path.join(os.getcwd(), 'downloads')
            os.makedirs(downloads_dir, exist_ok=True)
            
            prefs = {
                "download.default_directory": downloads_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            options.add_experimental_option("prefs", prefs)
            
            # Criar driver com path específico se disponível
            chromedriver_path = "/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver"
            
            try:
                if os.path.exists(chromedriver_path):
                    from selenium.webdriver.chrome.service import Service
                    service = Service(chromedriver_path)
                    self.driver = webdriver.Chrome(service=service, options=options)
                else:
                    self.driver = webdriver.Chrome(options=options)
                
                # Timeouts robustos
                self.driver.set_page_load_timeout(45)
                self.driver.implicitly_wait(8)
                
                self.logger.info("Driver XML robusto inicializado")
                return True
                
            except Exception as e:
                self.logger.error(f"Erro ao criar driver: {e}")
                return False
        
        def download_xml(self, invoice_key):
            """Download XML com estratégias múltiplas de fallback"""
            
            if not self.setup_driver():
                return {'success': False, 'message': 'Falha ao inicializar driver'}
            
            try:
                # 1. Navegar para o site
                self.logger.info("Acessando sistema de notas fiscais...")
                self.driver.get("https://meudanfe.com.br/")
                
                # Aguardar carregamento completo
                wait = WebDriverWait(self.driver, 15)
                wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                time.sleep(3)
                
                # 2. Encontrar e preencher campo da chave
                self.logger.info("Preenchendo chave da nota fiscal...")
                
                # Estratégia robusta para campo da chave
                chave_selectors = [
                    'input[placeholder*="CHAVE"]',
                    'input[placeholder*="chave"]',
                    'input[name*="chave"]',
                    'input[id*="chave"]',
                    'input[type="text"]'
                ]
                
                chave_field = None
                for selector in chave_selectors:
                    try:
                        chave_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                        if chave_field and chave_field.is_displayed():
                            break
                    except:
                        continue
                
                if not chave_field:
                    return {'success': False, 'message': 'Campo da chave não encontrado'}
                
                # Preencher chave
                chave_field.clear()
                chave_field.send_keys(invoice_key)
                time.sleep(1)
                
                # 3. Enviar consulta usando múltiplas estratégias
                self.logger.info("Enviando consulta...")
                consulta_success = False
                
                # Estratégia 1: ENTER no campo
                try:
                    chave_field.send_keys(Keys.RETURN)
                    consulta_success = True
                    self.logger.info("Consulta via ENTER")
                except:
                    pass
                
                # Estratégia 2: Encontrar botão submit
                if not consulta_success:
                    try:
                        submit_selectors = [
                            'button[type="submit"]',
                            'input[type="submit"]',
                            'button.btn',
                            'button'
                        ]
                        
                        for selector in submit_selectors:
                            try:
                                buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                                for btn in buttons:
                                    if btn.is_displayed() and btn.is_enabled():
                                        try:
                                            btn.click()
                                            consulta_success = True
                                            self.logger.info("Consulta via botão")
                                            break
                                        except:
                                            continue
                                if consulta_success:
                                    break
                            except:
                                continue
                    except:
                        pass
                
                # Estratégia 3: JavaScript submit
                if not consulta_success:
                    try:
                        self.driver.execute_script("document.forms[0].submit();")
                        consulta_success = True
                        self.logger.info("Consulta via JavaScript")
                    except:
                        pass
                
                if not consulta_success:
                    return {'success': False, 'message': 'Falha ao enviar consulta'}
                
                # 4. Aguardar resultado
                self.logger.info("Aguardando processamento...")
                time.sleep(10)  # Tempo robusto para processamento
                
                # 5. Procurar e clicar botão XML
                self.logger.info("Procurando opção de download XML...")
                xml_success = False
                
                # Estratégias múltiplas para encontrar XML
                xml_strategies = [
                    # XPath strategies
                    (By.XPATH, "//button[contains(text(), 'XML')]"),
                    (By.XPATH, "//a[contains(text(), 'XML')]"),
                    (By.XPATH, "//input[@value='XML']"),
                    (By.XPATH, "//*[contains(text(), 'XML')]"),
                    # CSS strategies
                    (By.CSS_SELECTOR, "button[value*='xml']"),
                    (By.CSS_SELECTOR, "a[href*='xml']"),
                    (By.CSS_SELECTOR, "[onclick*='xml']"),
                ]
                
                for by_type, selector in xml_strategies:
                    try:
                        elements = self.driver.find_elements(by_type, selector)
                        for element in elements:
                            if element.is_displayed():
                                try:
                                    # Tentar clique normal
                                    element.click()
                                    xml_success = True
                                    self.logger.info("XML clicado com sucesso")
                                    break
                                except:
                                    try:
                                        # Fallback: JavaScript click
                                        self.driver.execute_script("arguments[0].click();", element)
                                        xml_success = True
                                        self.logger.info("XML clicado via JavaScript")
                                        break
                                    except:
                                        continue
                        if xml_success:
                            break
                    except:
                        continue
                
                if not xml_success:
                    return {'success': False, 'message': 'Botão XML não encontrado ou inacessível'}
                
                # 6. Aguardar download
                self.logger.info("Aguardando download...")
                time.sleep(8)
                
                # 7. Verificar arquivo baixado
                downloads_dir = os.path.join(os.getcwd(), 'downloads')
                if os.path.exists(downloads_dir):
                    files = os.listdir(downloads_dir)
                    xml_files = [f for f in files if f.endswith('.xml') and invoice_key[:10] in f]
                    
                    if xml_files:
                        latest_file = max(xml_files, key=lambda f: os.path.getctime(os.path.join(downloads_dir, f)))
                        file_size = os.path.getsize(os.path.join(downloads_dir, latest_file))
                        
                        self.logger.info(f"XML baixado: {latest_file} ({file_size} bytes)")
                        
                        return {
                            'success': True,
                            'message': 'XML baixado com sucesso',
                            'filename': latest_file,
                            'size_bytes': file_size,
                            'path': os.path.join(downloads_dir, latest_file)
                        }
                
                return {'success': False, 'message': 'Arquivo XML não foi baixado'}
                
            except Exception as e:
                self.logger.error(f"Erro durante download: {e}")
                return {'success': False, 'message': f'Erro: {str(e)}'}
            
            finally:
                self.cleanup()
        
        def cleanup(self):
            """Limpeza de recursos"""
            if self.driver:
                try:
                    self.driver.quit()
                    self.logger.info("Driver encerrado")
                except:
                    pass
    
    return RobustXMLDownloader()

def test_robust_download():
    """Teste da versão robusta do robô XML"""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Iniciando teste do robô XML robusto...")
    
    # Criar instância do robô
    downloader = create_robust_xml_downloader()
    
    # Testar com chave real
    invoice_key = "44250485179240000239550020004175361171503396"
    result = downloader.download_xml(invoice_key)
    
    return result

if __name__ == "__main__":
    result = test_robust_download()
    
    print("\n" + "="*60)
    print("🤖 TESTE DO ROBÔ XML ROBUSTO")
    print("="*60)
    print(f"Status: {'✅ SUCESSO' if result['success'] else '❌ FALHA'}")
    print(f"Mensagem: {result['message']}")
    
    if result['success']:
        print(f"Arquivo: {result.get('filename', 'N/A')}")
        print(f"Tamanho: {result.get('size_bytes', 0)} bytes")
        print(f"Caminho: {result.get('path', 'N/A')}")
    
    print("="*60)