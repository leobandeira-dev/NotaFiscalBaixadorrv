#!/usr/bin/env python3
"""
Sistema de automação atualizado para consultardanfe.com
Versão 2025 com suporte a reCAPTCHA e nova estrutura do site
"""

import os
import sys
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.common.keys import Keys
import requests
from performance_solution import DeployOptimizer

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConsultarDanfeFallback:
    """Automação para consultardanfe.com com suporte a CAPTCHA"""
    
    def __init__(self):
        self.base_url = "https://consultardanfe.com/"
        self.driver = None
        self.optimizer = DeployOptimizer()
        
    def setup_driver(self):
        """Configurar Chrome WebDriver com otimizações para DEPLOY"""
        try:
            chrome_options = Options()
            
            # Aplicar otimizações para deploy
            if self.optimizer.is_deploy_environment():
                chrome_options.add_argument('--headless=new')
                chrome_options.add_argument('--window-size=400,300')
                chrome_options.add_argument('--memory-pressure-off')
                chrome_options.add_argument('--max_old_space_size=512')
            else:
                chrome_options.add_argument('--headless')
                chrome_options.add_argument('--window-size=800,600')
            
            # Configurações específicas para consultardanfe
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # User agent real
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Configurações de download
            download_dir = os.path.abspath('./downloads')
            os.makedirs(download_dir, exist_ok=True)
            
            prefs = {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Localizar chromedriver
            chromedriver_path = None
            possible_paths = [
                '/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver',
                '/usr/bin/chromedriver',
                'chromedriver'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    chromedriver_path = path
                    break
            
            if not chromedriver_path:
                raise Exception("ChromeDriver não encontrado")
            
            logger.info(f"Using chromedriver at: {chromedriver_path}")
            service = Service(chromedriver_path)
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Remover propriedades de automação
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Fallback Chrome WebDriver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup WebDriver: {str(e)}")
            return False
    
    def handle_captcha_popup(self, job_id):
        """Tentar lidar com popup de CAPTCHA"""
        try:
            logger.info(f"[Fallback {job_id}] Verificando popup de CAPTCHA...")
            
            # Aguardar um pouco para o popup aparecer
            time.sleep(2)
            
            # Procurar por elementos do reCAPTCHA
            captcha_selectors = [
                'iframe[src*="recaptcha"]',
                '.g-recaptcha',
                '[data-sitekey]',
                'iframe[title*="reCAPTCHA"]'
            ]
            
            captcha_found = False
            for selector in captcha_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        logger.warning(f"[Fallback {job_id}] CAPTCHA detectado: {selector}")
                        captcha_found = True
                        break
                except:
                    continue
            
            if captcha_found:
                logger.warning(f"[Fallback {job_id}] CAPTCHA presente - tentando estratégias de contorno...")
                
                # Estratégia 1: Aguardar e tentar prosseguir
                time.sleep(3)
                
                # Estratégia 2: Pressionar ESC para fechar popup
                try:
                    self.driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
                    time.sleep(1)
                except:
                    pass
                
                # Estratégia 3: Procurar botão de fechar
                close_selectors = [
                    'button[class*="close"]',
                    '.close',
                    '[aria-label="Close"]',
                    '[aria-label="Fechar"]'
                ]
                
                for selector in close_selectors:
                    try:
                        close_btn = self.driver.find_element(By.CSS_SELECTOR, selector)
                        if close_btn.is_displayed():
                            close_btn.click()
                            time.sleep(1)
                            logger.info(f"[Fallback {job_id}] Popup fechado com sucesso")
                            return True
                    except:
                        continue
                
                return False  # CAPTCHA não resolvido
            
            return True  # Sem CAPTCHA
            
        except Exception as e:
            logger.error(f"[Fallback {job_id}] Erro ao lidar com CAPTCHA: {str(e)}")
            return False
    
    def download_invoice_xml(self, invoice_key: str, job_id: str, user_id: int = None):
        """Download XML usando consultardanfe.com como fallback"""
        start_time = time.time()
        
        try:
            logger.info(f"[Fallback {job_id}] Starting XML download for invoice key: {invoice_key}")
            
            if not self.setup_driver():
                raise Exception("Failed to initialize WebDriver")
            
            # Navegar para o site
            logger.info(f"[Fallback {job_id}] Navigating to fallback site...")
            self.driver.get(self.base_url)
            
            # Aguardar página carregar
            wait_time = 8 if self.optimizer.is_deploy_environment() else 5
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Procurar campo de entrada da chave
            logger.info(f"[Fallback {job_id}] Looking for invoice key input field...")
            
            # Possíveis seletores para o campo de entrada
            input_selectors = [
                'input[placeholder*="chave"]',
                'input[name*="chave"]',
                'input[id*="chave"]',
                'input[type="text"]',
                'input[placeholder*="Chave"]',
                'input[placeholder*="44"]',
                'textarea[placeholder*="chave"]'
            ]
            
            input_field = None
            for selector in input_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            input_field = element
                            logger.info(f"[Fallback {job_id}] Found input field with selector: {selector}")
                            break
                    if input_field:
                        break
                except:
                    continue
            
            if not input_field:
                raise Exception("Input field not found on fallback site")
            
            # Inserir chave da nota fiscal
            logger.info(f"[Fallback {job_id}] Entering invoice key...")
            input_field.clear()
            input_field.send_keys(invoice_key)
            time.sleep(1)
            
            # Procurar botão de envio
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button[class*="submit"]',
                'button[class*="btn"]',
                '.btn-primary',
                'button:contains("Consultar")',
                'button:contains("Buscar")',
                'button:contains("Gerar")'
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            submit_button = element
                            logger.info(f"[Fallback {job_id}] Found submit button with selector: {selector}")
                            break
                    if submit_button:
                        break
                except:
                    continue
            
            if not submit_button:
                # Tentar Enter no campo de entrada
                logger.info(f"[Fallback {job_id}] No submit button found, trying Enter key...")
                input_field.send_keys(Keys.RETURN)
            else:
                logger.info(f"[Fallback {job_id}] Clicking submit button...")
                submit_button.click()
            
            time.sleep(2)
            
            # Verificar se há CAPTCHA
            if not self.handle_captcha_popup(job_id):
                raise Exception("CAPTCHA detected and could not be bypassed")
            
            # Aguardar resultado
            logger.info(f"[Fallback {job_id}] Waiting for results...")
            time.sleep(5)
            
            # Procurar link de download do XML
            download_selectors = [
                'a[href*=".xml"]',
                'a[href*="xml"]',
                'a[download*=".xml"]',
                '.download-xml',
                '[data-type="xml"]',
                'button[onclick*="xml"]'
            ]
            
            download_link = None
            for selector in download_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed():
                            download_link = element
                            logger.info(f"[Fallback {job_id}] Found download link with selector: {selector}")
                            break
                    if download_link:
                        break
                except:
                    continue
            
            if not download_link:
                raise Exception("Download link not found")
            
            # Obter URL de download
            download_url = download_link.get_attribute('href')
            if not download_url:
                download_url = download_link.get_attribute('onclick')
                if download_url and 'http' in download_url:
                    # Extrair URL do onclick
                    import re
                    url_match = re.search(r'https?://[^\'"]+', download_url)
                    if url_match:
                        download_url = url_match.group()
            
            if not download_url or 'http' not in download_url:
                raise Exception("Valid download URL not found")
            
            logger.info(f"[Fallback {job_id}] Found download URL: {download_url}")
            
            # Download do arquivo
            logger.info(f"[Fallback {job_id}] Downloading XML file...")
            response = requests.get(download_url, timeout=30)
            response.raise_for_status()
            
            # Salvar arquivo
            filename = f"{invoice_key}.xml"
            file_path = os.path.join('./downloads', filename)
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"[Fallback {job_id}] XML downloaded successfully: {filename}")
            
            elapsed_time = time.time() - start_time
            logger.info(f"📊 FALLBACK PERFORMANCE: {elapsed_time:.3f}s")
            
            return {
                'success': True,
                'filename': filename,
                'file_path': file_path,
                'message': f'XML downloaded successfully via fallback system'
            }
            
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(f"[Fallback {job_id}] Failed after {elapsed_time:.3f}s: {str(e)}")
            
            return {
                'success': False,
                'error': str(e),
                'message': f'Fallback download failed: {str(e)}'
            }
            
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("Fallback WebDriver closed successfully")
                except:
                    pass
    
    def test_connection(self):
        """Testar conectividade com o site de fallback"""
        try:
            if not self.setup_driver():
                return {
                    'success': False,
                    'message': 'Failed to initialize WebDriver'
                }
            
            self.driver.get(self.base_url)
            time.sleep(3)
            
            title = self.driver.title
            current_url = self.driver.current_url
            
            success = 'consultardanfe' in title.lower() or 'consultardanfe' in current_url.lower()
            
            return {
                'success': success,
                'message': f'Fallback site accessible. Title: {title}',
                'url': current_url
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Fallback connection failed: {str(e)}'
            }
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                except:
                    pass

if __name__ == "__main__":
    # Teste rápido
    automation = ConsultarDanfeFallback()
    result = automation.test_connection()
    print(f"Teste de conexão: {result}")