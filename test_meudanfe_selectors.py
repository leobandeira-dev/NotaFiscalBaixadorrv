#!/usr/bin/env python3
"""
Script para testar e capturar os seletores HTML do site meudanfe.com.br
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_meudanfe_selectors():
    """Test and capture HTML selectors from meudanfe.com.br"""
    
    # Setup Chrome options
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    
    # Find chromedriver
    import subprocess
    result = subprocess.run(['which', 'chromedriver'], capture_output=True, text=True)
    chromedriver_path = result.stdout.strip()
    print(f"Using chromedriver at: {chromedriver_path}")
    
    # Initialize driver
    service = Service(chromedriver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    
    try:
        # Navigate to the site
        url = "https://meudanfe.com.br/"
        print(f"\n🌐 Navigating to {url}...")
        driver.get(url)
        
        # Wait for page to load
        time.sleep(3)
        
        # Get page source
        print("\n📄 Page loaded. Analyzing HTML structure...\n")
        
        # Try to find all input fields
        print("=" * 60)
        print("INPUT FIELDS:")
        print("=" * 60)
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        for i, inp in enumerate(inputs):
            inp_id = inp.get_attribute('id')
            inp_name = inp.get_attribute('name')
            inp_class = inp.get_attribute('class')
            inp_type = inp.get_attribute('type')
            inp_placeholder = inp.get_attribute('placeholder')
            
            print(f"\nInput #{i+1}:")
            print(f"  ID: {inp_id}")
            print(f"  Name: {inp_name}")
            print(f"  Class: {inp_class}")
            print(f"  Type: {inp_type}")
            print(f"  Placeholder: {inp_placeholder}")
        
        # Try to find all buttons
        print("\n" + "=" * 60)
        print("BUTTONS:")
        print("=" * 60)
        buttons = driver.find_elements(By.TAG_NAME, 'button')
        for i, btn in enumerate(buttons):
            btn_id = btn.get_attribute('id')
            btn_name = btn.get_attribute('name')
            btn_class = btn.get_attribute('class')
            btn_text = btn.text
            
            print(f"\nButton #{i+1}:")
            print(f"  ID: {btn_id}")
            print(f"  Name: {btn_name}")
            print(f"  Class: {btn_class}")
            print(f"  Text: {btn_text}")
        
        # Try to find all links (a tags)
        print("\n" + "=" * 60)
        print("LINKS (A TAGS):")
        print("=" * 60)
        links = driver.find_elements(By.TAG_NAME, 'a')
        for i, link in enumerate(links[:20]):  # Limit to first 20
            link_id = link.get_attribute('id')
            link_class = link.get_attribute('class')
            link_text = link.text
            link_href = link.get_attribute('href')
            
            if link_text or link_id:  # Only show links with text or ID
                print(f"\nLink #{i+1}:")
                print(f"  ID: {link_id}")
                print(f"  Class: {link_class}")
                print(f"  Text: {link_text}")
                print(f"  Href: {link_href}")
        
        # Try specific selectors
        print("\n" + "=" * 60)
        print("TESTING SPECIFIC SELECTORS:")
        print("=" * 60)
        
        selectors = [
            ('id', 'searchTxt'),
            ('id', 'searchBtn'),
            ('css', 'input[type="text"]'),
            ('css', 'input[placeholder*="chave"]'),
            ('css', 'input[placeholder*="Chave"]'),
            ('xpath', "//input[@type='text']"),
            ('xpath', "//button[contains(text(), 'BUSCAR')]"),
            ('xpath', "//a[contains(text(), 'BUSCAR')]"),
        ]
        
        for method, selector in selectors:
            try:
                if method == 'id':
                    element = driver.find_element(By.ID, selector)
                elif method == 'css':
                    element = driver.find_element(By.CSS_SELECTOR, selector)
                elif method == 'xpath':
                    element = driver.find_element(By.XPATH, selector)
                
                print(f"\n✅ FOUND: {method}={selector}")
                print(f"   Tag: {element.tag_name}")
                print(f"   ID: {element.get_attribute('id')}")
                print(f"   Class: {element.get_attribute('class')}")
                print(f"   Text: {element.text}")
            except Exception as e:
                print(f"\n❌ NOT FOUND: {method}={selector}")
        
        # Save page source for inspection
        with open('/tmp/meudanfe_page_source.html', 'w', encoding='utf-8') as f:
            f.write(driver.page_source)
        print("\n💾 Page source saved to: /tmp/meudanfe_page_source.html")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()
        print("\n✅ Driver closed")

if __name__ == "__main__":
    test_meudanfe_selectors()
