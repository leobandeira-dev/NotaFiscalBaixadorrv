#!/usr/bin/env python3
"""
Sistema de automação usando Firefox como alternativa ao Chrome
Solução para problemas de WebDriver em ambiente containerizado
"""

import os
import logging
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger(__name__)

class FirefoxFallbackDownloader:
    """Sistema de download usando Firefox WebDriver"""
    
    def __init__(self):
        self.driver = None
        self.base_url = "https://consultardanfe.com"
        
    def setup_firefox_driver(self):
        """Configurar Firefox WebDriver com otimizações para container"""
        try:
            firefox_options = Options()
            
            # Configurações headless otimizadas para container
            firefox_options.add_argument('--headless')
            firefox_options.add_argument('--no-sandbox')
            firefox_options.add_argument('--disable-dev-shm-usage')
            firefox_options.add_argument('--disable-gpu')
            firefox_options.add_argument('--window-size=800,600')
            
            # Configurações de performance
            firefox_options.add_argument('--disable-extensions')
            firefox_options.add_argument('--disable-plugins')
            firefox_options.add_argument('--disable-images')
            
            # Configurações de rede
            firefox_options.add_argument('--disable-web-security')
            firefox_options.add_argument('--disable-features=VizDisplayCompositor')
            
            # Configurar User-Agent
            firefox_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64; rv:91.0) Gecko/20100101 Firefox/91.0')
            
            # Tentar encontrar geckodriver
            geckodriver_paths = [
                '/usr/local/bin/geckodriver',
                '/usr/bin/geckodriver',
                '/home/runner/.local/bin/geckodriver',
                'geckodriver'
            ]
            
            geckodriver_path = None
            for path in geckodriver_paths:
                if os.path.exists(path) or path == 'geckodriver':
                    geckodriver_path = path
                    break
            
            if geckodriver_path:
                logger.info(f"Using geckodriver at: {geckodriver_path}")
                service = Service(geckodriver_path)
                self.driver = webdriver.Firefox(service=service, options=firefox_options)
            else:
                logger.info("Using system geckodriver")
                self.driver = webdriver.Firefox(options=firefox_options)
            
            # Configurar timeouts
            self.driver.implicitly_wait(5)
            self.driver.set_page_load_timeout(15)
            
            logger.info("Firefox WebDriver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup Firefox WebDriver: {str(e)}")
            return False
    
    def download_invoice_xml(self, invoice_key: str, job_id: str, user_id: int = None):
        """Download XML usando Firefox"""
        try:
            logger.info(f"[Firefox {job_id}] Starting XML download for invoice key: {invoice_key}")
            
            # Configurar driver
            if not self.setup_firefox_driver():
                return {
                    'success': False,
                    'error': 'Failed to initialize Firefox WebDriver',
                    'message': 'Firefox fallback initialization failed'
                }
            
            # Navegar para o site
            logger.info(f"[Firefox {job_id}] Navigating to fallback site...")
            self.driver.get(self.base_url)
            
            # Aguardar página carregar
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            logger.info(f"[Firefox {job_id}] Page loaded successfully")
            
            # Procurar campo de entrada
            try:
                input_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'], input[placeholder*='chave'], input[name*='chave']"))
                )
                
                logger.info(f"[Firefox {job_id}] Input field found")
                
                # Inserir chave
                input_field.clear()
                input_field.send_keys(invoice_key)
                
                time.sleep(1)
                
                # Procurar botão de submit
                submit_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit'], input[type='submit'], .btn-submit"))
                )
                
                logger.info(f"[Firefox {job_id}] Clicking submit button...")
                submit_button.click()
                
                # Aguardar resposta
                time.sleep(3)
                
                # Verificar se há XML disponível
                page_source = self.driver.page_source
                if "xml" in page_source.lower() or "download" in page_source.lower():
                    logger.info(f"[Firefox {job_id}] XML content detected")
                    
                    return {
                        'success': True,
                        'filename': f"{invoice_key}_firefox.xml",
                        'message': 'Firefox fallback successful',
                        'source': 'firefox_fallback'
                    }
                else:
                    logger.warning(f"[Firefox {job_id}] No XML content found")
                    return {
                        'success': False,
                        'error': 'XML not found',
                        'message': 'Firefox fallback: XML not available'
                    }
                    
            except TimeoutException:
                logger.error(f"[Firefox {job_id}] Timeout waiting for page elements")
                return {
                    'success': False,
                    'error': 'Page timeout',
                    'message': 'Firefox fallback: Page elements not found'
                }
                
        except Exception as e:
            logger.error(f"[Firefox {job_id}] Failed after {time.time():.3f}s: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'message': f'Firefox fallback failed: {str(e)}'
            }
        
        finally:
            self.cleanup()
    
    def test_connection(self):
        """Testar conexão Firefox"""
        try:
            if not self.setup_firefox_driver():
                return {
                    'success': False,
                    'message': 'Firefox WebDriver initialization failed'
                }
            
            self.driver.get(self.base_url)
            
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            return {
                'success': True,
                'message': 'Firefox connection successful'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f'Firefox connection failed: {str(e)}'
            }
        
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Limpar recursos Firefox"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Firefox WebDriver closed successfully")
            except:
                pass
            finally:
                self.driver = None