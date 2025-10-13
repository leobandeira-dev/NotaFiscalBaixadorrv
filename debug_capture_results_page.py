#!/usr/bin/env python3
"""
Debug script to capture the EXACT HTML structure of the results page
after searching for an invoice key
"""

import time
import subprocess
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

TEST_KEY = "42250485179240000239550020004175361171503396"

def debug_capture_results():
    """Capture the results page HTML and list all clickable elements"""
    
    # Find chromedriver
    result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
    chromedriver_path = result.stdout.strip()
    print(f"Using chromedriver: {chromedriver_path}")
    
    # Chrome options with SSL ignore
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--ignore-certificate-errors')
    chrome_options.add_argument('--ignore-ssl-errors')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Initialize driver
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        print("\n" + "=" * 70)
        print("DEBUGGING: CAPTURING RESULTS PAGE STRUCTURE")
        print("=" * 70)
        
        # Navigate to site
        url = "https://meudanfe.com.br/"
        print(f"\n1️⃣ Navigating to {url}...")
        driver.get(url)
        time.sleep(5)
        
        # Find and fill input
        print("\n2️⃣ Finding search input...")
        input_field = WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.ID, 'searchTxt'))
        )
        print(f"   ✅ Found input field")
        
        # Type key
        print(f"\n3️⃣ Typing key: {TEST_KEY}...")
        input_field.clear()
        input_field.send_keys(TEST_KEY)
        time.sleep(1)
        
        # Find and click search button
        print("\n4️⃣ Finding and clicking BUSCAR button...")
        search_btn = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.ID, 'searchBtn'))
        )
        print(f"   ✅ Found BUSCAR button")
        search_btn.click()
        
        # Wait for results to load
        print("\n5️⃣ Waiting for results to load (15 seconds)...")
        time.sleep(15)
        
        print("\n6️⃣ Capturing page structure...")
        
        # Save full HTML
        html_file = "/tmp/results_page_debug.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print(f"   💾 Saved HTML to: {html_file}")
        
        # Take screenshot
        screenshot_file = "/tmp/results_page_debug.png"
        driver.save_screenshot(screenshot_file)
        print(f"   📸 Saved screenshot to: {screenshot_file}")
        
        # List ALL buttons
        print("\n" + "=" * 70)
        print("ALL BUTTONS ON PAGE:")
        print("=" * 70)
        buttons = driver.find_elements(By.TAG_NAME, 'button')
        for i, btn in enumerate(buttons):
            print(f"\nButton #{i+1}:")
            print(f"  ID: {btn.get_attribute('id')}")
            print(f"  Class: {btn.get_attribute('class')}")
            print(f"  Text: {btn.text}")
            print(f"  innerHTML: {btn.get_attribute('innerHTML')[:100]}")
            print(f"  Visible: {btn.is_displayed()}")
            print(f"  Enabled: {btn.is_enabled()}")
        
        # List ALL links (a tags)
        print("\n" + "=" * 70)
        print("ALL LINKS ON PAGE:")
        print("=" * 70)
        links = driver.find_elements(By.TAG_NAME, 'a')
        for i, link in enumerate(links):
            link_text = link.text.strip()
            link_id = link.get_attribute('id')
            link_class = link.get_attribute('class')
            
            # Only show links with text or relevant classes
            if link_text or 'download' in (link_class or '').lower() or 'btn' in (link_class or '').lower():
                print(f"\nLink #{i+1}:")
                print(f"  ID: {link_id}")
                print(f"  Class: {link_class}")
                print(f"  Text: {link_text}")
                print(f"  Href: {link.get_attribute('href')}")
                print(f"  Visible: {link.is_displayed()}")
        
        # Search for elements containing "Baixar"
        print("\n" + "=" * 70)
        print("ELEMENTS CONTAINING 'Baixar':")
        print("=" * 70)
        
        all_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'Baixar')]")
        for i, elem in enumerate(all_elements):
            print(f"\nElement #{i+1}:")
            print(f"  Tag: {elem.tag_name}")
            print(f"  ID: {elem.get_attribute('id')}")
            print(f"  Class: {elem.get_attribute('class')}")
            print(f"  Text: {elem.text}")
            print(f"  Visible: {elem.is_displayed()}")
            print(f"  Enabled: {elem.is_enabled()}")
        
        # Search for elements containing "DANFE"
        print("\n" + "=" * 70)
        print("ELEMENTS CONTAINING 'DANFE':")
        print("=" * 70)
        
        danfe_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'DANFE')]")
        for i, elem in enumerate(danfe_elements):
            print(f"\nElement #{i+1}:")
            print(f"  Tag: {elem.tag_name}")
            print(f"  ID: {elem.get_attribute('id')}")
            print(f"  Class: {elem.get_attribute('class')}")
            print(f"  Text: {elem.text}")
            print(f"  Visible: {elem.is_displayed()}")
            print(f"  Enabled: {elem.is_enabled()}")
        
        # Search for elements containing "XML"
        print("\n" + "=" * 70)
        print("ELEMENTS CONTAINING 'XML':")
        print("=" * 70)
        
        xml_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'XML')]")
        for i, elem in enumerate(xml_elements):
            print(f"\nElement #{i+1}:")
            print(f"  Tag: {elem.tag_name}")
            print(f"  ID: {elem.get_attribute('id')}")
            print(f"  Class: {elem.get_attribute('class')}")
            print(f"  Text: {elem.text}")
            print(f"  Visible: {elem.is_displayed()}")
            print(f"  Enabled: {elem.is_enabled()}")
        
        print("\n" + "=" * 70)
        print("✅ DEBUG CAPTURE COMPLETED")
        print("=" * 70)
        print(f"\n📁 Files saved:")
        print(f"   - HTML: {html_file}")
        print(f"   - Screenshot: {screenshot_file}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()
        print("\n✅ Driver closed")

if __name__ == "__main__":
    debug_capture_results()
