#!/usr/bin/env python3
"""
Advanced diagnostic script to understand why download buttons aren't found
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

def check_iframes(driver):
    """Check if there are any iframes on the page"""
    iframes = driver.find_elements(By.TAG_NAME, 'iframe')
    logger.info(f"📦 Found {len(iframes)} iframe(s) on the page")
    
    for i, iframe in enumerate(iframes):
        logger.info(f"   Iframe {i+1}: id='{iframe.get_attribute('id')}' src='{iframe.get_attribute('src')}'")
    
    return iframes

def check_button_by_id(driver, button_id):
    """Check button existence and properties"""
    logger.info(f"\n🔍 Checking button: #{button_id}")
    
    try:
        # Try to find by ID
        button = driver.find_element(By.ID, button_id)
        logger.info(f"   ✅ Button FOUND by ID")
        
        # Check properties
        is_displayed = button.is_displayed()
        is_enabled = button.is_enabled()
        tag_name = button.tag_name
        classes = button.get_attribute('class')
        style = button.get_attribute('style')
        href = button.get_attribute('href')
        
        logger.info(f"   Tag: {tag_name}")
        logger.info(f"   Displayed: {is_displayed}")
        logger.info(f"   Enabled: {is_enabled}")
        logger.info(f"   Classes: {classes}")
        logger.info(f"   Style: {style}")
        logger.info(f"   Href: {href}")
        
        # Try to get computed style via JavaScript
        computed_display = driver.execute_script(
            "return window.getComputedStyle(arguments[0]).display;", button
        )
        computed_visibility = driver.execute_script(
            "return window.getComputedStyle(arguments[0]).visibility;", button
        )
        logger.info(f"   Computed display: {computed_display}")
        logger.info(f"   Computed visibility: {computed_visibility}")
        
        return True, button
        
    except Exception as e:
        logger.error(f"   ❌ Button NOT found: {e}")
        return False, None

def search_all_elements_with_download(driver):
    """Search for ANY element containing 'download' in class or id"""
    logger.info("\n🔎 Searching for ALL elements with 'download' in id/class...")
    
    script = """
    var elements = document.querySelectorAll('[id*="download"], [class*="download"]');
    var results = [];
    elements.forEach(function(el) {
        results.push({
            tag: el.tagName,
            id: el.id,
            class: el.className,
            text: el.textContent.substring(0, 50)
        });
    });
    return results;
    """
    
    results = driver.execute_script(script)
    logger.info(f"   Found {len(results)} elements with 'download' in id/class:")
    for r in results:
        logger.info(f"     <{r['tag']}> id='{r['id']}' class='{r['class']}' text='{r['text'][:30]}...'")

def main():
    driver = None
    invoice_key = "42250485179240000239550020004175361171503396"
    
    try:
        logger.info("=" * 70)
        logger.info("🧪 ADVANCED BUTTON DIAGNOSTIC")
        logger.info("=" * 70)
        
        driver = setup_chrome()
        logger.info("✅ Chrome driver initialized")
        
        # Navigate to site
        logger.info(f"\n🌐 Navigating to meudanfe.com.br...")
        driver.get("https://meudanfe.com.br/")
        time.sleep(3)
        
        # Check iframes before search
        logger.info("\n📦 Checking iframes BEFORE search...")
        check_iframes(driver)
        
        # Enter key and search
        logger.info(f"\n⌨️ Entering invoice key and searching...")
        input_field = driver.find_element(By.ID, 'searchTxt')
        input_field.clear()
        input_field.send_keys(invoice_key)
        time.sleep(1)
        
        search_btn = driver.find_element(By.ID, 'searchBtn')
        search_btn.click()
        logger.info("✅ Search button clicked")
        
        # Wait for results
        logger.info("\n⏳ Waiting 15 seconds for results...")
        time.sleep(15)
        
        # Check iframes after search
        logger.info("\n📦 Checking iframes AFTER search...")
        iframes = check_iframes(driver)
        
        # Search for download elements
        search_all_elements_with_download(driver)
        
        # Check both buttons in main context
        logger.info("\n" + "=" * 70)
        logger.info("CHECKING BUTTONS IN MAIN CONTEXT")
        logger.info("=" * 70)
        
        xml_found, xml_button = check_button_by_id(driver, 'downloadXmlBtn')
        danfe_found, danfe_button = check_button_by_id(driver, 'downloadDanfeBtn')
        
        # If there are iframes, check inside them
        if iframes:
            logger.info("\n" + "=" * 70)
            logger.info("CHECKING INSIDE IFRAMES")
            logger.info("=" * 70)
            
            for i, iframe in enumerate(iframes):
                logger.info(f"\n🔄 Switching to iframe {i+1}...")
                driver.switch_to.frame(iframe)
                
                search_all_elements_with_download(driver)
                check_button_by_id(driver, 'downloadXmlBtn')
                check_button_by_id(driver, 'downloadDanfeBtn')
                
                driver.switch_to.default_content()
                logger.info("🔄 Switched back to main context")
        
        # Try using WebDriverWait
        logger.info("\n" + "=" * 70)
        logger.info("TRYING WEBDRIVERWAIT")
        logger.info("=" * 70)
        
        try:
            logger.info("⏳ Waiting for downloadXmlBtn to be present...")
            wait = WebDriverWait(driver, 10)
            xml_btn = wait.until(EC.presence_of_element_located((By.ID, 'downloadXmlBtn')))
            logger.info("✅ WebDriverWait found downloadXmlBtn!")
        except Exception as e:
            logger.error(f"❌ WebDriverWait failed: {e}")
        
        # Save final HTML
        logger.info("\n💾 Saving final page HTML...")
        with open('final_page_diagnostic.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        logger.info("✅ Saved to final_page_diagnostic.html")
        
        logger.info("\n" + "=" * 70)
        logger.info("🏁 DIAGNOSTIC COMPLETE")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if driver:
            driver.quit()
            logger.info("\n🚪 Browser closed")

if __name__ == "__main__":
    main()
