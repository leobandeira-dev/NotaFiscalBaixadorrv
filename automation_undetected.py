"""
Advanced automation with anti-bot detection and increased timeouts
Uses standard Selenium with stealth techniques to avoid bot detection
"""

import os
import time
import random
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import subprocess
import json
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StealthInvoiceDownloader:
    """Invoice downloader with anti-bot detection and human-like behavior"""
    
    def __init__(self):
        self.driver = None
        self.download_dir = "/home/runner/workspace/downloads"
        os.makedirs(self.download_dir, exist_ok=True)
        self._init_driver()
    
    def _get_random_delay(self, min_sec=1.5, max_sec=3.5):
        """Generate random delay to simulate human behavior"""
        return random.uniform(min_sec, max_sec)
    
    def _human_type(self, element, text):
        """Type text with random delays between characters"""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
    
    def _init_driver(self):
        """Initialize Chrome WebDriver with stealth options"""
        try:
            logger.info("Initializing STEALTH Chrome WebDriver...")
            
            # Find chromedriver
            result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
            chromedriver_path = result.stdout.strip()
            logger.info(f"Found chromedriver at: {chromedriver_path}")
            
            # Chrome options with anti-detection
            chrome_options = Options()
            
            # Basic options
            chrome_options.add_argument('--headless=new')  # New headless mode
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            
            # SSL/Certificate options - Allow insecure sites
            chrome_options.add_argument('--ignore-certificate-errors')
            chrome_options.add_argument('--ignore-ssl-errors')
            chrome_options.add_argument('--allow-insecure-localhost')
            chrome_options.add_argument('--allow-running-insecure-content')
            
            # Anti-detection: Window size
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--start-maximized')
            
            # Anti-detection: Realistic user agent
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            ]
            chrome_options.add_argument(f'user-agent={random.choice(user_agents)}')
            
            # Anti-detection: Disable automation flags
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Enable performance logging to capture network requests
            chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
            
            # Anti-detection: Add realistic preferences
            prefs = {
                'profile.default_content_setting_values.notifications': 2,
                'profile.default_content_settings.popups': 0,
                'download.default_directory': self.download_dir,
                'download.prompt_for_download': False,
                'download.directory_upgrade': True,
                'safebrowsing.enabled': True,
                'profile.default_content_setting_values.automatic_downloads': 1,
                # Language preferences
                'intl.accept_languages': 'pt-BR,pt,en-US,en',
                # Disable images for faster loading (optional)
                # 'profile.managed_default_content_settings.images': 2,
            }
            chrome_options.add_experimental_option('prefs', prefs)
            
            # Performance optimizations
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-infobars')
            chrome_options.add_argument('--disable-notifications')
            
            # Initialize service
            service = Service(chromedriver_path)
            
            # Create driver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            
            # Enable Network domain to capture download requests
            self.driver.execute_cdp_cmd('Network.enable', {})
            
            # Anti-detection: Execute CDP commands to hide webdriver
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": self.driver.execute_script("return navigator.userAgent").replace('Headless', '')
            })
            
            # Anti-detection: Override navigator.webdriver
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            # Anti-detection: Add Chrome runtime
            self.driver.execute_script("""
                window.navigator.chrome = {
                    runtime: {}
                };
            """)
            
            # Anti-detection: Override permissions
            self.driver.execute_script("""
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );
            """)
            
            # Anti-detection: Mock plugins
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5]
                });
            """)
            
            # Anti-detection: Mock languages
            self.driver.execute_script("""
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['pt-BR', 'pt', 'en-US', 'en']
                });
            """)
            
            # Set longer timeouts
            self.driver.set_page_load_timeout(90)  # 90 seconds
            self.driver.implicitly_wait(10)  # 10 seconds
            
            logger.info("✅ STEALTH Chrome WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Chrome WebDriver: {e}")
            raise
    
    def _extract_download_url_from_logs(self, job_id: str, file_type: str = 'xml'):
        """Extract download URL from Chrome performance logs"""
        try:
            logs = self.driver.get_log('performance')
            
            # Extensions to look for
            extensions = {
                'xml': ['.xml'],
                'danfe': ['.pdf', 'danfe']
            }
            search_extensions = extensions.get(file_type, ['.xml'])
            
            download_urls = []
            for log in logs:
                try:
                    message = json.loads(log['message'])['message']
                    
                    # Look for network response events
                    if message.get('method') == 'Network.responseReceived':
                        response = message.get('params', {}).get('response', {})
                        url = response.get('url', '')
                        
                        # Check for download indicators
                        headers = response.get('headers', {})
                        content_disposition = headers.get('content-disposition', '').lower()
                        content_type = response.get('mimeType', '').lower()
                        
                        # Check if this is a download
                        is_download = False
                        if 'attachment' in content_disposition:
                            is_download = True
                        elif any(ext in url.lower() for ext in search_extensions):
                            is_download = True
                        elif file_type == 'xml' and ('xml' in content_type or 'application/xml' in content_type):
                            is_download = True
                        elif file_type == 'danfe' and ('pdf' in content_type or 'application/pdf' in content_type):
                            is_download = True
                        
                        if is_download and url and url.startswith('http'):
                            download_urls.append(url)
                            logger.info(f"[Job {job_id}] 🎯 Found download URL: {url[:100]}...")
                
                except (json.JSONDecodeError, KeyError):
                    continue
            
            return download_urls
        
        except Exception as e:
            logger.error(f"[Job {job_id}] Error extracting download URL: {e}")
            return []
    
    def download_invoice_xml(self, invoice_key: str, job_id: str, download_type: str = 'xml', user_id: int = None):
        """
        Download XML or DANFE with stealth mode and increased timeouts
        
        Args:
            invoice_key: 44-digit invoice key
            job_id: Job ID for tracking
            download_type: 'xml' or 'danfe'
            user_id: User ID
        
        Returns:
            Dict with success status and file path or error
        """
        try:
            logger.info(f"[Job {job_id}] 🕵️ STEALTH MODE: Starting {download_type.upper()} download for: {invoice_key}")
            
            # Navigate to website
            url = "https://meudanfe.com.br/"
            logger.info(f"[Job {job_id}] 🌐 Navigating to {url}...")
            self.driver.get(url)
            
            # Wait for page load with longer timeout
            logger.info(f"[Job {job_id}] ⏳ Waiting for page to load (extended timeout)...")
            time.sleep(self._get_random_delay(5, 8))  # Longer initial wait
            
            # Wait for JavaScript to execute
            try:
                WebDriverWait(self.driver, 30).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                logger.info(f"[Job {job_id}] ✅ Page fully loaded")
            except TimeoutException:
                logger.warning(f"[Job {job_id}] ⚠️ Page load timeout, continuing anyway...")
            
            # Additional wait for dynamic content
            time.sleep(self._get_random_delay(3, 5))
            
            # Try to find input field with multiple strategies
            logger.info(f"[Job {job_id}] 🔍 Looking for input field...")
            input_element = None
            
            # List of selectors to try
            selectors = [
                (By.ID, 'searchTxt'),
                (By.NAME, 'searchTxt'),
                (By.CSS_SELECTOR, 'input[id="searchTxt"]'),
                (By.XPATH, "//input[@id='searchTxt']"),
                (By.CSS_SELECTOR, 'input[placeholder*="chave"]'),
                (By.CSS_SELECTOR, 'input[placeholder*="Chave"]'),
                (By.CSS_SELECTOR, 'input[type="text"]'),
                (By.XPATH, "//input[@type='text']"),
                (By.XPATH, "//input[contains(@placeholder, 'chave')]"),
                (By.XPATH, "//input[contains(@placeholder, 'Chave')]"),
                (By.CSS_SELECTOR, 'input.form-control'),
                (By.XPATH, "//input[@class='form-control']"),
            ]
            
            for i, (by_type, selector) in enumerate(selectors):
                try:
                    logger.info(f"[Job {job_id}] 🎯 Trying selector {i+1}/{len(selectors)}: {by_type}='{selector}'")
                    
                    # Wait for element to be present
                    element = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((by_type, selector))
                    )
                    
                    # Wait for element to be clickable
                    input_element = WebDriverWait(self.driver, 15).until(
                        EC.element_to_be_clickable((by_type, selector))
                    )
                    
                    logger.info(f"[Job {job_id}] ✅ Found input field with selector {i+1}")
                    break
                    
                except Exception as e:
                    logger.debug(f"[Job {job_id}] ❌ Selector {i+1} failed: {str(e)[:100]}")
                    continue
            
            if not input_element:
                # Debug: Save page source
                debug_file = f"/tmp/meudanfe_debug_{job_id}.html"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                logger.error(f"[Job {job_id}] Page source saved to: {debug_file}")
                
                # Debug: Take screenshot
                screenshot_file = f"/tmp/meudanfe_debug_{job_id}.png"
                self.driver.save_screenshot(screenshot_file)
                logger.error(f"[Job {job_id}] Screenshot saved to: {screenshot_file}")
                
                raise Exception("Input field not found after trying all selectors")
            
            # Human-like interaction: Move to element (simulate mouse movement)
            logger.info(f"[Job {job_id}] 🖱️ Simulating human interaction...")
            time.sleep(self._get_random_delay(0.5, 1.5))
            
            # Clear field
            input_element.clear()
            time.sleep(self._get_random_delay(0.3, 0.7))
            
            # Type with human-like delays
            logger.info(f"[Job {job_id}] ⌨️ Typing invoice key with human-like behavior...")
            self._human_type(input_element, invoice_key)
            
            # Verify input
            entered_value = input_element.get_attribute('value')
            logger.info(f"[Job {job_id}] Entered value: {entered_value}")
            
            if entered_value != invoice_key:
                logger.warning(f"[Job {job_id}] ⚠️ Input mismatch, trying JavaScript fallback...")
                self.driver.execute_script(f"arguments[0].value = '{invoice_key}';", input_element)
                time.sleep(self._get_random_delay(0.5, 1.0))
            
            # Find and click search button
            logger.info(f"[Job {job_id}] 🔍 Looking for search button...")
            search_button = None
            
            button_selectors = [
                (By.ID, 'searchBtn'),
                (By.XPATH, "//a[@id='searchBtn']"),
                (By.XPATH, "//button[contains(text(), 'BUSCAR')]"),
                (By.XPATH, "//a[contains(text(), 'BUSCAR')]"),
                (By.CSS_SELECTOR, 'button.btn-primary'),
                (By.CSS_SELECTOR, 'a.btn-primary'),
                (By.XPATH, "//button[@type='submit']"),
                (By.XPATH, "//a[contains(@class, 'btn')]"),
            ]
            
            for i, (by_type, selector) in enumerate(button_selectors):
                try:
                    logger.info(f"[Job {job_id}] 🎯 Trying button selector {i+1}: {by_type}='{selector}'")
                    search_button = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((by_type, selector))
                    )
                    logger.info(f"[Job {job_id}] ✅ Found search button")
                    break
                except Exception as e:
                    logger.debug(f"[Job {job_id}] Button selector {i+1} failed")
                    continue
            
            if not search_button:
                raise Exception("Search button not found")
            
            # Human delay before clicking
            time.sleep(self._get_random_delay(1.0, 2.0))
            
            # Click search button
            logger.info(f"[Job {job_id}] 🖱️ Clicking search button...")
            search_button.click()
            
            # Wait for the NEW PAGE to load by detecting specific elements that only appear AFTER results load
            logger.info(f"[Job {job_id}] ⏳ Waiting for results page to load completely...")
            
            # Multiple strategies to detect when results page is loaded
            page_loaded = False
            wait_strategies = [
                # Strategy 1: Wait for "NOVA CONSULTA" button (appears only on results page)
                (By.XPATH, "//button[contains(text(), 'NOVA CONSULTA')]"),
                (By.XPATH, "//*[contains(text(), 'NOVA CONSULTA')]"),
                # Strategy 2: Wait for invoice key display
                (By.XPATH, f"//*[contains(text(), '{invoice_key}')]"),
                # Strategy 3: Wait for any download button
                (By.ID, 'downloadXmlBtn'),
                (By.ID, 'downloadDanfeBtn'),
            ]
            
            for by_type, selector in wait_strategies:
                try:
                    logger.info(f"[Job {job_id}] 🔍 Checking for results page element: {selector[:50]}...")
                    WebDriverWait(self.driver, 30).until(
                        EC.presence_of_element_located((by_type, selector))
                    )
                    logger.info(f"[Job {job_id}] ✅ Results page loaded! (detected via: {selector[:50]})")
                    page_loaded = True
                    break
                except:
                    continue
            
            if not page_loaded:
                logger.warning(f"[Job {job_id}] ⚠️ Could not detect results page load, proceeding anyway...")
                # Fallback to time-based wait
                time.sleep(10)
            
            # Extra buffer for any animations/transitions
            logger.info(f"[Job {job_id}] ⏳ Waiting for page animations to complete...")
            time.sleep(3)
            
            # Find download button based on type
            logger.info(f"[Job {job_id}] 🔍 Looking for {download_type.upper()} download button...")
            
            if download_type == 'xml':
                download_selectors = [
                    (By.ID, 'downloadXmlBtn'),  # CORRECT ID from website!
                    (By.XPATH, "//a[@id='downloadXmlBtn']"),
                    (By.XPATH, "//a[contains(text(), 'Baixar XML')]"),
                    (By.XPATH, "//a[contains(.//span, 'Baixar XML')]"),
                    (By.CSS_SELECTOR, "a#downloadXmlBtn"),
                    (By.XPATH, "//*[@id='downloadXmlBtn']"),
                ]
            else:  # danfe
                download_selectors = [
                    (By.ID, 'downloadDanfeBtn'),  # CORRECT ID from website!
                    (By.XPATH, "//a[@id='downloadDanfeBtn']"),
                    (By.XPATH, "//a[contains(text(), 'Baixar DANFE')]"),
                    (By.XPATH, "//a[contains(.//span, 'Baixar DANFE')]"),
                    (By.CSS_SELECTOR, "a#downloadDanfeBtn"),
                    (By.XPATH, "//*[@id='downloadDanfeBtn']"),
                ]
            
            download_button = None
            for i, (by_type, selector) in enumerate(download_selectors):
                try:
                    # First, wait for element to be PRESENT (not necessarily visible)
                    download_button = WebDriverWait(self.driver, 15).until(
                        EC.presence_of_element_located((by_type, selector))
                    )
                    logger.info(f"[Job {job_id}] ✅ Found {download_type.upper()} download button (ID: {selector if by_type == By.ID else 'other'})")
                    break
                except:
                    continue
            
            if not download_button:
                raise Exception(f"{download_type.upper()} download button not found")
            
            # Scroll to button to make it visible (CRITICAL FIX!)
            logger.info(f"[Job {job_id}] 📜 Scrolling to {download_type.upper()} button...")
            self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", download_button)
            time.sleep(2)  # Wait for scroll animation
            
            # Human delay before download
            time.sleep(self._get_random_delay(1.0, 2.0))
            
            # Get list of files BEFORE clicking
            files_before = set(os.listdir(self.download_dir))
            
            # Click download using JavaScript (more robust than Selenium click)
            logger.info(f"[Job {job_id}] 📥 Clicking {download_type.upper()} download with JavaScript...")
            self.driver.execute_script("arguments[0].click();", download_button)
            
            # Wait for download to complete by checking for new files
            logger.info(f"[Job {job_id}] ⏳ Waiting for file to download...")
            max_wait = 30  # 30 seconds max wait
            check_interval = 1  # Check every second
            downloaded_file = None
            
            for i in range(max_wait):
                time.sleep(check_interval)
                files_after = set(os.listdir(self.download_dir))
                new_files = files_after - files_before
                
                # Filter out partial downloads (.crdownload, .tmp)
                completed_files = [f for f in new_files if not f.endswith(('.crdownload', '.tmp', '.part'))]
                
                if completed_files:
                    downloaded_file = completed_files[0]
                    logger.info(f"[Job {job_id}] ✅ Found downloaded file: {downloaded_file}")
                    break
                
                if i > 0 and i % 5 == 0:
                    logger.info(f"[Job {job_id}] Still waiting... ({i}s elapsed)")
            
            if not downloaded_file:
                raise Exception(f"Download timeout: no new file appeared after {max_wait} seconds")
            
            # Determine correct file extension and rename
            file_ext = 'pdf' if download_type == 'danfe' else 'xml'
            old_path = os.path.join(self.download_dir, downloaded_file)
            new_path = f"{self.download_dir}/{invoice_key}.{file_ext}"
            
            # Rename file to correct name
            os.rename(old_path, new_path)
            logger.info(f"[Job {job_id}] ✅ File renamed to: {new_path}")
            
            return {
                'success': True,
                'file_path': new_path,
                'message': f'{download_type.upper()} downloaded successfully'
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[Job {job_id}] ❌ Error: {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'message': f'Failed to download {download_type.upper()}'
            }
    
    def cleanup(self):
        """Close the WebDriver"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("✅ WebDriver closed successfully")
        except Exception as e:
            logger.error(f"Error closing WebDriver: {e}")
