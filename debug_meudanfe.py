#!/usr/bin/env python3
"""
Debug script to analyze meudanfe.com.br website structure
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
    """Setup Chrome WebDriver"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1280,720')
    
    # Get chromedriver path
    result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
    chromedriver_path = result.stdout.strip()
    
    service = Service(executable_path=chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def analyze_website():
    """Analyze the website structure"""
    driver = setup_driver()
    
    try:
        logger.info("Navigating to meudanfe.com.br...")
        driver.get("https://meudanfe.com.br/")
        
        # Wait for page load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        logger.info(f"Page title: {driver.title}")
        logger.info(f"Current URL: {driver.current_url}")
        
        # Find all input elements
        inputs = driver.find_elements(By.TAG_NAME, "input")
        logger.info(f"Found {len(inputs)} input elements:")
        
        for i, inp in enumerate(inputs):
            try:
                tag_name = inp.tag_name
                input_type = inp.get_attribute('type') or 'none'
                name = inp.get_attribute('name') or 'none'
                id_attr = inp.get_attribute('id') or 'none'
                placeholder = inp.get_attribute('placeholder') or 'none'
                class_attr = inp.get_attribute('class') or 'none'
                
                logger.info(f"Input {i+1}: type={input_type}, name={name}, id={id_attr}, placeholder={placeholder}, class={class_attr}")
            except Exception as e:
                logger.warning(f"Could not inspect input {i+1}: {e}")
        
        # Find all textareas
        textareas = driver.find_elements(By.TAG_NAME, "textarea")
        logger.info(f"Found {len(textareas)} textarea elements:")
        
        for i, textarea in enumerate(textareas):
            try:
                name = textarea.get_attribute('name') or 'none'
                id_attr = textarea.get_attribute('id') or 'none'
                placeholder = textarea.get_attribute('placeholder') or 'none'
                class_attr = textarea.get_attribute('class') or 'none'
                
                logger.info(f"Textarea {i+1}: name={name}, id={id_attr}, placeholder={placeholder}, class={class_attr}")
            except Exception as e:
                logger.warning(f"Could not inspect textarea {i+1}: {e}")
        
        # Find all buttons
        buttons = driver.find_elements(By.TAG_NAME, "button")
        logger.info(f"Found {len(buttons)} button elements:")
        
        for i, btn in enumerate(buttons):
            try:
                btn_type = btn.get_attribute('type') or 'none'
                btn_text = btn.text.strip() or 'no-text'
                class_attr = btn.get_attribute('class') or 'none'
                
                logger.info(f"Button {i+1}: type={btn_type}, text='{btn_text}', class={class_attr}")
            except Exception as e:
                logger.warning(f"Could not inspect button {i+1}: {e}")
        
        # Look for any elements with specific text or attributes related to invoice keys
        logger.info("Looking for elements containing 'chave', 'nfe', 'danfe', 'consulta'...")
        
        # Check all elements for relevant text
        all_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'chave') or contains(text(), 'NFe') or contains(text(), 'consulta')]")
        logger.info(f"Found {len(all_elements)} elements with relevant text")
        
        for i, elem in enumerate(all_elements[:10]):  # Limit to first 10
            try:
                tag = elem.tag_name
                text = elem.text.strip()[:100]  # First 100 chars
                logger.info(f"Relevant element {i+1}: <{tag}> '{text}'")
            except Exception as e:
                logger.warning(f"Could not inspect relevant element {i+1}: {e}")
        
        # Save page source for analysis
        page_source = driver.page_source
        logger.info(f"Page source length: {len(page_source)} characters")
        
        # Save to file for manual inspection
        with open('meudanfe_page_source.html', 'w', encoding='utf-8') as f:
            f.write(page_source)
        logger.info("Page source saved to meudanfe_page_source.html")
        
    except Exception as e:
        logger.error(f"Error analyzing website: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    analyze_website()