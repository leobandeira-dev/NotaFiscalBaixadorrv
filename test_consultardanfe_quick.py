#!/usr/bin/env python3
"""
Teste rápido do consultardanfe.com - apenas identificação
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time

def test_quick():
    """Teste rápido de identificação de elementos"""
    driver = None
    
    try:
        print("🔧 Configurando Chrome...")
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1024,768')
        chrome_options.add_argument('--disable-gpu')
        
        service = Service('/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("🌐 Navegando para consultardanfe.com...")
        driver.get('https://consultardanfe.com/')
        time.sleep(5)
        
        print(f"📝 Título: {driver.title}")
        print(f"📍 URL: {driver.current_url}")
        
        # Verificar campos de entrada
        print("\n🔍 Verificando campo de entrada...")
        inputs = driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
        
        for i, inp in enumerate(inputs):
            if inp.is_displayed():
                placeholder = inp.get_attribute('placeholder') or ''
                print(f"   Input {i+1}: placeholder='{placeholder}'")
                
                if 'chave' in placeholder.lower():
                    print("   ✅ Campo de chave encontrado!")
                    
                    # Testar inserção
                    test_key = "35250513516247000107550010000113401146202508"
                    inp.clear()
                    inp.send_keys(test_key)
                    
                    inserted = inp.get_attribute('value')
                    if inserted == test_key:
                        print("   ✅ Chave inserida com sucesso!")
                    else:
                        print(f"   ⚠️ Chave parcial: {inserted[:20]}...")
        
        # Verificar botões
        print("\n🔘 Verificando botões...")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        
        for i, btn in enumerate(buttons):
            if btn.is_displayed():
                text = btn.text.strip()
                if text:
                    print(f"   Botão {i+1}: '{text}'")
                    
                    if 'buscar' in text.lower() or 'danfe' in text.lower():
                        print("   ✅ Botão de busca encontrado!")
        
        # Verificar CAPTCHA
        print("\n🤖 Verificando CAPTCHA...")
        captcha_indicators = [
            "iframe[src*='recaptcha']",
            ".g-recaptcha",
            "input[name*='captcha']"
        ]
        
        captcha_found = False
        for indicator in captcha_indicators:
            elements = driver.find_elements(By.CSS_SELECTOR, indicator)
            if elements:
                for element in elements:
                    if element.is_displayed():
                        print(f"   ⚠️ CAPTCHA detectado: {indicator}")
                        captcha_found = True
        
        if not captcha_found:
            print("   ✅ Nenhum CAPTCHA detectado")
        
        print("\n✅ Teste concluído com sucesso!")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    print("🧪 TESTE RÁPIDO - consultardanfe.com")
    print("="*40)
    
    success = test_quick()
    print(f"\n🎯 Resultado: {'SUCESSO' if success else 'FALHA'}")