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
from typing import Dict, Any
import re
from optimization_deploy import DeployOptimizer
from performance_solution import PerformanceSolution, EnhancedDeployOptimizer, DeployPerformanceMonitor
from automation_connection_fix import ChromeConnectionFix

logger = logging.getLogger(__name__)

class InvoiceDownloader:
    def __init__(self):
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome WebDriver with enhanced environment-optimized options"""
        try:
            # Apply comprehensive performance fixes for deploy environment
            performance_result = PerformanceSolution.apply_deploy_performance_fixes()
            logger.info(f"Performance optimizations applied: {performance_result['environment']}")
            
            # Setup downloads directory
            downloads_dir = os.path.abspath('downloads')
            os.makedirs(downloads_dir, exist_ok=True)
            logger.info(f"Setting download directory to: {downloads_dir}")
            
            # Get enhanced Chrome options with deploy-specific optimizations
            chrome_options = EnhancedDeployOptimizer.get_enhanced_chrome_options()
            
            # Additional specific optimizations
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')
            
            # Download preferences
            prefs = {
                "download.default_directory": downloads_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Try to find chromedriver
            chromedriver_path = None
            possible_paths = [
                '/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver',
                '/usr/bin/chromedriver',
                '/usr/local/bin/chromedriver'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    chromedriver_path = path
                    logger.info(f"Found chromedriver at: {chromedriver_path}")
                    break
            
            if chromedriver_path:
                logger.info(f"Attempting to use chromedriver at: {chromedriver_path}")
                from selenium.webdriver.chrome.service import Service
                service = Service(chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                logger.info("Using system chromedriver")
                self.driver = webdriver.Chrome(options=chrome_options)
            
            logger.info("Chrome WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup Chrome WebDriver: {str(e)}")
            raise
    
    @DeployPerformanceMonitor.measure_operation("xml_download")
    def download_invoice_xml(self, invoice_key: str, job_id: str, download_type: str = 'xml', user_id: int = None) -> Dict[str, Any]:
        """Download XML for a specific invoice key with enhanced environment-optimized timeouts"""
        try:
            # Get enhanced optimized timeouts for current environment
            timeouts = EnhancedDeployOptimizer.get_enhanced_timeouts()
            
            logger.info(f"[Job {job_id}] Starting XML download for invoice key: {invoice_key}")
            
            # Navigate to the website with new layout
            url = "https://meudanfe.com.br/"
            logger.info(f"[Job {job_id}] Navigating to updated invoice system...")
            self.driver.get(url)
            
            # Wait for page to fully load in new layout
            logger.info(f"[Job {job_id}] Waiting for page to fully load...")
            time.sleep(3)
            
            # Environment-optimized waits for new layout
            logger.info(f"[Job {job_id}] Looking for input field in new layout...")
            input_element = None
            
            # Try to wait for page to be interactive
            try:
                WebDriverWait(self.driver, 10).until(
                    lambda driver: driver.execute_script("return document.readyState") == "complete"
                )
                logger.info(f"[Job {job_id}] Page fully loaded")
            except:
                logger.info(f"[Job {job_id}] Page load timeout, proceeding anyway")
            
            # Try different strategies to find and interact with input field - Updated from website mapping
            selectors = [
                (By.ID, 'searchTxt'),  # Confirmed working selector from website mapping
                (By.NAME, 'searchTxt'),  # Backup name selector
                (By.CSS_SELECTOR, 'input[id="searchTxt"]'),  # CSS ID selector
                (By.XPATH, "//input[@id='searchTxt']"),  # XPath ID selector
                (By.CSS_SELECTOR, 'input[placeholder*="Chave"]'),  # Placeholder fallback
                (By.CSS_SELECTOR, 'input[type="text"]')  # Type fallback
            ]
            
            for i, selector in enumerate(selectors):
                try:
                    logger.info(f"[Job {job_id}] Trying input selector {i+1}: {selector}")
                    
                    # First find the element
                    element = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located(selector)
                    )
                    
                    # Then wait for it to be clickable
                    input_element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable(selector)
                    )
                    
                    logger.info(f"[Job {job_id}] Found interactive input field with selector {i+1}")
                    break
                except Exception as e:
                    logger.info(f"[Job {job_id}] Input selector {i+1} failed: {str(e)[:100]}")
                    continue
            
            if not input_element:
                raise Exception("Input field not found or not interactive in new layout")
            
            logger.info(f"[Job {job_id}] Page loaded - URL: {self.driver.current_url}")
            
            # Try multiple strategies to enter the invoice key
            logger.info(f"[Job {job_id}] Entering invoice key in new layout...")
            try:
                # Clear any existing content
                input_element.clear()
                time.sleep(0.5)
                
                # Enter the invoice key
                input_element.send_keys(invoice_key)
                time.sleep(1)
                
                # Verify the content was entered
                value = input_element.get_attribute('value')
                if value != invoice_key:
                    logger.warning(f"[Job {job_id}] Input value doesn't match: got '{value}', expected '{invoice_key}'")
                    # Try again with JavaScript
                    self.driver.execute_script(f"arguments[0].value = '{invoice_key}';", input_element)
                    
                logger.info(f"[Job {job_id}] Invoice key entered successfully")
                
            except Exception as e:
                logger.error(f"[Job {job_id}] Error entering invoice key: {e}")
                # Fallback: try with JavaScript
                try:
                    self.driver.execute_script(f"arguments[0].value = '{invoice_key}';", input_element)
                    logger.info(f"[Job {job_id}] Invoice key entered via JavaScript")
                except Exception as js_error:
                    raise Exception(f"Failed to enter invoice key: {e}, JavaScript fallback also failed: {js_error}")
            
            # Environment-optimized submit button wait for new green BUSCAR button (it's an <a> tag now)
            logger.info(f"[Job {job_id}] Looking for new green BUSCAR button...")
            submit_button = None
            for i, selector in enumerate([
                (By.ID, 'searchBtn'),  # Primary search button - it's a link now
                (By.XPATH, "//a[contains(text(), 'BUSCAR')]"),
                (By.XPATH, "//a[@id='searchBtn']"),
                (By.CSS_SELECTOR, "a[id='searchBtn']"),
                (By.XPATH, "//*[contains(text(), 'BUSCAR')]"),
                (By.XPATH, "//button[contains(text(), 'BUSCAR')]"),
                (By.CSS_SELECTOR, "a[href='#']")
            ], 1):
                try:
                    logger.info(f"[Job {job_id}] Trying submit selector {i}: {selector}")
                    submit_button = WebDriverWait(self.driver, timeouts['element_wait']).until(
                        EC.element_to_be_clickable(selector)
                    )
                    logger.info(f"[Job {job_id}] Found submit button with selector {i}")
                    break
                except Exception as e:
                    logger.info(f"[Job {job_id}] Submit selector {i} failed: {str(e)[:100]}")
                    continue
            
            if not submit_button:
                raise Exception("BUSCAR button not found in new layout")
            
            logger.info(f"[Job {job_id}] Clicking submit button...")
            # Try multiple click strategies to prevent disconnection
            try:
                # First try regular click
                submit_button.click()
            except Exception as click_error:
                logger.info(f"[Job {job_id}] Regular click failed, trying JavaScript: {click_error}")
                try:
                    # Fallback to JavaScript click if regular click fails
                    self.driver.execute_script("arguments[0].click();", submit_button)
                except Exception as js_error:
                    logger.info(f"[Job {job_id}] JavaScript click failed, trying action chains: {js_error}")
                    # Final fallback with action chains
                    from selenium.webdriver.common.action_chains import ActionChains
                    ActionChains(self.driver).move_to_element(submit_button).click().perform()
            
            # Wait for loading to complete in new layout
            logger.info(f"[Job {job_id}] Waiting for results to load in new layout...")
            time.sleep(timeouts['download_wait'])
            
            # Wait for loading spinner to disappear if present
            try:
                WebDriverWait(self.driver, 5).until_not(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "[class*='loading'], [class*='spinner'], .loading"))
                )
                logger.info(f"[Job {job_id}] Loading completed")
            except:
                logger.info(f"[Job {job_id}] No loading spinner detected, proceeding")
            
            logger.info(f"[Job {job_id}] After submit - URL: {self.driver.current_url}")
            
            # Additional wait to ensure results are fully loaded
            time.sleep(2)
            
            # Find XML download button in new layout (red "Baixar XML" button)
            logger.info(f"[Job {job_id}] Looking for XML download button in new layout...")
            
            # Debug: Print page content to understand new structure
            try:
                page_content = self.driver.page_source
                if "Baixar XML" in page_content:
                    logger.info(f"[Job {job_id}] 'Baixar XML' text found on page")
                else:
                    logger.info(f"[Job {job_id}] 'Baixar XML' text NOT found on page")
                    
                # Check for any XML-related buttons
                if "xml" in page_content.lower():
                    logger.info(f"[Job {job_id}] 'xml' text found on page")
                else:
                    logger.info(f"[Job {job_id}] 'xml' text NOT found on page")
            except Exception as e:
                logger.warning(f"[Job {job_id}] Could not debug page content: {e}")
            
            xml_button = None
            selectors = [
                (By.XPATH, "//button[contains(text(), 'Baixar XML')]"),
                (By.XPATH, "//*[contains(text(), 'Baixar XML')]"),
                (By.XPATH, "//a[contains(text(), 'Baixar XML')]"),
                (By.XPATH, "//button[contains(text(), 'XML')]"),
                (By.XPATH, "//*[contains(text(), 'XML')]"),
                (By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'xml') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'baixar')]"),
                (By.CSS_SELECTOR, "button[onclick*='xml'], a[href*='xml']"),
                (By.CSS_SELECTOR, "button[class*='btn'], a[class*='btn']")
            ]
            
            for i, selector in enumerate(selectors):
                try:
                    logger.info(f"[Job {job_id}] Trying selector {i+1}: {selector}")
                    xml_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable(selector)
                    )
                    logger.info(f"[Job {job_id}] Found XML button with selector {i+1}")
                    break
                except Exception as e:
                    logger.info(f"[Job {job_id}] Selector {i+1} failed: {str(e)[:100]}")
                    continue
            
            if not xml_button:
                raise Exception("Baixar XML button not found in new layout")
            
            logger.info(f"[Job {job_id}] Found XML button, clicking...")
            
            # Get the href or onclick attribute before clicking
            xml_url = xml_button.get_attribute('href')
            onclick = xml_button.get_attribute('onclick')
            
            logger.info(f"[Job {job_id}] XML button href: {xml_url}")
            logger.info(f"[Job {job_id}] XML button onclick: {onclick}")
            
            # Click the XML button
            xml_button.click()
            
            logger.info(f"[Job {job_id}] XML button clicked, starting comprehensive capture...")
            
            # Strategy 1: Direct URL download if href is available
            if xml_url and xml_url.startswith('http') and '.xml' in xml_url:
                logger.info(f"[Job {job_id}] Strategy 1: Direct URL download from {xml_url}")
                result = self.download_file_direct(xml_url, invoice_key, job_id)
                if result['success']:
                    return result
            
            # Strategy 2: Environment-optimized polling for browser downloads
            logger.info(f"[Job {job_id}] Strategy 2: Checking for browser downloads...")
            
            # Environment-optimized polling intervals and attempts
            for attempt in range(timeouts['max_attempts']):
                time.sleep(timeouts['download_poll'])
                download_result = self.check_downloaded_file(invoice_key, job_id)
                if download_result['success']:
                    logger.info(f"[Job {job_id}] Strategy 2 SUCCESS - file downloaded and found")
                    
                    # Process file with user_id for charging and database saving
                    if user_id and 'file_path' in download_result:
                        try:
                            # Read XML content from downloaded file
                            with open(download_result['file_path'], 'r', encoding='utf-8') as f:
                                xml_content = f.read()
                            
                            # Use new download service for charging and database operations
                            from download_service import DownloadService
                            success = DownloadService.process_successful_download(
                                user_id=user_id,
                                invoice_key=invoice_key,
                                xml_content=xml_content,
                                file_path=download_result['file_path'],
                                job_id=job_id
                            )
                            
                            if success:
                                logger.info(f"[Job {job_id}] Successfully charged and saved XML for user {user_id}")
                            else:
                                logger.error(f"[Job {job_id}] Failed to charge or save XML for user {user_id}")
                            
                        except Exception as e:
                            logger.error(f"[Job {job_id}] Error processing downloaded file: {e}")
                    
                    return download_result
            
            # Strategy 3: Extract XML from page source
            logger.info(f"[Job {job_id}] Strategy 3: Extracting XML from page source...")
            page_source = self.driver.page_source
            xml_content = self.extract_xml_from_page(page_source)
            if xml_content:
                return self.save_xml_content(xml_content, invoice_key, job_id)
            
            # Strategy 4: Check for new windows/tabs
            logger.info(f"[Job {job_id}] Strategy 4: Checking for new windows...")
            current_window = self.driver.current_window_handle
            all_windows = self.driver.window_handles
            
            if len(all_windows) > 1:
                for window in all_windows:
                    if window != current_window:
                        self.driver.switch_to.window(window)
                        window_url = self.driver.current_url
                        
                        if '.xml' in window_url:
                            logger.info(f"[Job {job_id}] Found XML window: {window_url}")
                            result = self.download_file_direct(window_url, invoice_key, job_id)
                            self.driver.close()
                            self.driver.switch_to.window(current_window)
                            if result['success']:
                                return result
                        
                        # Check window content for XML
                        window_source = self.driver.page_source
                        xml_content = self.extract_xml_from_page(window_source)
                        if xml_content:
                            self.driver.close()
                            self.driver.switch_to.window(current_window)
                            return self.save_xml_content(xml_content, invoice_key, job_id)
                        
                        self.driver.close()
                
                self.driver.switch_to.window(current_window)
            
            # Strategy 5: Wait longer and try again
            logger.info(f"[Job {job_id}] Strategy 5: Waiting longer and rechecking...")
            time.sleep(10)
            download_result = self.check_downloaded_file(invoice_key, job_id)
            if download_result['success']:
                return download_result
            
            logger.warning(f"[Job {job_id}] All capture strategies failed")
            return {
                'success': False,
                'error': 'XML não encontrado após todas as estratégias de captura'
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[Job {job_id}] Error downloading XML: {error_msg}")
            
            # Check if it's a Chrome connection issue
            if ChromeConnectionFix.is_connection_error(error_msg):
                logger.info(f"[Job {job_id}] Chrome connection issue detected")
                return ChromeConnectionFix.create_error_response(job_id, invoice_key, error_msg)
            
            return {
                'success': False,
                'error': f'Erro no download: {error_msg}',
                'error_category': ChromeConnectionFix.get_error_category(error_msg)
            }
    
    def download_file_direct(self, url: str, invoice_key: str, job_id: str) -> Dict[str, Any]:
        """Ultra-fast direct download from URL with optimized settings"""
        try:
            logger.info(f"[Job {job_id}] Ultra-fast download from: {url}")
            
            # Minimal headers for speed
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            
            # Ultra-fast request with minimal timeout
            response = requests.get(url, headers=headers, timeout=4, stream=False)
            response.raise_for_status()
            
            # Direct save without validation for speed
            filename = f"{invoice_key}.xml"
            file_path = os.path.join('downloads', filename)
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"[Job {job_id}] Ultra-fast download complete: {file_path}")
            
            return {
                'success': True,
                'file_path': file_path
            }
            
        except Exception as e:
            logger.error(f"[Job {job_id}] Ultra-fast download failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_downloaded_file(self, invoice_key: str, job_id: str) -> Dict[str, Any]:
        """Ultra-fast file check with minimal operations"""
        try:
            downloads_dir = 'downloads'
            
            # Ultra-fast check: look for exact filename first
            exact_file = os.path.join(downloads_dir, f"{invoice_key}.xml")
            if os.path.exists(exact_file):
                return {
                    'success': True,
                    'file_path': exact_file
                }
            
            # Quick pattern check with minimal list
            quick_patterns = [
                f"{invoice_key[:8]}.xml",
                "download.xml"
            ]
            
            for filename in quick_patterns:
                file_path = os.path.join(downloads_dir, filename)
                if os.path.exists(file_path):
                    # Fast rename without logging
                    proper_path = os.path.join(downloads_dir, f"{invoice_key}.xml")
                    os.rename(file_path, proper_path)
                    
                    return {
                        'success': True,
                        'file_path': proper_path
                    }
            
            # Last resort: check for any XML file
            try:
                for filename in os.listdir(downloads_dir):
                    if filename.endswith('.xml'):
                        file_path = os.path.join(downloads_dir, filename)
                        proper_path = os.path.join(downloads_dir, f"{invoice_key}.xml")
                        os.rename(file_path, proper_path)
                        
                        return {
                            'success': True,
                            'file_path': proper_path
                        }
            except:
                pass
            
            return {
                'success': False,
                'error': 'No downloaded file found'
            }
            
        except Exception as e:
            logger.error(f"[Job {job_id}] Error checking downloads: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def extract_xml_from_page(self, page_source: str) -> str:
        """Extract XML content from page source"""
        try:
            # Multiple patterns to find XML content
            patterns = [
                r'(<\?xml.*?</nfeProc>)',
                r'(<\?xml.*?</NFe>)',
                r'(<nfeProc.*?</nfeProc>)',
                r'(<NFe.*?</NFe>)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, page_source, re.DOTALL | re.IGNORECASE)
                if match:
                    xml_content = match.group(1)
                    if len(xml_content) > 100:  # Basic validation
                        return xml_content
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting XML: {e}")
            return None
    
    def save_xml_content(self, xml_content: str, invoice_key: str, job_id: str, user_id: int = None, import_type: str = 'SISTEMA') -> Dict[str, Any]:
        """Save XML content to file and database with proper Flask context"""
        try:
            filename = f"{invoice_key}.xml"
            file_path = os.path.join('downloads', filename)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            logger.info(f"[Job {job_id}] XML content saved to: {file_path}")
            
            # Salvar no banco de dados se user_id fornecido
            xml_id = None
            if user_id:
                try:
                    # Import Flask app and use application context
                    from new_app import app, db
                    from models import XMLFile, ImportedXML, User, UsageRecord, ServiceModule
                    from datetime import datetime
                    import xml.etree.ElementTree as ET
                    
                    with app.app_context():
                        # Verificar se XML já existe
                        existing = ImportedXML.query.filter_by(
                            user_id=user_id, 
                            invoice_key=invoice_key
                        ).first()
                        
                        if existing:
                            logger.info(f"[Job {job_id}] XML {invoice_key} already exists for user {user_id}")
                            return {
                                'success': True,
                                'file_path': file_path,
                                'xml_id': existing.id,
                                'filename': filename
                            }
                        
                        # Parse XML para extrair dados
                        try:
                            root = ET.fromstring(xml_content)
                            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
                            
                            # Extrair dados básicos
                            emit = root.find('.//nfe:emit', ns)
                            ide = root.find('.//nfe:ide', ns)
                            total = root.find('.//nfe:total/nfe:ICMSTot', ns)
                            
                            cnpj_emitente = emit.find('nfe:CNPJ', ns).text if emit is not None and emit.find('nfe:CNPJ', ns) is not None else ''
                            nome_emitente = emit.find('nfe:xNome', ns).text if emit is not None and emit.find('nfe:xNome', ns) is not None else ''
                            numero_nf = ide.find('nfe:nNF', ns).text if ide is not None and ide.find('nfe:nNF', ns) is not None else ''
                            serie_nf = ide.find('nfe:serie', ns).text if ide is not None and ide.find('nfe:serie', ns) is not None else ''
                            data_emissao_str = ide.find('nfe:dhEmi', ns).text if ide is not None and ide.find('nfe:dhEmi', ns) is not None else ''
                            valor_total = float(total.find('nfe:vNF', ns).text) if total is not None and total.find('nfe:vNF', ns) is not None else 0.0
                            
                            # Parse data
                            data_emissao = None
                            if data_emissao_str:
                                try:
                                    data_emissao = datetime.strptime(data_emissao_str[:10], '%Y-%m-%d').date()
                                except:
                                    pass
                            
                        except Exception as parse_error:
                            logger.warning(f"[Job {job_id}] Error parsing XML data: {parse_error}")
                            cnpj_emitente = nome_emitente = numero_nf = serie_nf = ''
                            data_emissao = None
                            valor_total = 0.0
                        
                        # Criar registro ImportedXML
                        imported_xml = ImportedXML(
                            user_id=user_id,
                            invoice_key=invoice_key,
                            xml_content=xml_content,
                            file_path=file_path,
                            import_type=import_type,
                            job_id=job_id,
                            cnpj_emitente=cnpj_emitente,
                            nome_emitente=nome_emitente,
                            numero_nf=numero_nf,
                            serie_nf=serie_nf,
                            data_emissao=data_emissao,
                            valor_total=valor_total,
                            danfe_generated=False,
                            label_generated=False,
                            imported_at=datetime.utcnow()
                        )
                        
                        db.session.add(imported_xml)
                        db.session.commit()
                        xml_id = imported_xml.id
                        
                        logger.info(f"[Job {job_id}] XML saved to database with ID: {xml_id}")
                        
                        # Charge credits for XML download
                        self.charge_for_download(user_id, invoice_key)
                    
                except Exception as e:
                    logger.error(f"[Job {job_id}] Error saving to database: {e}")
                    import traceback
                    logger.error(f"[Job {job_id}] Traceback: {traceback.format_exc()}")
            
            return {
                'success': True,
                'file_path': file_path,
                'xml_id': xml_id,
                'filename': filename
            }
            
        except Exception as e:
            logger.error(f"[Job {job_id}] Error saving XML: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def charge_for_download(self, user_id: int, invoice_key: str):
        """Charge user credits for XML download using simplified credit system"""
        try:
            from new_app import app, db
            from models import User
            from datetime import datetime
            
            with app.app_context():
                # Get user and check trial status
                user = User.query.get(user_id)
                if not user:
                    logger.error(f"User {user_id} not found for charging")
                    return
                
                # Check if user is in trial period
                is_trial_active = user.trial_expires_at and user.trial_expires_at > datetime.utcnow()
                
                # Only charge if not in trial
                if not is_trial_active:
                    # Use simplified credit system for consistent charging
                    from simple_credit_system import consume_xml_credit, get_user_xml_balance
                    
                    # Check if user has credits
                    available_credits = get_user_xml_balance(user_id)
                    if available_credits < 1:
                        logger.warning(f"Insufficient XML credits for user {user_id} - Available: {available_credits}")
                        return False
                    
                    # Consume XML credit
                    success = consume_xml_credit(
                        user_id=user_id,
                        description=f"Download XML via API: {invoice_key[:10]}..."
                    )
                    
                    if success:
                        logger.info(f"Successfully charged 1 XML credit for API download - User {user_id}")
                        return True
                    else:
                        logger.error(f"Failed to charge XML credit for user {user_id}")
                        return False
                else:
                    logger.info(f"Free XML download for trial user {user_id}")
                    return True
                
        except Exception as e:
            logger.error(f"Error charging for download: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return False
    
    def test_connection(self) -> Dict[str, Any]:
        """Test if the automation system can connect to the invoice system"""
        try:
            logger.info("Testing connection to invoice system...")
            
            url = "https://meudanfe.com.br/"
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Check if input field exists
            input_element = self.driver.find_element(
                By.CSS_SELECTOR, 'input[placeholder="Digite a CHAVE DE ACESSO"]'
            )
            
            if input_element:
                logger.info("Connection test successful - invoice system is accessible")
                return {
                    'success': True,
                    'message': 'Conexão com o sistema de notas fiscais estabelecida com sucesso',
                    'url': self.driver.current_url,
                    'title': self.driver.title
                }
            else:
                return {
                    'success': False,
                    'message': 'Sistema acessível mas interface não reconhecida'
                }
                
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {
                'success': False,
                'message': f'Falha na conexão: {str(e)}'
            }
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {e}")