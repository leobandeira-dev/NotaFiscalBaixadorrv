import os
import time
import logging
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class InvoiceDownloader:
    def __init__(self):
        self.driver: Optional[webdriver.Chrome] = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        try:
            logger.info("Setting up Chrome WebDriver...")
            
            chrome_options = Options()
            # Essential headless options for Replit environment - more stable configuration
            chrome_options.add_argument('--headless')  # Use standard headless mode for stability
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-software-rasterizer')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-features=TranslateUI,VizDisplayCompositor')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            # Keep JavaScript enabled as website likely needs it
            chrome_options.add_argument('--window-size=1280,720')  # Smaller window size
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')
            
            # Memory and performance optimizations for stability
            chrome_options.add_argument('--memory-pressure-off')
            chrome_options.add_argument('--max_old_space_size=2048')  # Reduced memory
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--disable-web-security')
            # Remove single-process as it can cause instability
            chrome_options.add_argument('--disable-crash-reporter')
            chrome_options.add_argument('--disable-in-process-stack-traces')
            
            # Download preferences
            download_dir = os.path.abspath('downloads')
            logger.info(f"Setting download directory to: {download_dir}")
            prefs = {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False,
                "profile.default_content_settings.popups": 0
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Auto-detect chromedriver path
            import subprocess
            chromedriver_path = None
            
            try:
                # Try to find chromedriver using which command
                result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
                if result.returncode == 0:
                    chromedriver_path = result.stdout.strip()
                    logger.info(f"Found chromedriver at: {chromedriver_path}")
            except Exception as e:
                logger.warning(f"Could not auto-detect chromedriver: {e}")
            
            # Try to use detected or system chromedriver
            if chromedriver_path:
                try:
                    logger.info(f"Attempting to use chromedriver at: {chromedriver_path}")
                    service = Service(executable_path=chromedriver_path)
                    self.driver = webdriver.Chrome(service=service, options=chrome_options)
                    logger.info("Successfully initialized Chrome with detected chromedriver")
                except Exception as detected_error:
                    logger.warning(f"Detected chromedriver failed: {detected_error}")
                    self.driver = None
            
            # Fallback to selenium manager if detection failed
            if not self.driver:
                try:
                    logger.info("Using selenium manager as fallback...")
                    self.driver = webdriver.Chrome(options=chrome_options)
                    logger.info("Successfully initialized Chrome with selenium manager")
                except Exception as selenium_error:
                    logger.error(f"Selenium manager also failed: {selenium_error}")
                    raise selenium_error
            
            # Set shorter timeouts to prevent hanging
            self.driver.implicitly_wait(5)
            self.driver.set_page_load_timeout(20)
            self.driver.set_script_timeout(15)
            
            # Test driver with a simple page
            logger.info("Testing Chrome WebDriver with simple page...")
            self.driver.get("data:text/html,<html><body>Test</body></html>")
            logger.info("Chrome WebDriver test successful")
            
            logger.info("Chrome WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup Chrome WebDriver: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            raise
    
    def download_invoice_xml(self, invoice_key: str, job_id: str, download_type: str = 'xml') -> Dict[str, Any]:
        """Download XML or DANFE for a specific invoice key"""
        try:
            logger.info(f"[Job {job_id}] Starting {download_type.upper()} download for invoice key: {invoice_key}")
            
            # Check if driver is available
            if not self.driver:
                return {
                    'success': False,
                    'error': 'WebDriver não está disponível'
                }
            
            # Navigate to the website
            url = "https://meudanfe.com.br/"
            logger.info(f"[Job {job_id}] Navigating to invoice system...")
            self.driver.get(url)
            
            # Wait for page to load and log page info
            logger.info(f"[Job {job_id}] Waiting for page to load...")
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Log current page details for debugging
            current_url = self.driver.current_url
            page_title = self.driver.title
            logger.info(f"[Job {job_id}] Page loaded - URL: {current_url}, Title: {page_title}")
            
            # Save page source for debugging if needed
            try:
                page_source = self.driver.page_source[:2000]  # First 2000 chars
                logger.debug(f"[Job {job_id}] Page source preview: {page_source}")
            except:
                logger.warning(f"[Job {job_id}] Could not capture page source")
            
            # Look for input field for invoice key
            logger.info(f"[Job {job_id}] Looking for input field for invoice key...")
            
            # Use specific selectors based on website analysis
            input_selectors = [
                'input[placeholder="Digite a CHAVE DE ACESSO"]',  # Exact match
                'input[placeholder*="CHAVE DE ACESSO"]',         # Partial match
                'input[placeholder*="chave"]',                   # Fallback 1
                'input[type="text"]'                             # Fallback 2
            ]
            
            input_element = None
            for i, selector in enumerate(input_selectors):
                try:
                    logger.debug(f"[Job {job_id}] Trying selector {i+1}/{len(input_selectors)}: {selector}")
                    input_element = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"[Job {job_id}] Found input element with selector: {selector}")
                    break
                except TimeoutException:
                    logger.debug(f"[Job {job_id}] Selector {selector} not found")
                    continue
            
            if not input_element:
                # List all input elements found on page for debugging
                try:
                    all_inputs = self.driver.find_elements(By.TAG_NAME, "input")
                    logger.info(f"[Job {job_id}] Found {len(all_inputs)} input elements on page:")
                    for idx, inp in enumerate(all_inputs[:10]):  # Log first 10
                        try:
                            inp_type = inp.get_attribute('type') or 'unknown'
                            inp_name = inp.get_attribute('name') or 'no-name'
                            inp_id = inp.get_attribute('id') or 'no-id'
                            inp_placeholder = inp.get_attribute('placeholder') or 'no-placeholder'
                            logger.info(f"[Job {job_id}] Input {idx+1}: type={inp_type}, name={inp_name}, id={inp_id}, placeholder={inp_placeholder}")
                        except:
                            logger.warning(f"[Job {job_id}] Could not inspect input {idx+1}")
                except Exception as e:
                    logger.error(f"[Job {job_id}] Error listing input elements: {e}")
                
                return {
                    'success': False,
                    'error': 'Campo de entrada para chave da nota fiscal não encontrado'
                }
            
            # Clear and enter the invoice key
            logger.info(f"[Job {job_id}] Entering invoice key into input field...")
            input_element.clear()
            input_element.send_keys(invoice_key)
            logger.info(f"[Job {job_id}] Invoice key entered successfully")
            
            # Look for submit button - use specific selectors from website analysis
            logger.info(f"[Job {job_id}] Looking for submit button...")
            submit_selectors = [
                'button[type="submit"]',
                '.btn',
                'button'
            ]
            
            submit_button = None
            for i, selector in enumerate(submit_selectors):
                try:
                    logger.debug(f"[Job {job_id}] Trying submit selector {i+1}/{len(submit_selectors)}: {selector}")
                    submit_button = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"[Job {job_id}] Found submit button with selector: {selector}")
                    break
                except TimeoutException:
                    logger.debug(f"[Job {job_id}] Submit selector {selector} not found")
                    continue
            
            # Also try to find buttons by text content
            if not submit_button:
                logger.info(f"[Job {job_id}] Trying to find submit button by text content...")
                try:
                    buttons = self.driver.find_elements(By.TAG_NAME, "button")
                    logger.info(f"[Job {job_id}] Found {len(buttons)} button elements")
                    for idx, btn in enumerate(buttons):
                        try:
                            btn_text = btn.text.lower().strip()
                            logger.debug(f"[Job {job_id}] Button {idx+1} text: '{btn_text}'")
                            if any(text in btn_text for text in ['buscar', 'consultar', 'download', 'enviar', 'pesquisar', 'ir']):
                                submit_button = btn
                                logger.info(f"[Job {job_id}] Found submit button by text: '{btn_text}'")
                                break
                        except:
                            logger.warning(f"[Job {job_id}] Could not inspect button {idx+1}")
                except Exception as e:
                    logger.error(f"[Job {job_id}] Error finding buttons by text: {e}")
            
            if not submit_button:
                return {
                    'success': False,
                    'error': 'Botão de envio não encontrado'
                }
            
            # Click submit button
            logger.info(f"[Job {job_id}] Clicking submit button...")
            submit_button.click()
            logger.info(f"[Job {job_id}] Submit button clicked")
            
            # Wait for response/results page
            logger.info(f"[Job {job_id}] Waiting for response page...")
            time.sleep(5)  # Increased wait time
            
            # Log new page details
            new_url = self.driver.current_url
            new_title = self.driver.title
            logger.info(f"[Job {job_id}] After submit - URL: {new_url}, Title: {new_title}")
            
            # Enhanced download extraction - look for the appropriate download button
            logger.info(f"[Job {job_id}] Looking for {download_type.upper()} download button...")
            
            # Look for the appropriate download button based on type
            download_button_found = False
            
            if download_type.lower() == 'xml':
                search_texts = ['baixar xml', 'xml']
                button_type = 'XML'
            elif download_type.lower() == 'danfe':
                search_texts = ['baixar danfe', 'danfe']
                button_type = 'DANFE'
            else:
                search_texts = ['baixar xml', 'xml']  # Default to XML
                button_type = 'XML'
            
            try:
                # First try with CSS selectors that might match the download button
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                logger.info(f"[Job {job_id}] Found {len(buttons)} buttons on page")
                
                for idx, btn in enumerate(buttons):
                    try:
                        btn_text = btn.text.strip()
                        btn_style = btn.get_attribute('style') or ''
                        btn_class = btn.get_attribute('class') or ''
                        
                        logger.debug(f"[Job {job_id}] Button {idx+1}: text='{btn_text}', class='{btn_class}', style='{btn_style[:100]}'")
                        
                        # Look specifically for the requested download button
                        if any(search_text in btn_text.lower() for search_text in search_texts):
                            logger.info(f"[Job {job_id}] Found {button_type} button: '{btn_text}'")
                            
                            # Check if button has href attribute (is actually a link)
                            btn_href = btn.get_attribute('onclick') or btn.get_attribute('href')
                            if btn_href:
                                logger.info(f"[Job {job_id}] Button has action: {btn_href[:100]}")
                            
                            # Store window handles before clicking
                            original_handles = self.driver.window_handles
                            
                            btn.click()
                            download_button_found = True
                            time.sleep(3)  # Wait for action to complete
                            
                            # Check if new window opened
                            new_handles = self.driver.window_handles
                            if len(new_handles) > len(original_handles):
                                logger.info(f"[Job {job_id}] New window opened after clicking {button_type} button")
                            
                            logger.info(f"[Job {job_id}] Clicked {button_type} download button")
                            break
                            
                    except Exception as e:
                        logger.warning(f"[Job {job_id}] Error checking button {idx+1}: {e}")
                        continue
                        
            except Exception as e:
                logger.warning(f"[Job {job_id}] Error finding {button_type} buttons: {e}")
            
            # If download button was found and clicked, check for download or content
            if download_button_found:
                logger.info(f"[Job {job_id}] {button_type} button was clicked, starting comprehensive capture strategies...")
                logger.info(f"[Job {job_id}] Current URL after button click: {self.driver.current_url}")
                logger.info(f"[Job {job_id}] Page title after button click: {self.driver.title}")
                
                # Wait for the download/content to load
                time.sleep(3)
                
                # Strategy 0: Check if a direct download happened first
                download_result = self.check_downloaded_file(invoice_key, job_id, download_type)
                if download_result['success']:
                    return download_result
                
                # Strategy 0.5: Try to get the href of the clicked button and download directly
                try:
                    logger.info(f"[Job {job_id}] Checking for direct download link...")
                    current_url = self.driver.current_url
                    page_source = self.driver.page_source
                    
                    # Look for XML download links in the current page
                    import re
                    xml_links = re.findall(r'href=["\']([^"\']*\.xml[^"\']*)["\']', page_source, re.IGNORECASE)
                    if xml_links:
                        for xml_link in xml_links:
                            logger.info(f"[Job {job_id}] Found XML link: {xml_link}")
                            try:
                                if xml_link.startswith('http'):
                                    download_url = xml_link
                                else:
                                    # Relative URL
                                    from urllib.parse import urljoin
                                    download_url = urljoin(current_url, xml_link)
                                
                                logger.info(f"[Job {job_id}] Attempting direct download from: {download_url}")
                                download_result = self.download_file(download_url, invoice_key, job_id)
                                if download_result['success']:
                                    return download_result
                            except Exception as e:
                                logger.debug(f"[Job {job_id}] Failed to download from {xml_link}: {e}")
                                continue
                except Exception as e:
                    logger.warning(f"[Job {job_id}] Error checking for direct download links: {e}")
                
                # Wait a bit more for content to load
                time.sleep(5)
                
                # CRITICAL: Force execution of all XML capture strategies
                logger.info(f"[Job {job_id}] ===== STARTING COMPREHENSIVE XML CAPTURE =====")
                
                xml_captured = False
                final_result = None
                
                # Enhanced XML extraction strategies specifically for meudanfe.com.br
                try:
                    # Strategy 1: Check browser downloads first
                    logger.info(f"[Job {job_id}] Strategy 1: Checking browser downloads...")
                    time.sleep(3)  # Give more time for download
                    download_result = self.check_downloaded_file(invoice_key, job_id, download_type)
                    if download_result['success']:
                        logger.info(f"[Job {job_id}] SUCCESS: Found file via browser download")
                        xml_captured = True
                        final_result = download_result
                    else:
                        logger.info(f"[Job {job_id}] Strategy 1 failed: No file in downloads directory")
                    
                    # Strategy 2: Direct page analysis for XML content
                    logger.info(f"[Job {job_id}] Strategy 2: Analyzing current page for XML content...")
                    current_page_source = self.driver.page_source
                    xml_content = self.extract_xml_from_page(current_page_source, job_id)
                    if xml_content and not xml_captured:
                        logger.info(f"[Job {job_id}] SUCCESS: Found XML content in page source")
                        result = self.save_xml_file(xml_content, invoice_key, job_id)
                        if result['success']:
                            xml_captured = True
                            final_result = result
                    
                    # Strategy 3: Wait longer and check for delayed downloads
                    if not xml_captured:
                        logger.info(f"[Job {job_id}] Strategy 3: Waiting for delayed download...")
                        time.sleep(10)  # Wait longer for potential download
                        download_result = self.check_downloaded_file(invoice_key, job_id, download_type)
                        if download_result['success']:
                            logger.info(f"[Job {job_id}] SUCCESS: Found delayed download")
                            xml_captured = True
                            final_result = download_result
                    
                    # Return result if XML was captured
                    if xml_captured and final_result:
                        logger.info(f"[Job {job_id}] ===== XML CAPTURE SUCCESSFUL =====")
                        return final_result
                    
                    # Continue with additional strategies
                    current_url = self.driver.current_url
                    
                    # Look for direct XML content that may have been loaded in the page
                    xml_content = self.extract_xml_from_page(current_page_source, job_id)
                    if xml_content:
                        logger.info(f"[Job {job_id}] Found XML content in current page")
                        return self.save_xml_file(xml_content, invoice_key, job_id)
                    
                    # Strategy 1.6: Check if we can construct the download URL manually
                    # meudanfe.com.br often uses predictable URL patterns
                    if 'ver-danfe' in current_url:
                        logger.info(f"[Job {job_id}] Attempting to construct direct XML download URL...")
                        try:
                            # Try common URL patterns for XML download
                            base_url = current_url.replace('/ver-danfe', '')
                            potential_xml_urls = [
                                f"{base_url}/download-xml/{invoice_key}",
                                f"{base_url}/xml/{invoice_key}",
                                f"{base_url}/download/{invoice_key}.xml",
                                f"https://meudanfe.com.br/download-xml/{invoice_key}",
                                f"https://meudanfe.com.br/xml/{invoice_key}.xml"
                            ]
                            
                            for xml_url in potential_xml_urls:
                                logger.info(f"[Job {job_id}] Trying direct XML URL: {xml_url}")
                                try:
                                    download_result = self.download_file(xml_url, invoice_key, job_id)
                                    if download_result['success']:
                                        return download_result
                                except Exception as e:
                                    logger.debug(f"[Job {job_id}] Direct URL failed: {e}")
                                    continue
                        except Exception as e:
                            logger.warning(f"[Job {job_id}] Error trying direct URLs: {e}")
                    
                    # Strategy 2: Look for meudanfe.com.br specific XML patterns
                    import re
                    logger.info(f"[Job {job_id}] Analyzing page for meudanfe.com.br XML patterns...")
                    
                    # Check for specific patterns used by meudanfe.com.br
                    # Look for hidden download links or form actions
                    download_patterns = [
                        r'href=["\']([^"\']*download[^"\']*xml[^"\']*)["\']',
                        r'href=["\']([^"\']*xml[^"\']*download[^"\']*)["\']',
                        r'action=["\']([^"\']*download[^"\']*)["\']',
                        r'data-href=["\']([^"\']*\.xml[^"\']*)["\']',
                        r'data-url=["\']([^"\']*\.xml[^"\']*)["\']',
                        r'data-download=["\']([^"\']*\.xml[^"\']*)["\']'
                    ]
                    
                    dynamic_links = []
                    for pattern in download_patterns:
                        matches = re.findall(pattern, current_page_source, re.IGNORECASE)
                        dynamic_links.extend(matches)
                        if matches:
                            logger.info(f"[Job {job_id}] Found {len(matches)} links with pattern: {pattern[:30]}...")
                    
                    # Also check for JavaScript-generated URLs
                    js_patterns = [
                        r'window\.open\(["\']([^"\']*\.xml[^"\']*)["\']',
                        r'location\.href\s*=\s*["\']([^"\']*\.xml[^"\']*)["\']',
                        r'download\(["\']([^"\']*\.xml[^"\']*)["\']'
                    ]
                    
                    for pattern in js_patterns:
                        matches = re.findall(pattern, current_page_source, re.IGNORECASE)
                        dynamic_links.extend(matches)
                    
                    for link in dynamic_links:
                        logger.info(f"[Job {job_id}] Found dynamic XML link: {link}")
                        try:
                            if not link.startswith('http'):
                                from urllib.parse import urljoin
                                link = urljoin(self.driver.current_url, link)
                            
                            download_result = self.download_file(link, invoice_key, job_id)
                            if download_result['success']:
                                return download_result
                        except Exception as e:
                            logger.debug(f"[Job {job_id}] Failed to download from dynamic link {link}: {e}")
                    
                    # Strategy 3: Check for new tabs/windows
                    original_window = self.driver.current_window_handle
                    all_windows = self.driver.window_handles
                    
                    if len(all_windows) > 1:
                        logger.info(f"[Job {job_id}] Checking {len(all_windows)} windows for XML content")
                        for window_handle in all_windows:
                            if window_handle != original_window:
                                try:
                                    self.driver.switch_to.window(window_handle)
                                    time.sleep(3)
                                    
                                    page_url = self.driver.current_url
                                    page_source = self.driver.page_source
                                    
                                    logger.info(f"[Job {job_id}] Checking window: {page_url[:100]}")
                                    
                                    # Check if this is an XML file URL
                                    if '.xml' in page_url.lower():
                                        logger.info(f"[Job {job_id}] Found XML URL in new window: {page_url}")
                                        try:
                                            download_result = self.download_file(page_url, invoice_key, job_id)
                                            self.driver.close()
                                            self.driver.switch_to.window(original_window)
                                            if download_result['success']:
                                                return download_result
                                        except Exception as e:
                                            logger.warning(f"[Job {job_id}] Failed to download from window URL: {e}")
                                    
                                    # Look for XML content in the new window
                                    xml_content = self.extract_xml_from_page(page_source, job_id)
                                    if xml_content:
                                        self.driver.close()
                                        self.driver.switch_to.window(original_window)
                                        return self.save_xml_file(xml_content, invoice_key, job_id)
                                    
                                    self.driver.close()
                                except Exception as e:
                                    logger.warning(f"[Job {job_id}] Error checking window: {e}")
                                    try:
                                        self.driver.close()
                                    except:
                                        pass
                        
                        self.driver.switch_to.window(original_window)
                    
                    # Strategy 2: Check current page for XML content
                    time.sleep(3)
                    page_source = self.driver.page_source
                    xml_content = self.extract_xml_from_page(page_source, job_id)
                    if xml_content:
                        return self.save_xml_file(xml_content, invoice_key, job_id)
                    
                    # Strategy 3: Look for download links or iframe content
                    try:
                        # Check for any download links that might contain XML
                        download_links = self.driver.find_elements(By.TAG_NAME, "a")
                        for link in download_links:
                            try:
                                href = link.get_attribute('href')
                                text = link.text.lower()
                                if href and ('xml' in href.lower() or 'xml' in text):
                                    logger.info(f"[Job {job_id}] Found XML download link: {href}")
                                    # Try to download directly using requests
                                    download_result = self.download_file(href, invoice_key, job_id)
                                    if download_result['success']:
                                        return download_result
                            except Exception as e:
                                logger.debug(f"[Job {job_id}] Error checking link: {e}")
                                continue
                    except Exception as e:
                        logger.warning(f"[Job {job_id}] Error checking download links: {e}")
                    
                    # Strategy 4: Check for iframes with XML content
                    try:
                        iframes = self.driver.find_elements(By.TAG_NAME, "iframe")
                        for idx, iframe in enumerate(iframes):
                            try:
                                self.driver.switch_to.frame(iframe)
                                iframe_source = self.driver.page_source
                                xml_content = self.extract_xml_from_page(iframe_source, job_id)
                                if xml_content:
                                    self.driver.switch_to.default_content()
                                    return self.save_xml_file(xml_content, invoice_key, job_id)
                                self.driver.switch_to.default_content()
                            except Exception as e:
                                logger.debug(f"[Job {job_id}] Error checking iframe {idx}: {e}")
                                try:
                                    self.driver.switch_to.default_content()
                                except:
                                    pass
                    except Exception as e:
                        logger.warning(f"[Job {job_id}] Error checking iframes: {e}")
                
                except Exception as e:
                    logger.error(f"[Job {job_id}] Error in XML extraction strategies: {e}")
            
            # If button click didn't work, try to find download links
            if not download_button_found:
                logger.info(f"[Job {job_id}] {button_type} button not found, looking for download links...")
            
            # Look for download links with enhanced selectors
            download_selectors = [
                'a[href*=".xml"]',
                'a[href*="download"]', 
                'a[download]',
                'a[href*="xml"]',
                'a[href*="arquivo"]',
                'a[href*="file"]',
                'a[href*="danfe"]'
            ]
            
            download_link = None
            for selector in download_selectors:
                try:
                    download_link = self.driver.find_element(By.CSS_SELECTOR, selector)
                    logger.info(f"[Job {job_id}] Found download link with selector: {selector}")
                    break
                except:
                    continue
            
            # Enhanced text-based link search
            if not download_link:
                try:
                    links = self.driver.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        try:
                            link_text = link.text.lower().strip()
                            link_href = link.get_attribute('href') or ''
                            
                            if any(keyword in link_text for keyword in ['xml', 'download', 'baixar', 'arquivo', 'danfe']) or \
                               any(keyword in link_href.lower() for keyword in ['.xml', 'download', 'arquivo', 'xml']):
                                download_link = link
                                logger.info(f"[Job {job_id}] Found download link by content: '{link_text}' -> '{link_href}'")
                                break
                        except:
                            continue
                except Exception as e:
                    logger.warning(f"[Job {job_id}] Error searching links: {e}")
            
            # Process download link if found
            if download_link:
                try:
                    download_url = download_link.get_attribute('href')
                    logger.info(f"[Job {job_id}] Found download URL: {download_url}")
                    
                    # Skip if URL redirects to homepage
                    if download_url and download_url.rstrip('/').endswith('.com.br'):
                        logger.warning(f"[Job {job_id}] Download link redirects to homepage, skipping direct download")
                    elif download_url and download_url.startswith('http'):
                        logger.info(f"[Job {job_id}] Attempting direct download from URL: {download_url}")
                        return self.download_file(download_url, invoice_key, job_id)
                    else:
                        logger.info(f"[Job {job_id}] Clicking download link...")
                        download_link.click()
                        time.sleep(8)
                        return self.check_downloaded_file(invoice_key, job_id)
                except Exception as e:
                    logger.warning(f"[Job {job_id}] Error processing download link: {e}")
            
            # Enhanced XML content search
            logger.info(f"[Job {job_id}] Searching for XML content in page elements...")
            xml_content = None
            
            # Try various selectors and approaches to find XML
            xml_search_strategies = [
                # Direct element searches
                ('CSS', 'pre'),
                ('CSS', 'code'), 
                ('CSS', 'textarea'),
                ('CSS', '[class*="xml"]'),
                ('CSS', '[id*="xml"]'),
                ('CSS', 'div'),
                ('CSS', 'span'),
                # XPath searches for XML patterns
                ('XPATH', '//*[contains(text(), "<?xml")]'),
                ('XPATH', '//*[contains(text(), "<nfeProc")]'),
                ('XPATH', '//*[contains(text(), "<NFe")]'),
                ('XPATH', '//*[contains(text(), "<infNFe")]'),
            ]
            
            for strategy_type, selector in xml_search_strategies:
                try:
                    if strategy_type == 'CSS':
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    else:  # XPATH
                        elements = self.driver.find_elements(By.XPATH, selector)
                    
                    for element in elements:
                        try:
                            content = element.text.strip()
                            # More comprehensive XML detection
                            if content and len(content) > 50 and any(pattern in content for pattern in [
                                '<?xml', '<nfeProc', '<NFe', '<infNFe', 'versao=', 'xmlns='
                            ]):
                                xml_content = content
                                logger.info(f"[Job {job_id}] Found XML content using {strategy_type} selector '{selector}' (length: {len(content)})")
                                break
                        except:
                            continue
                    
                    if xml_content:
                        break
                        
                except Exception as e:
                    logger.debug(f"[Job {job_id}] Strategy {strategy_type}:'{selector}' failed: {e}")
                    continue
            
            # Check page source directly as last resort
            if not xml_content:
                try:
                    page_source = self.driver.page_source
                    if '<?xml' in page_source and ('<nfeProc' in page_source or '<NFe' in page_source):
                        logger.info(f"[Job {job_id}] Found XML content in page source")
                        # Extract XML from page source
                        import re
                        xml_match = re.search(r'(<\?xml.*?</nfeProc>)', page_source, re.DOTALL)
                        if not xml_match:
                            xml_match = re.search(r'(<\?xml.*?</NFe>)', page_source, re.DOTALL)
                        
                        if xml_match:
                            xml_content = xml_match.group(1)
                            logger.info(f"[Job {job_id}] Extracted XML from page source (length: {len(xml_content)})")
                except Exception as e:
                    logger.warning(f"[Job {job_id}] Error checking page source: {e}")
            
            # If no XML found yet, try to look for it in the current page after clicking XML button
            if not xml_content:
                logger.info(f"[Job {job_id}] No XML content found yet, checking current page source...")
                try:
                    # Wait a bit more and check page source
                    time.sleep(3)
                    page_source = self.driver.page_source
                    
                    # Look for XML patterns in the page
                    import re
                    # Try to find XML content that might be embedded
                    xml_patterns = [
                        r'(<\?xml[^>]*>.*?</nfeProc>)',
                        r'(<\?xml[^>]*>.*?</NFe>)', 
                        r'(<nfeProc[^>]*>.*?</nfeProc>)',
                        r'(<NFe[^>]*>.*?</NFe>)'
                    ]
                    
                    for pattern in xml_patterns:
                        match = re.search(pattern, page_source, re.DOTALL | re.IGNORECASE)
                        if match:
                            xml_content = match.group(1)
                            logger.info(f"[Job {job_id}] Found XML pattern in page source (length: {len(xml_content)})")
                            break
                            
                    # If still no XML, try to find it in text content of elements
                    if not xml_content:
                        logger.info(f"[Job {job_id}] Searching for XML in all page elements...")
                        all_elements = self.driver.find_elements(By.XPATH, "//*")
                        for element in all_elements:
                            try:
                                text = element.text.strip()
                                if text and len(text) > 100 and ('<?xml' in text or '<nfeProc' in text or '<NFe' in text):
                                    xml_content = text
                                    logger.info(f"[Job {job_id}] Found XML in element text (length: {len(xml_content)})")
                                    break
                            except:
                                continue
                                
                except Exception as e:
                    logger.warning(f"[Job {job_id}] Error in enhanced XML search: {e}")

            # Save XML content if found
            if xml_content:
                try:
                    filename = f"{invoice_key}.xml"
                    file_path = os.path.join('downloads', filename)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(xml_content)
                    
                    logger.info(f"[Job {job_id}] XML content saved to: {file_path}")
                    
                    # If download type is DANFE, generate PDF from XML
                    if download_type.lower() == 'danfe':
                        return self.generate_danfe_from_xml(file_path, invoice_key, job_id)
                    else:
                        return {
                            'success': True,
                            'file_path': file_path
                        }
                except Exception as e:
                    logger.error(f"[Job {job_id}] Error saving XML content: {e}")
                    return {
                        'success': False,
                        'error': f'Erro ao salvar XML: {str(e)}'
                    }
            
            # Check for error messages on the page
            try:
                error_keywords = ['erro', 'inválid', 'não encontrad', 'inexistent', 'error']
                page_text = self.driver.find_element(By.TAG_NAME, "body").text.lower()
                
                for keyword in error_keywords:
                    if keyword in page_text:
                        logger.warning(f"[Job {job_id}] Detected error keyword '{keyword}' in page")
                        return {
                            'success': False,
                            'error': f'Possível erro na consulta - página contém "{keyword}"'
                        }
            except:
                pass
            
            logger.warning(f"[Job {job_id}] No XML content found for invoice key: {invoice_key}")
            return {
                'success': False,
                'error': 'XML não encontrado na página de resultados'
            }
            
        except TimeoutException as e:
            logger.error(f"[Job {job_id}] Timeout error for {invoice_key}: {e}")
            return {
                'success': False,
                'error': 'Timeout aguardando resposta do site'
            }
        except WebDriverException as e:
            logger.error(f"[Job {job_id}] WebDriver error for {invoice_key}: {e}")
            return {
                'success': False,
                'error': f'Erro do WebDriver: {str(e)}'
            }
        except Exception as e:
            logger.error(f"[Job {job_id}] Unexpected error downloading {invoice_key}: {str(e)}")
            import traceback
            logger.error(f"[Job {job_id}] Full traceback: {traceback.format_exc()}")
            return {
                'success': False,
                'error': f'Erro inesperado: {str(e)}'
            }
    
    def download_file(self, url: str, invoice_key: str, job_id: str) -> Dict[str, Any]:
        """Download file from URL using requests"""
        try:
            logger.info(f"[Job {job_id}] Downloading file from URL: {url}")
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            }
            
            response = requests.get(url, timeout=30, headers=headers)
            response.raise_for_status()
            
            logger.info(f"[Job {job_id}] File downloaded successfully, size: {len(response.content)} bytes")
            
            # Determine filename
            filename = f"{invoice_key}.xml"
            file_path = os.path.join('downloads', filename)
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            logger.info(f"[Job {job_id}] File saved to: {file_path}")
            
            return {
                'success': True,
                'file_path': file_path
            }
            
        except requests.RequestException as e:
            logger.error(f"[Job {job_id}] Request error downloading file: {e}")
            return {
                'success': False,
                'error': f'Erro ao baixar arquivo: {str(e)}'
            }
        except Exception as e:
            logger.error(f"[Job {job_id}] Unexpected error saving file: {e}")
            return {
                'success': False,
                'error': f'Erro inesperado ao salvar arquivo: {str(e)}'
            }
    
    def check_downloaded_file(self, invoice_key, job_id, download_type='xml'):
        """Check if file was downloaded by Selenium"""
        downloads_dir = 'downloads'
        
        # Wait for file to be downloaded
        max_wait = 30  # seconds
        wait_time = 0
        
        # Determine file extension based on download type
        if download_type.lower() == 'danfe':
            file_extensions = ['.pdf', '.PDF']
            new_filename = f"{invoice_key}.pdf"
        else:  # xml
            file_extensions = ['.xml', '.XML']
            new_filename = f"{invoice_key}.xml"
        
        while wait_time < max_wait:
            # Look for files that might be the downloaded file
            for filename in os.listdir(downloads_dir):
                if any(filename.endswith(ext) for ext in file_extensions) and (invoice_key in filename or any(filename.endswith(ext) for ext in file_extensions)):
                    file_path = os.path.join(downloads_dir, filename)
                    
                    # Rename file to have invoice key in name
                    new_file_path = os.path.join(downloads_dir, new_filename)
                    
                    if file_path != new_file_path:
                        os.rename(file_path, new_file_path)
                    
                    return {
                        'success': True,
                        'file_path': new_file_path
                    }
            
            time.sleep(1)
            wait_time += 1
        
        return {
            'success': False,
            'error': f'Arquivo {download_type.upper()} não foi baixado dentro do tempo limite'
        }
    
    def generate_danfe_from_xml(self, xml_file_path: str, invoice_key: str, job_id: str) -> Dict[str, Any]:
        """Generate DANFE PDF from XML file"""
        try:
            from simple_danfe import generate_simple_danfe
            
            logger.info(f"[Job {job_id}] Generating DANFE from XML: {xml_file_path}")
            
            # Read XML content
            with open(xml_file_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            # Generate PDF DANFE
            pdf_filename = f"{invoice_key}.pdf"
            pdf_path = os.path.join('downloads', pdf_filename)
            
            success = generate_simple_danfe(xml_content, pdf_path)
            
            if success:
                logger.info(f"[Job {job_id}] DANFE generated successfully: {pdf_path}")
                
                # Remove XML file if only DANFE was requested
                try:
                    os.remove(xml_file_path)
                    logger.info(f"[Job {job_id}] Temporary XML file removed: {xml_file_path}")
                except:
                    pass
                
                return {
                    'success': True,
                    'file_path': pdf_path
                }
            else:
                logger.error(f"[Job {job_id}] Failed to generate DANFE from XML")
                return {
                    'success': False,
                    'error': 'Erro ao gerar DANFE a partir do XML'
                }
                
        except Exception as e:
            logger.error(f"[Job {job_id}] Error generating DANFE: {e}")
            return {
                'success': False,
                'error': f'Erro ao gerar DANFE: {str(e)}'
            }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test if the automation system can connect to the invoice system"""
        try:
            if not self.driver:
                return {
                    'success': False,
                    'error': 'WebDriver não está disponível'
                }
            
            logger.info("Testing connection to invoice system...")
            url = "https://meudanfe.com.br/"
            
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            current_url = self.driver.current_url
            page_title = self.driver.title
            
            logger.info(f"Connection test successful - URL: {current_url}, Title: {page_title}")
            
            # Check if we can find basic elements
            try:
                inputs = self.driver.find_elements(By.TAG_NAME, "input")
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                
                logger.info(f"Found {len(inputs)} input elements and {len(buttons)} button elements")
                
                return {
                    'success': True,
                    'url': current_url,
                    'title': page_title,
                    'inputs_found': len(inputs),
                    'buttons_found': len(buttons)
                }
            except Exception as element_error:
                logger.warning(f"Could not count elements: {element_error}")
                return {
                    'success': True,
                    'url': current_url,
                    'title': page_title,
                    'inputs_found': 0,
                    'buttons_found': 0
                }
                
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {
                'success': False,
                'error': f'Erro no teste de conexão: {str(e)}'
            }
    
    def extract_xml_from_page(self, page_source: str, job_id: str) -> str:
        """Extract XML content from page source"""
        try:
            import re
            
            # Multiple patterns to find XML content
            patterns = [
                r'(<\?xml.*?</nfeProc>)',
                r'(<\?xml.*?</NFe>)',
                r'(<\?xml.*?</infNFe>)',
                r'(<nfeProc.*?</nfeProc>)',
                r'(<NFe.*?</NFe>)'
            ]
            
            for pattern in patterns:
                xml_match = re.search(pattern, page_source, re.DOTALL | re.IGNORECASE)
                if xml_match:
                    xml_content = xml_match.group(1)
                    logger.info(f"[Job {job_id}] XML content extracted using pattern: {pattern[:20]}...")
                    return xml_content
            
            # Check if page contains raw XML without proper tags
            if '<?xml' in page_source:
                logger.info(f"[Job {job_id}] Found XML marker but couldn't extract complete content")
                # Try to extract from pre or code tags
                pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', page_source, re.DOTALL | re.IGNORECASE)
                if pre_match and '<?xml' in pre_match.group(1):
                    return pre_match.group(1).strip()
                
                code_match = re.search(r'<code[^>]*>(.*?)</code>', page_source, re.DOTALL | re.IGNORECASE)
                if code_match and '<?xml' in code_match.group(1):
                    return code_match.group(1).strip()
            
            return None
            
        except Exception as e:
            logger.error(f"[Job {job_id}] Error extracting XML from page: {e}")
            return None
    
    def save_xml_file(self, xml_content: str, invoice_key: str, job_id: str) -> Dict[str, Any]:
        """Save XML content to file"""
        try:
            # Clean up XML content
            xml_content = xml_content.strip()
            
            # Ensure proper XML declaration
            if not xml_content.startswith('<?xml'):
                xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n' + xml_content
            
            # Create downloads directory
            downloads_dir = 'downloads'
            os.makedirs(downloads_dir, exist_ok=True)
            
            # Generate filename
            filename = f"{invoice_key}.xml"
            file_path = os.path.join(downloads_dir, filename)
            
            # Save the file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            file_size = os.path.getsize(file_path)
            logger.info(f"[Job {job_id}] XML file saved: {file_path} ({file_size} bytes)")
            
            return {
                'success': True,
                'file_path': file_path,
                'filename': filename,
                'size': file_size
            }
            
        except Exception as e:
            logger.error(f"[Job {job_id}] Error saving XML file: {e}")
            return {
                'success': False,
                'error': f'Erro ao salvar arquivo XML: {str(e)}'
            }

    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {str(e)}")
