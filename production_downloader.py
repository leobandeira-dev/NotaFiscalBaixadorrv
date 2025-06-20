"""
Production-ready downloader for deployed environments
Handles Chrome/WebDriver limitations in containerized deployments
"""

import os
import time
import logging
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException

logger = logging.getLogger(__name__)

class ProductionDownloader:
    def __init__(self):
        self.driver = None
        self.max_retries = 3
    
    def setup_driver(self):
        """Setup Chrome WebDriver with production-specific configurations"""
        try:
            logger.info("Setting up production WebDriver...")
            
            # Create downloads directory
            downloads_dir = os.path.abspath('downloads')
            os.makedirs(downloads_dir, exist_ok=True)
            
            # Chrome options for containerized environment
            chrome_options = Options()
            chrome_options.add_argument('--headless=new')  # Use new headless mode
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript')
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
            chrome_options.add_argument('--disable-features=TranslateUI,BlinkGenPropertyTrees,VizDisplayCompositor')
            chrome_options.add_argument('--aggressive-cache-discard')
            chrome_options.add_argument('--memory-pressure-off')
            chrome_options.add_argument('--max_old_space_size=4096')
            
            # Production-specific flags for stability
            chrome_options.add_argument('--single-process')
            chrome_options.add_argument('--disable-setuid-sandbox')
            chrome_options.add_argument('--disable-site-isolation-trials')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Download preferences
            prefs = {
                "download.default_directory": downloads_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False,
                "profile.default_content_settings.popups": 0,
                "profile.default_content_setting_values.automatic_downloads": 1,
                "profile.managed_default_content_settings.images": 2  # Block images
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Try multiple initialization strategies
            strategies = [
                self._try_webdriver_manager,
                self._try_system_chromedriver,
                self._try_nix_chromedriver,
                self._try_manual_paths
            ]
            
            for strategy in strategies:
                try:
                    self.driver = strategy(chrome_options)
                    if self.driver:
                        logger.info(f"✅ WebDriver initialized with {strategy.__name__}")
                        break
                except Exception as e:
                    logger.warning(f"{strategy.__name__} failed: {e}")
                    continue
            
            if not self.driver:
                raise Exception("All WebDriver initialization strategies failed")
            
            # Configure timeouts for production
            self.driver.set_page_load_timeout(60)
            self.driver.implicitly_wait(20)
            
            # Add stealth script to avoid detection
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            logger.info("Production WebDriver setup completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup production WebDriver: {e}")
            return False
    
    def _try_webdriver_manager(self, chrome_options):
        """Try WebDriverManager approach"""
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            return webdriver.Chrome(service=service, options=chrome_options)
        except:
            return None
    
    def _try_system_chromedriver(self, chrome_options):
        """Try system ChromeDriver"""
        try:
            return webdriver.Chrome(options=chrome_options)
        except:
            return None
    
    def _try_nix_chromedriver(self, chrome_options):
        """Try Nix store ChromeDriver paths"""
        try:
            import glob
            nix_paths = glob.glob('/nix/store/*/bin/chromedriver')
            for path in nix_paths:
                if os.path.exists(path):
                    service = Service(path)
                    return webdriver.Chrome(service=service, options=chrome_options)
        except:
            pass
        return None
    
    def _try_manual_paths(self, chrome_options):
        """Try manual ChromeDriver paths"""
        paths = [
            '/usr/bin/chromedriver',
            '/usr/local/bin/chromedriver',
            '/opt/google/chrome/chromedriver'
        ]
        
        for path in paths:
            try:
                if os.path.exists(path):
                    service = Service(path)
                    return webdriver.Chrome(service=service, options=chrome_options)
            except:
                continue
        return None
    
    def download_xml_production(self, invoice_key: str, job_id: str, user_id: int = None):
        """Production-optimized XML download"""
        try:
            logger.info(f"[Job {job_id}] Starting production XML download for: {invoice_key}")
            
            if not self.setup_driver():
                return {"success": False, "error": "Failed to initialize WebDriver"}
            
            # Navigate with retry logic
            for attempt in range(self.max_retries):
                try:
                    logger.info(f"[Job {job_id}] Attempt {attempt + 1}: Navigating to system...")
                    self.driver.get("https://meudanfe.com.br/")
                    
                    # Wait for page load
                    wait = WebDriverWait(self.driver, 30)
                    wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
                    
                    # Look for input field
                    input_selectors = [
                        'input[name="chave"]',
                        'input[type="text"]',
                        '#chave',
                        '.chave-input'
                    ]
                    
                    input_element = None
                    for selector in input_selectors:
                        try:
                            input_element = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                            break
                        except:
                            continue
                    
                    if not input_element:
                        raise Exception("Could not find input field")
                    
                    # Clear and enter invoice key
                    input_element.clear()
                    input_element.send_keys(invoice_key)
                    logger.info(f"[Job {job_id}] Invoice key entered")
                    
                    # Look for submit button
                    submit_selectors = [
                        'button[type="submit"]',
                        'input[type="submit"]',
                        '.btn-submit',
                        '#submit'
                    ]
                    
                    submit_button = None
                    for selector in submit_selectors:
                        try:
                            submit_button = self.driver.find_element(By.CSS_SELECTOR, selector)
                            break
                        except:
                            continue
                    
                    if not submit_button:
                        raise Exception("Could not find submit button")
                    
                    # Click submit
                    submit_button.click()
                    logger.info(f"[Job {job_id}] Submit button clicked")
                    
                    # Wait for response page
                    time.sleep(5)
                    
                    # Look for XML download options
                    xml_selectors = [
                        'a[href*="xml"]',
                        'button[onclick*="xml"]',
                        '.download-xml',
                        '#xml-download'
                    ]
                    
                    xml_button = None
                    for selector in xml_selectors:
                        try:
                            xml_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, selector)))
                            break
                        except:
                            continue
                    
                    if xml_button:
                        logger.info(f"[Job {job_id}] XML button found, clicking...")
                        xml_button.click()
                        
                        # Wait for download
                        time.sleep(10)
                        
                        # Check for downloaded file
                        downloads_dir = os.path.abspath('downloads')
                        expected_file = os.path.join(downloads_dir, f"{invoice_key}.xml")
                        
                        # Check for any XML file that might have been downloaded
                        for file in os.listdir(downloads_dir):
                            if file.endswith('.xml') and invoice_key in file:
                                downloaded_file = os.path.join(downloads_dir, file)
                                if os.path.exists(downloaded_file):
                                    # Rename to expected format if needed
                                    if downloaded_file != expected_file:
                                        os.rename(downloaded_file, expected_file)
                                    
                                    # Process and save XML to database
                                    self._process_and_save_xml(expected_file, invoice_key, job_id, user_id)
                                    
                                    logger.info(f"[Job {job_id}] File downloaded successfully: {expected_file}")
                                    return {
                                        "success": True,
                                        "file_path": expected_file,
                                        "file_size": os.path.getsize(expected_file)
                                    }
                    
                    # If direct download didn't work, try extracting XML from page source
                    page_source = self.driver.page_source
                    if '<?xml' in page_source and 'infNFe' in page_source:
                        logger.info(f"[Job {job_id}] Extracting XML from page source...")
                        xml_start = page_source.find('<?xml')
                        xml_end = page_source.find('</nfeProc>') + len('</nfeProc>')
                        
                        if xml_start != -1 and xml_end != -1:
                            xml_content = page_source[xml_start:xml_end]
                            
                            # Save XML file
                            xml_file_path = os.path.join(downloads_dir, f"{invoice_key}.xml")
                            with open(xml_file_path, 'w', encoding='utf-8') as f:
                                f.write(xml_content)
                            
                            # Process and save XML to database
                            self._process_and_save_xml(xml_file_path, invoice_key, job_id, user_id)
                            
                            logger.info(f"[Job {job_id}] XML extracted and saved: {xml_file_path}")
                            return {
                                "success": True,
                                "file_path": xml_file_path,
                                "file_size": os.path.getsize(xml_file_path)
                            }
                    
                    break  # Exit retry loop if we get here
                    
                except Exception as e:
                    logger.warning(f"[Job {job_id}] Attempt {attempt + 1} failed: {e}")
                    if attempt == self.max_retries - 1:
                        raise e
                    time.sleep(2)  # Wait before retry
            
            return {"success": False, "error": "Failed to download XML after all attempts"}
            
        except Exception as e:
            logger.error(f"[Job {job_id}] Production download failed: {e}")
            return {"success": False, "error": str(e)}
        
        finally:
            self.cleanup()
    
    def _process_and_save_xml(self, xml_file_path: str, invoice_key: str, job_id: str, user_id: int):
        """Process XML file and save to database with charging"""
        try:
            # Import here to avoid circular imports
            from download_service import process_xml_download
            
            logger.info(f"[Job {job_id}] Processing XML for database save: {invoice_key}")
            
            # Read XML content
            with open(xml_file_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            # Process through existing download service
            process_xml_download(user_id, invoice_key, xml_content, job_id)
            
            logger.info(f"[Job {job_id}] XML processed and saved to database: {invoice_key}")
            
        except Exception as e:
            logger.error(f"[Job {job_id}] Error processing XML for database: {e}")
            # Don't fail the download if database save fails
    
    def cleanup(self):
        """Clean up WebDriver resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except:
                pass
            self.driver = None