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
from models import XMLFile
from app import db
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
            self.performance.apply_chrome_optimizations(options)
            
            # Configurações específicas para fallback
            options.add_argument("--window-size=800,600")
            options.add_argument("--disable-blink-features=AutomationControlled")
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
            
            if chromedriver_path:
                logger.info(f"Using chromedriver at: {chromedriver_path}")
                self.driver = webdriver.Chrome(executable_path=chromedriver_path, options=options)
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
            
            # Aguardar resultado aparecer
            logger.info(f"[Fallback {job_id}] Waiting for results...")
            time.sleep(3)
            
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
    
    def save_xml_content(self, xml_content: str, invoice_key: str, job_id: str, user_id: int, import_type: str = 'FALLBACK') -> dict:
        """Salvar XML no banco de dados"""
        try:
            from app import app
            
            with app.app_context():
                # Processar XML para extrair dados
                xml_data = extract_xml_data(xml_content)
                
                # Verificar se XML já existe
                existing_xml = XMLFile.query.filter_by(
                    user_id=user_id,
                    chave_nf=invoice_key
                ).first()
                
                if existing_xml:
                    logger.info(f"[Fallback {job_id}] XML already exists for user {user_id}")
                    return {
                        'success': True,
                        'message': 'XML já existe no sistema',
                        'xml_data': xml_data,
                        'duplicate': True
                    }
                
                # Consumir crédito do usuário
                # if not consume_xml_credit_fixed(user_id):
                #     return {'success': False, 'error': 'Créditos insuficientes'}
                
                # Criar novo registro XMLFile
                xml_file = XMLFile(
                    user_id=user_id,
                    filename=f"{invoice_key}.xml",
                    chave_nf=invoice_key,
                    xml_content=xml_content,
                    import_type=import_type,
                    numero_nf=xml_data.get('numero_nf'),
                    serie_nf=xml_data.get('serie_nf'),
                    data_emissao=xml_data.get('data_emissao'),
                    valor_total=xml_data.get('valor_total'),
                    peso_bruto=xml_data.get('peso_bruto'),
                    quantidade_volumes=xml_data.get('quantidade_volumes'),
                    nome_emitente=xml_data.get('nome_emitente'),
                    cnpj_emitente=xml_data.get('cnpj_emitente'),
                    cidade_emitente=xml_data.get('cidade_emitente'),
                    uf_emitente=xml_data.get('uf_emitente'),
                    endereco_emitente=xml_data.get('endereco_emitente'),
                    cep_emitente=xml_data.get('cep_emitente'),
                    nome_destinatario=xml_data.get('nome_destinatario'),
                    destinatario_cnpj_cpf=xml_data.get('destinatario_cnpj_cpf'),
                    cidade_destinatario=xml_data.get('cidade_destinatario'),
                    uf_destinatario=xml_data.get('uf_destinatario'),
                    endereco_destinatario=xml_data.get('endereco_destinatario'),
                    cep_destinatario=xml_data.get('cep_destinatario')
                )
                
                db.session.add(xml_file)
                db.session.commit()
                
                logger.info(f"[Fallback {job_id}] XML saved successfully for user {user_id}")
                
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
    
    def cleanup(self):
        """Limpar recursos"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Fallback WebDriver closed successfully")
            except:
                pass
            self.driver = None