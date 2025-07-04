#!/usr/bin/env python3
"""
Simple test to debug the new layout issue
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_simple():
    """Simple test to understand the new layout"""
    
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    driver = None
    try:
        driver = webdriver.Chrome(options=chrome_options)
        logger.info("Chrome initialized")
        
        # Navigate to the site
        driver.get("https://meudanfe.com.br/")
        logger.info(f"Loaded page: {driver.current_url}")
        
        # Wait a bit for page to load
        time.sleep(3)
        
        # Try to find input field
        try:
            input_field = driver.find_element(By.CSS_SELECTOR, "input[type='text']")
            logger.info(f"Found input field: {input_field}")
            
            # Enter test key
            input_field.clear()
            input_field.send_keys("35250513516247000107550010000113401146202508")
            logger.info("Entered test key")
            
            # Try to find BUSCAR button
            time.sleep(2)
            try:
                buscar_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'BUSCAR')]")
                logger.info(f"Found BUSCAR button: {buscar_btn}")
                
                # Click it
                buscar_btn.click()
                logger.info("Clicked BUSCAR button")
                
                # Wait for results
                time.sleep(5)
                
                # Check page content
                page_source = driver.page_source
                if "XML" in page_source:
                    logger.info("✅ XML text found on results page")
                else:
                    logger.info("❌ XML text NOT found on results page")
                    
                # Try to find any buttons
                buttons = driver.find_elements(By.TAG_NAME, "button")
                logger.info(f"Found {len(buttons)} buttons on results page")
                for i, btn in enumerate(buttons):
                    try:
                        text = btn.text
                        if text:
                            logger.info(f"Button {i+1}: '{text}'")
                    except:
                        pass
                        
            except Exception as e:
                logger.error(f"Error with BUSCAR button: {e}")
                
        except Exception as e:
            logger.error(f"Error finding input field: {e}")
            
        # Print page title and URL for debugging
        logger.info(f"Final URL: {driver.current_url}")
        logger.info(f"Page title: {driver.title}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    test_simple()