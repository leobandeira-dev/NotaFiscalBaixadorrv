import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
import requests
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class InvoiceDownloader:
    def __init__(self):
        self.driver = None
        self.setup_driver()
    
    def setup_driver(self):
        """Setup Chrome WebDriver with appropriate options"""
        try:
            chrome_options = Options()
            chrome_options.add_argument('--headless')  # Run in background
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
            
            # Download preferences
            download_dir = os.path.abspath('downloads')
            prefs = {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            
            logger.info("Chrome WebDriver initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup Chrome WebDriver: {str(e)}")
            raise
    
    def download_invoice_xml(self, invoice_key, job_id):
        """Download XML for a specific invoice key from meudanfe.com.br"""
        try:
            logger.info(f"Starting download for invoice key: {invoice_key}")
            
            # Navigate to the website
            url = "https://meudanfe.com.br/"
            self.driver.get(url)
            
            # Wait for page to load
            WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Look for input field for invoice key
            # This is a generic approach - the actual selectors may need to be adjusted
            # based on the real website structure
            
            # Try different possible selectors for the invoice key input
            input_selectors = [
                'input[name*="chave"]',
                'input[id*="chave"]',
                'input[placeholder*="chave"]',
                'input[type="text"]',
                'input[name*="key"]',
                'input[id*="key"]'
            ]
            
            input_element = None
            for selector in input_selectors:
                try:
                    input_element = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                    logger.info(f"Found input element with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if not input_element:
                # If no specific input found, try to find any text input
                try:
                    input_element = WebDriverWait(self.driver, 10).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type="text"]'))
                    )
                except TimeoutException:
                    return {
                        'success': False,
                        'error': 'Campo de entrada para chave da nota fiscal não encontrado'
                    }
            
            # Clear and enter the invoice key
            input_element.clear()
            input_element.send_keys(invoice_key)
            
            # Look for submit button
            submit_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:contains("Buscar")',
                'button:contains("Consultar")',
                'button:contains("Download")',
                '.btn-primary',
                '.btn-success',
                'button'
            ]
            
            submit_button = None
            for selector in submit_selectors:
                try:
                    if ':contains(' in selector:
                        # Handle text-based selectors differently
                        buttons = self.driver.find_elements(By.TAG_NAME, "button")
                        for btn in buttons:
                            if any(text in btn.text.lower() for text in ['buscar', 'consultar', 'download', 'enviar']):
                                submit_button = btn
                                break
                        if submit_button:
                            break
                    else:
                        submit_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        break
                except TimeoutException:
                    continue
            
            if not submit_button:
                return {
                    'success': False,
                    'error': 'Botão de envio não encontrado'
                }
            
            # Click submit button
            submit_button.click()
            
            # Wait for response/results page
            time.sleep(3)
            
            # Look for download link or XML content
            download_selectors = [
                'a[href*=".xml"]',
                'a:contains("XML")',
                'a:contains("Download")',
                'a[download]',
                '.download-link',
                '.xml-link'
            ]
            
            download_link = None
            for selector in download_selectors:
                try:
                    if ':contains(' in selector:
                        links = self.driver.find_elements(By.TAG_NAME, "a")
                        for link in links:
                            if 'xml' in link.text.lower() or 'download' in link.text.lower():
                                download_link = link
                                break
                        if download_link:
                            break
                    else:
                        download_link = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                        )
                        break
                except TimeoutException:
                    continue
            
            if download_link:
                # Get the download URL
                download_url = download_link.get_attribute('href')
                
                if download_url:
                    # Download the file using requests
                    return self.download_file(download_url, invoice_key, job_id)
                else:
                    # Click the download link
                    download_link.click()
                    time.sleep(5)
                    
                    # Check if file was downloaded
                    return self.check_downloaded_file(invoice_key, job_id)
            
            # If no download link found, check if XML content is displayed on page
            try:
                xml_content = self.driver.find_element(By.TAG_NAME, "pre").text
                if xml_content and xml_content.strip().startswith('<?xml'):
                    # Save XML content to file
                    filename = f"{invoice_key}.xml"
                    file_path = os.path.join('downloads', filename)
                    
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(xml_content)
                    
                    return {
                        'success': True,
                        'file_path': file_path
                    }
            except:
                pass
            
            return {
                'success': False,
                'error': 'XML não encontrado ou link de download não disponível'
            }
            
        except TimeoutException:
            return {
                'success': False,
                'error': 'Timeout aguardando resposta do site'
            }
        except WebDriverException as e:
            return {
                'success': False,
                'error': f'Erro do WebDriver: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Unexpected error downloading {invoice_key}: {str(e)}")
            return {
                'success': False,
                'error': f'Erro inesperado: {str(e)}'
            }
    
    def download_file(self, url, invoice_key, job_id):
        """Download file from URL using requests"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Determine filename
            filename = f"{invoice_key}.xml"
            file_path = os.path.join('downloads', filename)
            
            # Save file
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            return {
                'success': True,
                'file_path': file_path
            }
            
        except requests.RequestException as e:
            return {
                'success': False,
                'error': f'Erro ao baixar arquivo: {str(e)}'
            }
        except Exception as e:
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
    
    def cleanup(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver closed successfully")
            except Exception as e:
                logger.error(f"Error closing WebDriver: {str(e)}")
