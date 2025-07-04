"""
Speed-Optimized Automation for XML Downloads
Bypasses conventional selectors and goes directly to text search strategy
Target: Reduce processing time from 57s to under 30s
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
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from automation_fixed import InvoiceDownloader

logger = logging.getLogger(__name__)

class SpeedOptimizedInvoiceDownloader(InvoiceDownloader):
    """
    Speed-optimized version of InvoiceDownloader
    Skips conventional selectors and uses direct text search
    """
    
    def download_invoice_xml(self, invoice_key: str, job_id: str, download_type: str = 'xml', user_id: int = None) -> dict:
        """Speed-optimized XML download with direct text search strategy"""
        try:
            logger.info(f"[Job {job_id}] SPEED-OPTIMIZED: Starting XML download for invoice key: {invoice_key}")
            
            # Step 1: Navigate to page (faster loading)
            logger.info(f"[Job {job_id}] Navigating to invoice system...")
            self.driver.get("https://meudanfe.com.br/")
            
            # Step 2: Ultra-fast page load check (reduced timeout)
            WebDriverWait(self.driver, 3).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            
            # Step 3: Find and fill input field (ultra-fast)
            logger.info(f"[Job {job_id}] Looking for input field...")
            input_field = WebDriverWait(self.driver, 2).until(
                EC.presence_of_element_located((By.ID, "searchTxt"))
            )
            
            input_field.clear()
            input_field.send_keys(invoice_key)
            logger.info(f"[Job {job_id}] Invoice key entered")
            
            # Step 4: Find and click search button (ultra-fast)
            search_button = WebDriverWait(self.driver, 2).until(
                EC.element_to_be_clickable((By.ID, "searchBtn"))
            )
            search_button.click()
            logger.info(f"[Job {job_id}] Search button clicked")
            
            # Step 5: Minimal wait for results
            time.sleep(1)  # Ultra reduced wait
            
            # Step 6: IMMEDIATE TEXT SEARCH STRATEGY (skip conventional selectors)
            logger.info(f"[Job {job_id}] SPEED MODE: Using immediate text search for 'Baixar XML'")
            
            # Fast browser search
            actions = ActionChains(self.driver)
            actions.key_down(Keys.CONTROL).send_keys('f').key_up(Keys.CONTROL).perform()
            time.sleep(0.2)  # Minimal wait
            
            actions.send_keys('Baixar XML').perform()
            time.sleep(0.2)
            
            actions.send_keys(Keys.ENTER).perform()
            time.sleep(0.2)
            
            actions.send_keys(Keys.ESCAPE).perform()
            time.sleep(0.1)
            
            # Step 7: Direct JavaScript click via TreeWalker
            result = self.driver.execute_script("""
                // Force options div visible
                var optionsDiv = document.getElementById('optionsDiv');
                if (optionsDiv) {
                    optionsDiv.style.display = 'block';
                    optionsDiv.style.visibility = 'visible';
                }
                
                // Immediate TreeWalker search for "Baixar XML"
                var walker = document.createTreeWalker(
                    document.body,
                    NodeFilter.SHOW_TEXT,
                    null,
                    false
                );
                
                var textNode;
                while (textNode = walker.nextNode()) {
                    if (textNode.textContent.trim() === 'Baixar XML') {
                        var element = textNode.parentNode;
                        // Find clickable parent
                        while (element && element !== document.body) {
                            if (element.tagName === 'BUTTON' || element.tagName === 'A' || 
                                element.onclick || element.getAttribute('onclick') ||
                                element.style.cursor === 'pointer') {
                                element.click();
                                return 'XML button clicked via optimized TreeWalker';
                            }
                            element = element.parentNode;
                        }
                    }
                }
                
                // Fallback: Quick clickable element search
                var clickables = document.querySelectorAll('button, a, *[onclick]');
                for (var i = 0; i < clickables.length; i++) {
                    var elem = clickables[i];
                    if ((elem.textContent || '').trim() === 'Baixar XML') {
                        elem.click();
                        return 'XML button clicked via fallback search';
                    }
                }
                
                return 'No XML button found';
            """)
            
            if 'clicked' in result.lower():
                logger.info(f"[Job {job_id}] SPEED SUCCESS: {result}")
                
                # Step 8: Ultra-fast file verification
                time.sleep(0.5)  # Ultra minimal wait for download
                
                # Check for downloaded file
                downloaded_file = self.check_downloaded_file(invoice_key, job_id)
                if downloaded_file['success']:
                    logger.info(f"[Job {job_id}] SPEED OPTIMIZATION SUCCESSFUL - File downloaded")
                    return downloaded_file
                
                # Alternative: Check for XML in page source
                try:
                    page_source = self.driver.page_source
                    xml_content = self.extract_xml_from_page(page_source)
                    if xml_content and len(xml_content) > 100:
                        logger.info(f"[Job {job_id}] SPEED SUCCESS - XML extracted from page")
                        save_result = self.save_xml_content(xml_content, invoice_key, job_id, user_id)
                        if save_result['success']:
                            return save_result
                except Exception as e:
                    logger.info(f"[Job {job_id}] Page extraction failed: {e}")
            
            # If speed optimization fails, fall back to original method
            logger.info(f"[Job {job_id}] Speed optimization failed, falling back to original method")
            return super().download_invoice_xml(invoice_key, job_id, download_type, user_id)
            
        except Exception as e:
            logger.error(f"[Job {job_id}] Speed-optimized download failed: {e}")
            # Fall back to original method
            return super().download_invoice_xml(invoice_key, job_id, download_type, user_id)

# Function to replace the original downloader in download_service.py
def get_speed_optimized_downloader():
    """Returns speed-optimized downloader instance"""
    return SpeedOptimizedInvoiceDownloader()