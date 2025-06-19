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
    
    def download_invoice_xml(self, invoice_key: str, job_id: str) -> Dict[str, Any]:
        """Download XML for a specific invoice key from meudanfe.com.br"""
        try:
            logger.info(f"[Job {job_id}] Starting download for invoice key: {invoice_key}")
            
            # Check if driver is available
            if not self.driver:
                return {
                    'success': False,
                    'error': 'WebDriver não está disponível'
                }
            
            # Navigate to the website
            url = "https://meudanfe.com.br/"
            logger.info(f"[Job {job_id}] Navigating to: {url}")
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
                'button:contains("Buscar DANFE/XML")',
                'button:contains("Buscar")',
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
            
            # Look for download link or XML content
            logger.info(f"[Job {job_id}] Looking for download links...")
            download_selectors = [
                'a[href*=".xml"]',
                'a[href*="download"]',
                'a[download]',
                '.download-link',
                '.xml-link',
                'a[href*="arquivo"]',
                'a[href*="file"]'
            ]
            
            download_link = None
            for i, selector in enumerate(download_selectors):
                try:
                    logger.debug(f"[Job {job_id}] Trying download selector {i+1}/{len(download_selectors)}: {selector}")
                    download_link = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"[Job {job_id}] Found download link with selector: {selector}")
                    break
                except TimeoutException:
                    logger.debug(f"[Job {job_id}] Download selector {selector} not found")
                    continue
            
            # Also try to find links by text content
            if not download_link:
                logger.info(f"[Job {job_id}] Trying to find download link by text content...")
                try:
                    links = self.driver.find_elements(By.TAG_NAME, "a")
                    logger.info(f"[Job {job_id}] Found {len(links)} link elements")
                    for idx, link in enumerate(links):
                        try:
                            link_text = link.text.lower().strip()
                            link_href = link.get_attribute('href') or ''
                            logger.debug(f"[Job {job_id}] Link {idx+1}: text='{link_text}', href='{link_href[:100]}'")
                            if ('xml' in link_text or 'download' in link_text or 'baixar' in link_text or 
                                '.xml' in link_href or 'download' in link_href):
                                download_link = link
                                logger.info(f"[Job {job_id}] Found download link by content: text='{link_text}', href='{link_href[:100]}'")
                                break
                        except:
                            logger.warning(f"[Job {job_id}] Could not inspect link {idx+1}")
                except Exception as e:
                    logger.error(f"[Job {job_id}] Error finding links by text: {e}")
            
            if download_link:
                # Get the download URL
                download_url = download_link.get_attribute('href')
                logger.info(f"[Job {job_id}] Found download URL: {download_url}")
                
                if download_url and download_url.startswith('http'):
                    # Download the file using requests
                    logger.info(f"[Job {job_id}] Downloading file via requests...")
                    return self.download_file(download_url, invoice_key, job_id)
                else:
                    # Click the download link
                    logger.info(f"[Job {job_id}] Clicking download link...")
                    download_link.click()
                    time.sleep(8)  # Wait longer for download
                    
                    # Check if file was downloaded
                    return self.check_downloaded_file(invoice_key, job_id)
            
            # If no download link found, check if XML content is displayed on page
            logger.info(f"[Job {job_id}] Looking for XML content displayed on page...")
            try:
                # Look for XML in various containers
                xml_containers = ['pre', 'code', 'textarea', 'div.xml', '.xml-content']
                xml_content = None
                
                for container in xml_containers:
                    try:
                        element = self.driver.find_element(By.CSS_SELECTOR, container)
                        content = element.text.strip()
                        if content and ('<?xml' in content or '<nfeProc' in content or '<NFe' in content):
                            xml_content = content
                            logger.info(f"[Job {job_id}] Found XML content in {container} element")
                            break
                    except:
                        continue
                
                if xml_content:
                    # Save XML content to file
                    filename = f"{invoice_key}.xml"
                    file_path = os.path.join('downloads', filename)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(xml_content)
                    
                    logger.info(f"[Job {job_id}] XML content saved to file: {file_path}")
                    return {
                        'success': True,
                        'file_path': file_path
                    }
            except Exception as e:
                logger.error(f"[Job {job_id}] Error checking for XML content: {e}")
            
            logger.warning(f"[Job {job_id}] No XML found for invoice key: {invoice_key}")
            return {
                'success': False,
                'error': 'XML não encontrado ou link de download não disponível'
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
    
    def check_downloaded_file(self, invoice_key, job_id):
        """Check if file was downloaded by Selenium"""
        downloads_dir = 'downloads'
        
        # Wait for file to be downloaded
        max_wait = 30  # seconds
        wait_time = 0
        
        while wait_time < max_wait:
            # Look for files that might be the downloaded XML
            for filename in os.listdir(downloads_dir):
                if filename.endswith('.xml') and (invoice_key in filename or filename.endswith('.xml')):
                    file_path = os.path.join(downloads_dir, filename)
                    
                    # Rename file to have invoice key in name
                    new_filename = f"{invoice_key}.xml"
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
            'error': 'Arquivo XML não foi baixado dentro do tempo limite'
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """Test if the automation system can connect to meudanfe.com.br"""
        try:
            if not self.driver:
                return {
                    'success': False,
                    'error': 'WebDriver não está disponível'
                }
            
            logger.info("Testing connection to meudanfe.com.br...")
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
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {str(e)}")
