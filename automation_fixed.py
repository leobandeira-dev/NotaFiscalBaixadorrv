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
from ultra_speed_optimizer import UltraSpeedOptimizer, UltraSpeedMonitor

logger = logging.getLogger(__name__)

class InvoiceDownloader:
    def __init__(self):
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome WebDriver with deploy-specific robot fixes"""
        try:
            from deploy_robot_fix import DeployRobotFix
            
            # Apply deploy-specific fixes
            DeployRobotFix.apply_deploy_fixes()
            
            # Check environment and use appropriate driver
            if DeployRobotFix.is_deploy_environment():
                logger.info("🔧 DEPLOY ENVIRONMENT - Creating deploy-specific robot")
                self.driver = DeployRobotFix.create_deploy_driver()
            else:
                logger.info("🚀 DEVELOPMENT ENVIRONMENT - Using ultra performance")
                from ultra_performance_deploy import UltraPerformanceDeploy, ChromeDriverManager
                performance_result = UltraPerformanceDeploy.apply_ultra_performance()
                self.driver = ChromeDriverManager.get_optimized_driver()
            
            if self.driver:
                logger.info("✅ Chrome driver created successfully")
                return True
            else:
                logger.error("❌ Failed to create Chrome driver")
                return False
            
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
    
    @UltraSpeedMonitor.measure_ultra_speed
    def download_invoice_xml(self, invoice_key: str, job_id: str, download_type: str = 'xml', user_id: int = None) -> Dict[str, Any]:
        """Download XML for a specific invoice key with ULTRA-SPEED optimizations"""
        try:
            # Apply production-specific fixes
            from production_fix import ProductionFix
            
            # Detect production environment with comprehensive checks
            is_production = ProductionFix.is_production_environment()
            ProductionFix.apply_production_fixes()
            
            # Use environment-appropriate timeouts
            from deploy_robot_fix import DeployRobotFix
            if DeployRobotFix.is_deploy_environment():
                timeouts = DeployRobotFix.get_deploy_timeouts()
                logger.info(f"🔧 [Job {job_id}] Deploy timeouts: {timeouts}")
            else:
                from ultra_performance_deploy import UltraPerformanceDeploy
                timeouts = UltraPerformanceDeploy.get_ultra_timeouts()
                logger.info(f"⚡ [Job {job_id}] Ultra timeouts: {timeouts}")
            
            logger.info(f"🚀 [Job {job_id}] ULTRA-SPEED XML download starting: {invoice_key}")
            
            # Navigate to the website
            url = "https://meudanfe.com.br/"
            logger.info(f"[Job {job_id}] Navigating to invoice system...")
            self.driver.get(url)
            
            # ULTRA-SPEED waits with minimal timeouts
            logger.info(f"⚡ [Job {job_id}] Domain-aware input search...")
            input_element = WebDriverWait(self.driver, timeouts['element_wait']).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[placeholder="Digite a CHAVE DE ACESSO"]'))
            )
            logger.info(f"⚡ [Job {job_id}] Page ready - URL: {self.driver.current_url}")
            
            logger.info(f"⚡ [Job {job_id}] Domain-aware key entry...")
            input_element.clear()
            input_element.send_keys(invoice_key)
            
            # Domain-aware submit button with extended timeout for custom domain
            logger.info(f"⚡ [Job {job_id}] Domain-aware submit search...")
            try:
                submit_button = WebDriverWait(self.driver, timeouts['element_wait']).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'buscar')]"))
                )
            except Exception as e:
                logger.error(f"[Job {job_id}] Submit button not found with timeout {timeouts['element_wait']}s: {e}")
                raise Exception(f"Submit button not found (timeout: {timeouts['element_wait']}s)")
            
            logger.info(f"⚡ [Job {job_id}] Ultra-fast submit click...")
            submit_button.click()
            
            # ULTRA-SPEED results wait (reduced from default)
            logger.info(f"⚡ [Job {job_id}] Ultra-fast response wait...")
            time.sleep(0.3)  # Drastically reduced from previous timeouts
            
            logger.info(f"⚡ [Job {job_id}] Submit complete - URL: {self.driver.current_url}")
            
            # ULTRA-SPEED XML button detection
            logger.info(f"⚡ [Job {job_id}] Domain-aware XML button search (timeout: {timeouts['xml_button']}s)...")
            try:
                xml_button = WebDriverWait(self.driver, timeouts['xml_button']).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'xml') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'baixar')]"))
                )
            except Exception as e:
                logger.error(f"[Job {job_id}] XML button search failed after {timeouts['xml_button']}s: {e}")
                raise Exception(f"XML download button not found (timeout: {timeouts['xml_button']}s)")
            
            logger.info(f"[Job {job_id}] Found XML button, clicking...")
            
            # Get the href or onclick attribute before clicking
            xml_url = xml_button.get_attribute('href')
            onclick = xml_button.get_attribute('onclick')
            
            logger.info(f"[Job {job_id}] XML button href: {xml_url}")
            logger.info(f"[Job {job_id}] XML button onclick: {onclick}")
            
            # ULTRA-SPEED: Use JavaScript click to avoid visual interference
            try:
                self.driver.execute_script("arguments[0].click();", xml_button)
                logger.info(f"⚡ [Job {job_id}] JavaScript click executed")
            except:
                # Fallback to regular click
                xml_button.click()
                logger.info(f"⚡ [Job {job_id}] Regular click executed")
            
            logger.info(f"[Job {job_id}] XML button clicked, starting comprehensive capture...")
            
            # Strategy 1: Direct URL download if href is available
            if xml_url and xml_url.startswith('http') and '.xml' in xml_url:
                logger.info(f"[Job {job_id}] Strategy 1: Direct URL download from {xml_url}")
                result = self.download_file_direct(xml_url, invoice_key, job_id)
                if result['success']:
                    return result
            
            # Strategy 2: Environment-aware polling for browser downloads
            logger.info(f"⚡ [Job {job_id}] Environment-aware polling initiated...")
            logger.info(f"🔧 [Job {job_id}] Using timeouts - max_attempts: {timeouts['max_attempts']}, poll_interval: {timeouts['download_poll']}s")
            
            # Environment-aware polling with appropriate intervals
            for attempt in range(timeouts['max_attempts']):
                time.sleep(timeouts['download_poll'])
                download_result = self.check_downloaded_file(invoice_key, job_id)
                if download_result['success']:
                    total_time = attempt * timeouts['download_poll']
                    logger.info(f"🚀 [Job {job_id}] SUCCESS - file captured in {total_time:.1f}s (attempt {attempt+1}/{timeouts['max_attempts']})")
                    
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
            logger.error(f"[Job {job_id}] Error downloading XML: {str(e)}")
            return {
                'success': False,
                'error': f'Erro no download: {str(e)}'
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