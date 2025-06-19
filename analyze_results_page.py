#!/usr/bin/env python3
"""
Analyze the meudanfe.com.br results page structure to understand XML download process
"""

import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import subprocess

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1280,720')
    
    result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
    chromedriver_path = result.stdout.strip()
    
    service = Service(executable_path=chromedriver_path)
    return webdriver.Chrome(service=service, options=chrome_options)

def test_invoice_search():
    driver = setup_driver()
    
    try:
        # Navigate to main page
        logger.info("Navigating to meudanfe.com.br...")
        driver.get("https://meudanfe.com.br/")
        
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        # Find and fill invoice key input
        logger.info("Looking for invoice key input...")
        input_element = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[placeholder="Digite a CHAVE DE ACESSO"]'))
        )
        
        test_key = "35250162954987000130550020001854371034511150"
        input_element.clear()
        input_element.send_keys(test_key)
        logger.info(f"Entered test key: {test_key}")
        
        # Find and click submit button
        logger.info("Looking for submit button...")
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))
        )
        logger.info("Clicking submit button...")
        submit_button.click()
        
        # Wait for results page
        logger.info("Waiting for results page...")
        WebDriverWait(driver, 15).until(
            lambda d: d.current_url != "https://meudanfe.com.br/"
        )
        
        current_url = driver.current_url
        page_title = driver.title
        logger.info(f"Results page - URL: {current_url}, Title: {page_title}")
        
        # Wait a bit more for content to load
        import time
        time.sleep(5)
        
        # Analyze the results page
        logger.info("Analyzing results page content...")
        
        # Look for download links
        download_links = driver.find_elements(By.CSS_SELECTOR, 'a[href*="download"], a[href*=".xml"], a[download]')
        logger.info(f"Found {len(download_links)} potential download links")
        
        for i, link in enumerate(download_links):
            try:
                href = link.get_attribute('href') or 'no-href'
                text = link.text.strip() or 'no-text'
                logger.info(f"Download link {i+1}: href='{href}', text='{text}'")
            except:
                logger.warning(f"Could not inspect download link {i+1}")
        
        # Look for XML content in various containers
        xml_containers = ['pre', 'code', 'textarea', 'div', 'span']
        logger.info("Looking for XML content in page...")
        
        for container in xml_containers:
            try:
                elements = driver.find_elements(By.TAG_NAME, container)
                for i, elem in enumerate(elements):
                    try:
                        content = elem.text.strip()
                        if content and ('<?xml' in content or '<nfeProc' in content or '<NFe' in content):
                            logger.info(f"Found XML content in {container} element {i+1} (length: {len(content)})")
                            # Save first 500 chars for inspection
                            logger.info(f"XML preview: {content[:500]}...")
                            return content
                    except:
                        continue
            except:
                continue
        
        # Look for error messages or status indicators
        logger.info("Looking for error messages or status indicators...")
        error_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'erro') or contains(text(), 'inválid') or contains(text(), 'não encontrad')]")
        for elem in error_elements:
            try:
                text = elem.text.strip()
                if text:
                    logger.info(f"Status/Error message: {text}")
            except:
                continue
        
        # Check for any form of content that might indicate success or failure
        body_text = driver.find_element(By.TAG_NAME, "body").text
        logger.info(f"Page body text length: {len(body_text)} characters")
        
        # Save page source for detailed analysis
        page_source = driver.page_source
        with open('results_page_source.html', 'w', encoding='utf-8') as f:
            f.write(page_source)
        logger.info("Results page source saved to results_page_source.html")
        
        # Look for any buttons or links that might trigger XML download
        all_buttons = driver.find_elements(By.TAG_NAME, "button")
        logger.info(f"Found {len(all_buttons)} buttons on results page")
        
        for i, btn in enumerate(all_buttons):
            try:
                btn_text = btn.text.strip()
                btn_type = btn.get_attribute('type') or 'none'
                if btn_text:
                    logger.info(f"Button {i+1}: type='{btn_type}', text='{btn_text}'")
            except:
                continue
        
        return None
        
    except Exception as e:
        logger.error(f"Error during invoice search test: {e}")
        return None
    finally:
        driver.quit()

if __name__ == "__main__":
    test_invoice_search()