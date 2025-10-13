#!/usr/bin/env python3
"""
Check what the download buttons actually do
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

def setup_chrome():
    """Setup Chrome with anti-detection"""
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def main():
    driver = None
    invoice_key = "42250485179240000239550020004175361171503396"
    
    try:
        logger.info("🌐 Setting up Chrome...")
        driver = setup_chrome()
        
        logger.info(f"🌐 Navigating to meudanfe.com.br...")
        driver.get("https://meudanfe.com.br/")
        time.sleep(3)
        
        logger.info(f"⌨️ Entering invoice key and searching...")
        input_field = driver.find_element(By.ID, 'searchTxt')
        input_field.clear()
        input_field.send_keys(invoice_key)
        time.sleep(1)
        
        search_btn = driver.find_element(By.ID, 'searchBtn')
        search_btn.click()
        logger.info("✅ Search button clicked")
        
        logger.info("⏳ Waiting 20 seconds for results...")
        time.sleep(20)
        
        # Get button details
        logger.info("\n" + "=" * 70)
        logger.info("BUTTON DETAILS")
        logger.info("=" * 70)
        
        xml_btn = driver.find_element(By.ID, 'downloadXmlBtn')
        danfe_btn = driver.find_element(By.ID, 'downloadDanfeBtn')
        
        logger.info(f"\n📄 XML Button:")
        logger.info(f"   Tag: {xml_btn.tag_name}")
        logger.info(f"   Href: {xml_btn.get_attribute('href')}")
        logger.info(f"   Onclick: {xml_btn.get_attribute('onclick')}")
        logger.info(f"   Download attr: {xml_btn.get_attribute('download')}")
        
        # Check for any data attributes
        logger.info(f"   Data attributes:")
        attrs = driver.execute_script(
            "var items = {}; "
            "for (index = 0; index < arguments[0].attributes.length; ++index) { "
            "    items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value "
            "}; "
            "return items;", xml_btn
        )
        for key, value in attrs.items():
            if 'data-' in key or 'download' in key.lower():
                logger.info(f"     {key}: {value}")
        
        logger.info(f"\n📄 DANFE Button:")
        logger.info(f"   Tag: {danfe_btn.tag_name}")
        logger.info(f"   Href: {danfe_btn.get_attribute('href')}")
        logger.info(f"   Onclick: {danfe_btn.get_attribute('onclick')}")
        logger.info(f"   Download attr: {danfe_btn.get_attribute('download')}")
        
        # Check for any data attributes
        logger.info(f"   Data attributes:")
        attrs = driver.execute_script(
            "var items = {}; "
            "for (index = 0; index < arguments[0].attributes.length; ++index) { "
            "    items[arguments[0].attributes[index].name] = arguments[0].attributes[index].value "
            "}; "
            "return items;", danfe_btn
        )
        for key, value in attrs.items():
            if 'data-' in key or 'download' in key.lower():
                logger.info(f"     {key}: {value}")
        
        logger.info("\n" + "=" * 70)
        logger.info("🏁 COMPLETE")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    main()
