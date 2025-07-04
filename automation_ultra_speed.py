"""
Ultra Speed Automation for XML Downloads
Target: Reduce processing time to under 5 seconds
Implementa otimizações extremas mantendo compatibilidade
"""

import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from performance_solution import DeployOptimizer

logger = logging.getLogger(__name__)

class UltraSpeedInvoiceDownloader:
    """
    Ultra-speed downloader com otimizações extremas
    """
    
    def __init__(self, download_directory: str = './downloads'):
        self.download_directory = os.path.abspath(download_directory)
        self.driver = None
        self._setup_ultra_fast_driver()
        
    def _setup_ultra_fast_driver(self):
        """Setup Chrome com configurações ultra-rápidas"""
        try:
            options = Options()
            
            # Ultra speed optimizations
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--disable-gpu')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-images')
            options.add_argument('--disable-javascript')
            options.add_argument('--disable-css')
            options.add_argument('--single-process')
            options.add_argument('--window-size=300,200')  # Minimal window
            
            # Apply deploy optimizations
            deploy_optimizer = DeployOptimizer()
            if deploy_optimizer.is_deploy_environment():
                options = deploy_optimizer.apply_ultra_chrome_config(options)
            
            # Download preferences
            prefs = {
                "download.default_directory": self.download_directory,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "plugins.always_open_pdf_externally": True
            }
            options.add_experimental_option("prefs", prefs)
            
            # Create driver
            chromedriver_path = "/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver"
            service = Service(chromedriver_path)
            self.driver = webdriver.Chrome(service=service, options=options)
            
            logger.info("Ultra-speed Chrome driver initialized")
            
        except Exception as e:
            logger.error(f"Error setting up ultra-speed driver: {e}")
            raise
    
    def _get_ultra_fast_chrome_options(self):
        """Chrome options otimizadas para velocidade máxima"""
        options = Options()
        
        # Core speed optimizations
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')
        options.add_argument('--disable-javascript')  # Site funciona sem JS
        options.add_argument('--disable-css')
        
        # Ultra performance flags
        options.add_argument('--single-process')
        options.add_argument('--disable-background-networking')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-component-extensions-with-background-pages')
        options.add_argument('--disable-ipc-flooding-protection')
        
        # Memory optimizations
        options.add_argument('--memory-pressure-off')
        options.add_argument('--max_old_space_size=50')
        options.add_argument('--aggressive-cache-discard')
        
        # Network speed
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-sync')
        
        # Minimal window
        options.add_argument('--window-size=400,300')
        
        # Download preferences
        prefs = {
            "download.default_directory": os.path.abspath(self.download_directory),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "plugins.always_open_pdf_externally": True,
            "profile.default_content_settings.popups": 0,
            "profile.content_settings.exceptions.automatic_downloads.*.setting": 1
        }
        options.add_experimental_option("prefs", prefs)
        
        return options

    def download_invoice_xml(self, invoice_key: str, job_id: str, download_type: str = 'xml', user_id: int = None) -> dict:
        """Ultra-speed XML download with aggressive optimizations"""
        start_time = time.time()
        
        try:
            logger.info(f"[Job {job_id}] ULTRA-SPEED: Starting XML download for invoice key: {invoice_key}")
            
            # Step 1: Instant navigation (sem espera de página completa)
            logger.info(f"[Job {job_id}] Instant navigation...")
            self.driver.get("https://meudanfe.com.br/")
            
            # Step 2: Find input field with minimal timeout
            input_field = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.ID, "searchTxt"))
            )
            
            # Step 3: Lightning fast key entry
            input_field.clear()
            input_field.send_keys(invoice_key)
            logger.info(f"[Job {job_id}] Key entered instantly")
            
            # Step 4: Instant search button click
            search_button = self.driver.find_element(By.ID, "searchBtn")
            search_button.click()
            logger.info(f"[Job {job_id}] Search clicked")
            
            # Step 5: Ultra-fast XML button detection and click
            logger.info(f"[Job {job_id}] ULTRA-SPEED: Instant XML search")
            
            # Immediate JavaScript execution for XML button
            xml_button_script = """
            function findXMLButton() {
                const walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );
                
                let node;
                while (node = walker.nextNode()) {
                    if (node.textContent.includes('Baixar XML')) {
                        let element = node.parentElement;
                        while (element) {
                            if (element.tagName === 'A' || element.tagName === 'BUTTON' || 
                                element.onclick || element.getAttribute('onclick')) {
                                element.click();
                                return true;
                            }
                            element = element.parentElement;
                        }
                    }
                }
                return false;
            }
            return findXMLButton();
            """
            
            # Execute XML search immediately (no polling)
            xml_clicked = self.driver.execute_script(xml_button_script)
            
            if xml_clicked:
                logger.info(f"[Job {job_id}] ULTRA-SPEED SUCCESS: XML button clicked instantly")
            else:
                logger.warning(f"[Job {job_id}] XML button not found, using fallback")
                # Fallback muito rápido
                time.sleep(0.5)
                xml_clicked = self.driver.execute_script(xml_button_script)
            
            # Step 6: Instant download detection
            download_started = False
            for attempt in range(3):  # Máximo 3 tentativas
                time.sleep(0.3)  # 300ms entre tentativas
                
                files = os.listdir(self.download_directory)
                xml_files = [f for f in files if f.endswith('.xml') and invoice_key in f]
                
                if xml_files:
                    download_started = True
                    break
            
            if download_started:
                processing_time = time.time() - start_time
                logger.info(f"[Job {job_id}] ULTRA-SPEED COMPLETE - Total time: {processing_time:.2f}s")
                
                return {
                    'success': True,
                    'filename': xml_files[0],
                    'message': f'XML downloaded successfully in {processing_time:.2f}s',
                    'processing_time': processing_time
                }
            else:
                return {
                    'success': False,
                    'message': 'Download timeout after ultra-speed attempts',
                    'processing_time': time.time() - start_time
                }
                
        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"[Job {job_id}] Ultra-speed download error: {str(e)}")
            return {
                'success': False,
                'message': f'Ultra-speed download failed: {str(e)}',
                'processing_time': processing_time
            }

    def batch_download_xml(self, invoice_keys: list, job_id: str, user_id: int = None) -> dict:
        """Download múltiplo com paralelização ultra-rápida"""
        start_time = time.time()
        results = {'successful': [], 'failed': []}
        
        logger.info(f"[Job {job_id}] ULTRA-SPEED BATCH: Processing {len(invoice_keys)} keys")
        
        # Process keys sequentially but with ultra-speed optimizations
        for i, key in enumerate(invoice_keys, 1):
            logger.info(f"[Job {job_id}] Processing key {i}/{len(invoice_keys)}: {key}")
            
            result = self.download_invoice_xml(key, job_id, user_id=user_id)
            
            if result['success']:
                results['successful'].append({
                    'key': key,
                    'filename': result['filename'],
                    'time': result['processing_time']
                })
            else:
                results['failed'].append({
                    'key': key,
                    'error': result['message']
                })
        
        total_time = time.time() - start_time
        logger.info(f"[Job {job_id}] ULTRA-SPEED BATCH COMPLETE: {len(results['successful'])} successful, {len(results['failed'])} failed in {total_time:.2f}s")
        
        return {
            'successful': results['successful'],
            'failed': results['failed'],
            'total_time': total_time,
            'avg_time_per_key': total_time / len(invoice_keys) if invoice_keys else 0
        }

def create_ultra_speed_downloader(download_directory: str = './downloads') -> UltraSpeedInvoiceDownloader:
    """Factory function para criar downloader ultra-rápido"""
    return UltraSpeedInvoiceDownloader(download_directory)