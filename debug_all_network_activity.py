#!/usr/bin/env python3
"""
Debug script to see ALL network activity and JavaScript behavior when clicking download buttons
"""

import time
import logging
import json
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

def setup_chrome():
    """Setup Chrome with full logging"""
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--ignore-ssl-errors')
    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    # Enable performance logging
    options.set_capability('goog:loggingPrefs', {'performance': 'ALL', 'browser': 'ALL'})
    
    driver = webdriver.Chrome(options=options)
    driver.execute_cdp_cmd('Network.enable', {})
    driver.execute_cdp_cmd('Network.setUserAgentOverride', {
        "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    })
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

def analyze_all_network_logs(driver, button_name):
    """Analyze ALL network activity"""
    logger.info(f"\n📊 ANALYZING ALL NETWORK ACTIVITY AFTER {button_name} CLICK")
    logger.info("=" * 70)
    
    logs = driver.get_log('performance')
    logger.info(f"Total performance log entries: {len(logs)}")
    
    requests_made = []
    responses_received = []
    
    for log in logs:
        try:
            message = json.loads(log['message'])['message']
            method = message.get('method', '')
            
            if 'Network.request' in method:
                request_data = message.get('params', {})
                url = request_data.get('request', {}).get('url', '') or request_data.get('url', '')
                if url:
                    requests_made.append({
                        'method': method,
                        'url': url,
                        'timestamp': log.get('timestamp', 0)
                    })
            
            if 'Network.response' in method:
                response_data = message.get('params', {})
                response = response_data.get('response', {})
                url = response.get('url', '')
                content_type = response.get('mimeType', '')
                headers = response.get('headers', {})
                
                if url:
                    responses_received.append({
                        'method': method,
                        'url': url,
                        'content_type': content_type,
                        'headers': headers,
                        'timestamp': log.get('timestamp', 0)
                    })
        
        except (json.JSONDecodeError, KeyError) as e:
            continue
    
    logger.info(f"\n🌐 REQUESTS MADE: {len(requests_made)}")
    for req in requests_made[-10:]:  # Last 10
        logger.info(f"   {req['method']}: {req['url'][:100]}")
    
    logger.info(f"\n📦 RESPONSES RECEIVED: {len(responses_received)}")
    for resp in responses_received[-10:]:  # Last 10
        logger.info(f"   {resp['content_type']}: {resp['url'][:100]}")
        if 'content-disposition' in str(resp['headers']).lower():
            logger.info(f"     ⚠️ HAS Content-Disposition!")
    
    # Save full logs to file
    with open(f'network_logs_{button_name}.json', 'w') as f:
        json.dump({
            'requests': requests_made,
            'responses': responses_received
        }, f, indent=2)
    
    logger.info(f"\n💾 Full logs saved to: network_logs_{button_name}.json")
    
    return requests_made, responses_received

def main():
    driver = None
    invoice_key = "42250485179240000239550020004175361171503396"
    
    try:
        logger.info("=" * 70)
        logger.info("🔍 DEBUG: ALL NETWORK ACTIVITY")
        logger.info("=" * 70)
        
        driver = setup_chrome()
        logger.info("✅ Chrome initialized")
        
        # Navigate
        logger.info(f"\n🌐 Navigating to meudanfe.com.br...")
        driver.get("https://meudanfe.com.br/")
        time.sleep(3)
        
        # Search
        logger.info(f"⌨️ Searching for invoice...")
        input_field = driver.find_element(By.ID, 'searchTxt')
        input_field.clear()
        input_field.send_keys(invoice_key)
        time.sleep(1)
        
        search_btn = driver.find_element(By.ID, 'searchBtn')
        
        # Clear logs before search
        driver.get_log('performance')
        
        search_btn.click()
        logger.info("✅ Search clicked")
        time.sleep(20)  # Wait for results
        
        # Analyze logs after search
        analyze_all_network_logs(driver, "SEARCH")
        
        # Find XML button
        logger.info("\n" + "=" * 70)
        logger.info("🎯 TESTING XML BUTTON")
        logger.info("=" * 70)
        
        xml_btn = driver.find_element(By.ID, 'downloadXmlBtn')
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", xml_btn)
        time.sleep(2)
        
        # Check button onclick handler
        onclick_js = driver.execute_script("""
            var btn = arguments[0];
            return {
                onclick: btn.onclick ? btn.onclick.toString() : null,
                href: btn.href,
                eventListeners: getEventListeners ? getEventListeners(btn) : 'N/A'
            };
        """, xml_btn)
        logger.info(f"\n🔍 Button attributes:")
        logger.info(f"   onclick: {onclick_js.get('onclick')}")
        logger.info(f"   href: {onclick_js.get('href')}")
        
        # Clear logs before click
        driver.get_log('performance')
        
        # Click XML button
        driver.execute_script("arguments[0].click();", xml_btn)
        logger.info("✅ XML button clicked")
        
        # Wait and analyze
        time.sleep(10)
        analyze_all_network_logs(driver, "XML_BUTTON")
        
        logger.info("\n" + "=" * 70)
        logger.info("🏁 DEBUG COMPLETE")
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
