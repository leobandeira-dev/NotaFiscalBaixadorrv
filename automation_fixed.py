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

logger = logging.getLogger(__name__)

class InvoiceDownloader:
    def __init__(self):
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        try:
            logger.info("Setting up Chrome WebDriver...")
            
            # Setup downloads directory
            downloads_dir = os.path.abspath('downloads')
            os.makedirs(downloads_dir, exist_ok=True)
            logger.info(f"Setting download directory to: {downloads_dir}")
            
            # Chrome options optimized for speed
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1280,720')  # Smaller window for speed
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-background-networking')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-client-side-phishing-detection')
            chrome_options.add_argument('--disable-component-extensions-with-background-pages')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-ipc-flooding-protection')
            chrome_options.add_argument('--disable-sync')
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--no-default-browser-check')
            chrome_options.add_argument('--disable-hang-monitor')
            chrome_options.add_argument('--disable-prompt-on-repost')
            chrome_options.add_argument('--disable-domain-reliability')
            chrome_options.add_argument('--disable-features=TranslateUI,BlinkGenPropertyTrees')
            chrome_options.add_argument('--aggressive-cache-discard')
            chrome_options.add_argument('--enable-features=NetworkService,NetworkServiceLogging')
            
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
    
    def download_invoice_xml(self, invoice_key: str, job_id: str, download_type: str = 'xml') -> Dict[str, Any]:
        """Download XML for a specific invoice key with robust capture strategies"""
        try:
            logger.info(f"[Job {job_id}] Starting XML download for invoice key: {invoice_key}")
            
            # Navigate to the website
            url = "https://meudanfe.com.br/"
            logger.info(f"[Job {job_id}] Navigating to invoice system...")
            self.driver.get(url)
            
            # Wait for input field directly (faster than waiting for body)
            logger.info(f"[Job {job_id}] Looking for input field...")
            input_element = WebDriverWait(self.driver, 15).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[placeholder="Digite a CHAVE DE ACESSO"]'))
            )
            logger.info(f"[Job {job_id}] Page loaded - URL: {self.driver.current_url}")
            
            logger.info(f"[Job {job_id}] Entering invoice key...")
            input_element.clear()
            input_element.send_keys(invoice_key)
            
            # Find and click submit button with faster targeting
            logger.info(f"[Job {job_id}] Looking for submit button...")
            try:
                submit_button = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'buscar')]"))
                )
            except:
                raise Exception("Submit button not found")
            
            logger.info(f"[Job {job_id}] Clicking submit button...")
            submit_button.click()
            
            # Wait for results page with intelligent waiting
            logger.info(f"[Job {job_id}] Waiting for response page...")
            time.sleep(3)  # Much faster initial wait
            
            logger.info(f"[Job {job_id}] After submit - URL: {self.driver.current_url}")
            
            # Find XML download button with optimized xpath
            logger.info(f"[Job {job_id}] Looking for XML download button...")
            try:
                # Use single xpath query for faster element location
                xml_button = WebDriverWait(self.driver, 6).until(
                    EC.element_to_be_clickable((By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'xml') and contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'baixar')]"))
                )
            except:
                raise Exception("XML download button not found")
            
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
            
            # Strategy 2: Optimized polling for browser downloads
            logger.info(f"[Job {job_id}] Strategy 2: Checking for browser downloads...")
            
            # Fast polling: check every 1.5 seconds for up to 10 seconds
            for attempt in range(7):
                time.sleep(1.5)
                download_result = self.check_downloaded_file(invoice_key, job_id)
                if download_result['success']:
                    logger.info(f"[Job {job_id}] Strategy 2 SUCCESS - file downloaded and found")
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
        """Download file directly from URL"""
        try:
            logger.info(f"[Job {job_id}] Downloading directly from: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            filename = f"{invoice_key}.xml"
            file_path = os.path.join('downloads', filename)
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"[Job {job_id}] File downloaded: {file_path}")
            
            return {
                'success': True,
                'file_path': file_path
            }
            
        except Exception as e:
            logger.error(f"[Job {job_id}] Direct download failed: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def check_downloaded_file(self, invoice_key: str, job_id: str) -> Dict[str, Any]:
        """Check if file was downloaded to downloads directory"""
        try:
            downloads_dir = 'downloads'
            
            # Check for various filename patterns
            possible_files = [
                f"{invoice_key}.xml",
                f"{invoice_key[:8]}.xml",
                "download.xml",
                "nfe.xml"
            ]
            
            for filename in possible_files:
                file_path = os.path.join(downloads_dir, filename)
                if os.path.exists(file_path):
                    # Rename to proper filename if needed
                    proper_filename = f"{invoice_key}.xml"
                    proper_path = os.path.join(downloads_dir, proper_filename)
                    
                    if file_path != proper_path:
                        os.rename(file_path, proper_path)
                        file_path = proper_path
                    
                    logger.info(f"[Job {job_id}] Found downloaded file: {file_path}")
                    
                    return {
                        'success': True,
                        'file_path': file_path
                    }
            
            # Check all XML files in downloads directory
            for filename in os.listdir(downloads_dir):
                if filename.endswith('.xml'):
                    file_path = os.path.join(downloads_dir, filename)
                    proper_filename = f"{invoice_key}.xml"
                    proper_path = os.path.join(downloads_dir, proper_filename)
                    
                    os.rename(file_path, proper_path)
                    logger.info(f"[Job {job_id}] Found and renamed XML file: {proper_path}")
                    
                    return {
                        'success': True,
                        'file_path': proper_path
                    }
            
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
        """Save XML content to file and database"""
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
                    from xml_processor import save_xml_to_database
                    xml_id = save_xml_to_database(
                        user_id=user_id,
                        invoice_key=invoice_key,
                        xml_content=xml_content,
                        file_path=file_path,
                        import_type=import_type,
                        job_id=job_id
                    )
                    logger.info(f"[Job {job_id}] XML saved to database with ID: {xml_id}")
                except Exception as e:
                    logger.error(f"[Job {job_id}] Error saving to database: {e}")
            
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