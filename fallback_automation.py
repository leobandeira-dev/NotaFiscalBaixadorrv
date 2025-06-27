#!/usr/bin/env python3
"""
Sistema de fallback usando consultadanfe.com.br
Alternativa confiável quando o site principal falha
"""

import os
import time
import logging
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from xml_processor import extract_xml_data
# from simple_credit_system import consume_xml_credit_fixed
# from models import XMLFile
# from app import db
from performance_solution import PerformanceSolution

logger = logging.getLogger(__name__)

class FallbackDownloader:
    """Sistema de fallback usando consultadanfe.com.br"""
    
    def __init__(self):
        self.driver = None
        self.performance = PerformanceSolution()
        self.base_url = "https://consultadanfe.com.br/"
        
    def setup_driver(self):
        """Setup Chrome WebDriver otimizado para fallback"""
        try:
            options = Options()
            
            # Aplicar otimizações de performance
            self.performance.apply_deploy_performance_fixes()
            
            # Configurações específicas para fallback
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=400,300")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--disable-extensions")
            options.add_argument("--disable-default-apps")
            options.add_argument("--single-process")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            # Configurar diretório de downloads
            download_dir = os.path.abspath("downloads")
            os.makedirs(download_dir, exist_ok=True)
            
            prefs = {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            options.add_experimental_option("prefs", prefs)
            
            # Tentar encontrar chromedriver
            chromedriver_path = None
            possible_paths = [
                "/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver",
                "/usr/bin/chromedriver",
                "/usr/local/bin/chromedriver"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    chromedriver_path = path
                    break
            
            # Selenium 4 não usa mais executable_path
            from selenium.webdriver.chrome.service import Service
            
            if chromedriver_path:
                logger.info(f"Using chromedriver at: {chromedriver_path}")
                service = Service(executable_path=chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=options)
            else:
                logger.info("Using system chromedriver")
                self.driver = webdriver.Chrome(options=options)
            
            # Configurações adicionais
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.implicitly_wait(3)
            
            logger.info("Fallback Chrome WebDriver initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup fallback driver: {e}")
            return False
    
    def download_xml_fallback(self, invoice_key: str, job_id: str, user_id: int = None) -> dict:
        """Download XML usando site de fallback"""
        start_time = time.time()
        
        try:
            logger.info(f"[Fallback {job_id}] Starting XML download for invoice key: {invoice_key}")
            
            if not self.setup_driver():
                return {'success': False, 'error': 'Failed to setup fallback driver'}
            
            # Navegar para o site de fallback
            logger.info(f"[Fallback {job_id}] Navigating to fallback site...")
            self.driver.get(self.base_url)
            
            # Aguardar página carregar
            wait = WebDriverWait(self.driver, 8)
            
            # Procurar campo de entrada da chave
            logger.info(f"[Fallback {job_id}] Looking for invoice key input field...")
            
            # Diferentes seletores possíveis para o input
            input_selectors = [
                "input[placeholder*='chave']",
                "input[type='text']",
                "input.form-control",
                "#chave",
                "[name='chave']"
            ]
            
            input_element = None
            for selector in input_selectors:
                try:
                    input_element = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    logger.info(f"[Fallback {job_id}] Found input field with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not input_element:
                return {'success': False, 'error': 'Input field not found on fallback site'}
            
            # Limpar e inserir chave da nota fiscal
            logger.info(f"[Fallback {job_id}] Entering invoice key...")
            input_element.clear()
            input_element.send_keys(invoice_key)
            
            # Procurar botão de buscar
            logger.info(f"[Fallback {job_id}] Looking for search button...")
            
            button_selectors = [
                "button:contains('Buscar')",
                "button:contains('BUSCAR')",
                "input[type='submit']",
                "button[type='submit']",
                ".btn-primary",
                ".btn"
            ]
            
            submit_button = None
            for selector in button_selectors:
                try:
                    if ":contains(" in selector:
                        # Usar XPath para texto
                        text_content = selector.split(':contains(')[1].split(')')[0].strip("'")
                        xpath = f"//button[contains(text(), '{text_content}')] | //input[@value='{text_content}']"
                        submit_button = self.driver.find_element(By.XPATH, xpath)
                    else:
                        submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    logger.info(f"[Fallback {job_id}] Found submit button with selector: {selector}")
                    break
                except:
                    continue
            
            if not submit_button:
                return {'success': False, 'error': 'Submit button not found on fallback site'}
            
            # Clicar no botão de buscar
            logger.info(f"[Fallback {job_id}] Clicking search button...")
            submit_button.click()
            
            # Aguardar e verificar se apareceu CAPTCHA
            logger.info(f"[Fallback {job_id}] Waiting for results...")
            time.sleep(3)
            
            # Detectar e contornar CAPTCHA se presente
            captcha_handled = self.detect_and_handle_captcha(job_id)
            if captcha_handled:
                logger.info(f"[Fallback {job_id}] CAPTCHA detectado e contornado")
                # Reenviar formulário após contornar CAPTCHA
                return self.retry_form_submission(invoice_key, job_id, user_id)
            elif captcha_handled is None:  # CAPTCHA detectado mas não contornado
                logger.warning(f"[Fallback {job_id}] CAPTCHA não pôde ser contornado - tentando site alternativo")
                return self.try_alternative_fallback(invoice_key, job_id, user_id)
            
            # Procurar botão de download XML
            logger.info(f"[Fallback {job_id}] Looking for XML download button...")
            
            download_selectors = [
                "button:contains('DOWNLOAD ARQUIVO XML')",
                "button:contains('XML')",
                "a:contains('XML')",
                ".btn:contains('XML')",
                "[href*='xml']",
                "[onclick*='xml']"
            ]
            
            download_button = None
            for selector in download_selectors:
                try:
                    if ":contains(" in selector:
                        text = selector.split(':contains(')[1].split(')')[0].strip("'")
                        xpath = f"//button[contains(text(), '{text}')] | //a[contains(text(), '{text}')]"
                        download_button = self.driver.find_element(By.XPATH, xpath)
                    else:
                        download_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                    logger.info(f"[Fallback {job_id}] Found download button with selector: {selector}")
                    break
                except:
                    continue
            
            if not download_button:
                # Tentar extrair XML da própria página
                return self.extract_xml_from_page(job_id, invoice_key, user_id)
            
            # Clicar no botão de download
            logger.info(f"[Fallback {job_id}] Clicking download button...")
            download_button.click()
            
            # Aguardar download
            time.sleep(2)
            
            # Verificar se arquivo foi baixado
            result = self.check_downloaded_file(invoice_key, job_id)
            if result['success']:
                # Processar XML e salvar no banco
                if user_id:
                    return self.save_xml_content(result['xml_content'], invoice_key, job_id, user_id)
                return result
            else:
                # Tentar extrair da página como fallback
                return self.extract_xml_from_page(job_id, invoice_key, user_id)
                
        except Exception as e:
            logger.error(f"[Fallback {job_id}] Error in fallback download: {e}")
            return {'success': False, 'error': f'Fallback download failed: {str(e)}'}
        
        finally:
            elapsed = time.time() - start_time
            logger.info(f"📊 FALLBACK PERFORMANCE: {elapsed:.3f}s")
            self.cleanup()
    
    def extract_xml_from_page(self, job_id: str, invoice_key: str, user_id: int = None) -> dict:
        """Extrair XML diretamente do código da página"""
        try:
            logger.info(f"[Fallback {job_id}] Attempting to extract XML from page source...")
            
            page_source = self.driver.page_source
            
            # Procurar por XML na página
            xml_start_markers = [
                '<?xml version="1.0" encoding="UTF-8"?>',
                '<nfeProc',
                '<NFe',
                '<nfe:NFe'
            ]
            
            xml_content = None
            for marker in xml_start_markers:
                start_pos = page_source.find(marker)
                if start_pos != -1:
                    # Encontrar fim do XML
                    end_markers = ['</nfeProc>', '</NFe>', '</nfe:NFe>']
                    end_pos = -1
                    
                    for end_marker in end_markers:
                        temp_end = page_source.find(end_marker, start_pos)
                        if temp_end != -1:
                            end_pos = temp_end + len(end_marker)
                            break
                    
                    if end_pos != -1:
                        xml_content = page_source[start_pos:end_pos]
                        # Limpar entidades HTML
                        xml_content = xml_content.replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')
                        break
            
            if xml_content and len(xml_content) > 100:  # Validação básica
                logger.info(f"[Fallback {job_id}] XML extracted from page, size: {len(xml_content)} bytes")
                
                if user_id:
                    return self.save_xml_content(xml_content, invoice_key, job_id, user_id, import_type='FALLBACK')
                else:
                    return {
                        'success': True,
                        'xml_content': xml_content,
                        'file_size': len(xml_content),
                        'source': 'fallback_extraction'
                    }
            else:
                return {'success': False, 'error': 'No valid XML content found in page'}
                
        except Exception as e:
            logger.error(f"[Fallback {job_id}] Error extracting XML from page: {e}")
            return {'success': False, 'error': f'XML extraction failed: {str(e)}'}
    
    def check_downloaded_file(self, invoice_key: str, job_id: str) -> dict:
        """Verificar se arquivo foi baixado"""
        try:
            download_dir = os.path.abspath("downloads")
            
            # Aguardar um pouco para download completar
            for i in range(10):
                files = os.listdir(download_dir)
                xml_files = [f for f in files if f.endswith('.xml') and invoice_key[:10] in f]
                
                if xml_files:
                    xml_file = xml_files[0]
                    file_path = os.path.join(download_dir, xml_file)
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        xml_content = f.read()
                    
                    logger.info(f"[Fallback {job_id}] Downloaded file found: {xml_file}, size: {len(xml_content)} bytes")
                    
                    return {
                        'success': True,
                        'xml_content': xml_content,
                        'file_path': file_path,
                        'file_size': len(xml_content)
                    }
                
                time.sleep(0.5)
            
            return {'success': False, 'error': 'Downloaded file not found'}
            
        except Exception as e:
            logger.error(f"[Fallback {job_id}] Error checking downloaded file: {e}")
            return {'success': False, 'error': f'File check failed: {str(e)}'}
    
    def save_xml_content(self, xml_content: str, invoice_key: str, job_id: str, user_id: int = None, import_type: str = 'FALLBACK') -> dict:
        """Salvar XML (versão simplificada para testes)"""
        try:
            # Para testes básicos, salvar apenas em arquivo local
            os.makedirs('downloads', exist_ok=True)
            filename = f"downloads/{invoice_key}.xml"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            logger.info(f"[Fallback {job_id}] XML saved to file: {filename}")
            
            # Processar XML para extrair dados básicos
            try:
                xml_data = extract_xml_data(xml_content)
            except Exception as e:
                logger.warning(f"[Fallback {job_id}] Could not extract XML data: {e}")
                xml_data = {}
            
            return {
                'success': True,
                'message': 'XML baixado e processado com sucesso via fallback',
                'xml_data': xml_data,
                'file_size': len(xml_content),
                'source': 'fallback'
            }
                
        except Exception as e:
            logger.error(f"[Fallback {job_id}] Error saving XML: {e}")
            return {'success': False, 'error': f'Failed to save XML: {str(e)}'}
    
    def test_fallback_connection(self) -> dict:
        """Testar conectividade do site de fallback"""
        try:
            logger.info("Testing fallback site connectivity...")
            
            if not self.setup_driver():
                return {'success': False, 'error': 'Failed to setup driver'}
            
            self.driver.get(self.base_url)
            
            # Verificar se página carregou
            if "consultadanfe" in self.driver.current_url.lower():
                logger.info("Fallback site connection successful")
                return {
                    'success': True,
                    'message': 'Fallback site is accessible',
                    'url': self.driver.current_url
                }
            else:
                return {'success': False, 'error': 'Fallback site not accessible'}
                
        except Exception as e:
            logger.error(f"Fallback connection test failed: {e}")
            return {'success': False, 'error': f'Connection test failed: {str(e)}'}
        finally:
            self.cleanup()
    
    def detect_and_handle_captcha(self, job_id):
        """Detectar e contornar CAPTCHA se presente"""
        try:
            # Detectar elementos comuns de CAPTCHA
            captcha_indicators = [
                "//iframe[contains(@src, 'recaptcha')]",
                "//div[contains(@class, 'recaptcha')]", 
                "//*[contains(text(), 'motocicleta')]",
                "//*[contains(text(), 'motorcycle')]",
                "//*[contains(text(), 'Selecione')]",
                "//*[contains(text(), 'Select')]",
                "//div[contains(@class, 'captcha')]",
                "//img[contains(@alt, 'captcha')]"
            ]
            
            captcha_found = False
            for indicator in captcha_indicators:
                try:
                    element = self.driver.find_element(By.XPATH, indicator)
                    if element.is_displayed():
                        captcha_found = True
                        logger.warning(f"[Fallback {job_id}] CAPTCHA detectado: {indicator}")
                        break
                except:
                    continue
            
            if not captcha_found:
                return False
                
            # Tentar estratégias de contorno do CAPTCHA
            logger.info(f"[Fallback {job_id}] Tentando contornar CAPTCHA...")
            
            # Estratégia 1: Aguardar e tentar novamente
            time.sleep(2)
            
            # Estratégia 2: Simular comportamento humano com movimentos de mouse
            try:
                from selenium.webdriver.common.action_chains import ActionChains
                actions = ActionChains(self.driver)
                # Mover mouse para simular comportamento humano
                actions.move_by_offset(100, 100).perform()
                time.sleep(1)
                actions.move_by_offset(-50, -50).perform()
                time.sleep(1)
            except:
                pass
            
            # Estratégia 3: Recarregar a página e tentar novamente
            logger.info(f"[Fallback {job_id}] Recarregando página para contornar CAPTCHA...")
            self.driver.refresh()
            time.sleep(3)
            
            # Verificar se CAPTCHA ainda está presente
            captcha_still_present = False
            for indicator in captcha_indicators:
                try:
                    element = self.driver.find_element(By.XPATH, indicator)
                    if element.is_displayed():
                        captcha_still_present = True
                        break
                except:
                    continue
            
            if not captcha_still_present:
                logger.info(f"[Fallback {job_id}] CAPTCHA contornado com sucesso!")
                return True
            else:
                logger.warning(f"[Fallback {job_id}] CAPTCHA ainda presente após tentativas")
                return None  # Indica que CAPTCHA foi detectado mas não contornado
                
        except Exception as e:
            logger.error(f"[Fallback {job_id}] Erro ao tentar contornar CAPTCHA: {e}")
            return False

    def retry_form_submission(self, invoice_key: str, job_id: str, user_id: int = None) -> dict:
        """Reenviar formulário após contornar CAPTCHA"""
        try:
            logger.info(f"[Fallback {job_id}] Reenviando formulário após contornar CAPTCHA...")
            
            # Navegar para a página inicial novamente
            self.driver.get("https://consultadanfe.com.br/")
            time.sleep(2)
            
            # Preencher campo de chave novamente
            input_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='text'], input[name*='chave'], input[id*='chave']")
            input_field.clear()
            input_field.send_keys(invoice_key)
            
            # Clicar no botão de buscar
            submit_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            submit_button.click()
            
            time.sleep(3)
            
            # Proceder com download normal
            return self.extract_xml_from_page(job_id, invoice_key, user_id)
            
        except Exception as e:
            logger.error(f"[Fallback {job_id}] Erro ao reenviar formulário: {e}")
            return {'success': False, 'error': f'Erro ao reenviar formulário: {str(e)}'}

    def try_alternative_fallback(self, invoice_key: str, job_id: str, user_id: int = None) -> dict:
        """Tentar site alternativo quando CAPTCHA não pode ser contornado"""
        try:
            logger.info(f"[Fallback {job_id}] Tentando site alternativo...")
            
            # Lista de sites alternativos (apenas para demonstração - em produção, usar sites reais)
            alternative_sites = [
                "https://nfe.fazenda.gov.br/portal/consultaCompleta.aspx",
                # Adicionar outros sites alternativos aqui conforme necessário
            ]
            
            for site in alternative_sites:
                try:
                    logger.info(f"[Fallback {job_id}] Tentando site: {site}")
                    self.driver.get(site)
                    time.sleep(3)
                    
                    # Verificar se site está acessível
                    if "nfe.fazenda.gov.br" in self.driver.current_url:
                        # Site oficial da SEFAZ - retornar erro informativo
                        return {
                            'success': False, 
                            'error': 'Site de fallback bloqueado por CAPTCHA. Tente novamente em alguns minutos.'
                        }
                    
                except Exception as e:
                    logger.warning(f"[Fallback {job_id}] Site alternativo falhou: {e}")
                    continue
            
            return {
                'success': False, 
                'error': 'Todos os sites de fallback indisponíveis. Sistema principal será usado automaticamente.'
            }
            
        except Exception as e:
            logger.error(f"[Fallback {job_id}] Erro ao tentar sites alternativos: {e}")
            return {'success': False, 'error': f'Erro em sites alternativos: {str(e)}'}

    def cleanup(self):
        """Limpar recursos"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Fallback WebDriver closed successfully")
            except:
                pass
            self.driver = None