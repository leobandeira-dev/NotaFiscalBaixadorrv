#!/usr/bin/env python3
"""
Teste Rápido do Site consultadanfe.com
Versão otimizada para identificar elementos rapidamente
"""

import requests
from bs4 import BeautifulSoup
import re

def test_site_structure():
    """Testar estrutura do site consultadanfe.com rapidamente"""
    
    try:
        print("🌐 Acessando consultadanfe.com...")
        
        # Headers para simular browser real
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        response = requests.get('https://consultadanfe.com/', headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Erro HTTP: {response.status_code}")
            return False
            
        print(f"✅ Site acessível (Status: {response.status_code})")
        
        # Analisar HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print(f"📝 Título: {soup.title.string if soup.title else 'N/A'}")
        
        # Procurar campos de input
        inputs = soup.find_all('input')
        print(f"🔍 Encontrados {len(inputs)} campos input:")
        
        for i, inp in enumerate(inputs):
            input_type = inp.get('type', '')
            placeholder = inp.get('placeholder', '')
            input_id = inp.get('id', '')
            name = inp.get('name', '')
            
            print(f"   {i+1}. type='{input_type}', placeholder='{placeholder}', id='{input_id}', name='{name}'")
            
            # Verificar se parece campo para chave NF
            if any(term in placeholder.lower() for term in ['chave', 'nf', 'digite']):
                print(f"      🎯 POSSÍVEL CAMPO DE CHAVE NF!")
        
        # Procurar botões
        buttons = soup.find_all(['button', 'input'])
        submit_buttons = [btn for btn in buttons if 
                         btn.get('type') == 'submit' or 
                         'consultar' in btn.get_text().lower() or
                         'gerar' in btn.get_text().lower()]
        
        print(f"🔘 Encontrados {len(submit_buttons)} botões de submissão:")
        for i, btn in enumerate(submit_buttons):
            btn_text = btn.get_text().strip()
            btn_type = btn.get('type', '')
            print(f"   {i+1}. text='{btn_text}', type='{btn_type}'")
        
        # Procurar formulários
        forms = soup.find_all('form')
        print(f"📋 Encontrados {len(forms)} formulários:")
        for i, form in enumerate(forms):
            action = form.get('action', '')
            method = form.get('method', '')
            print(f"   {i+1}. action='{action}', method='{method}'")
        
        # Verificar se usa JavaScript/React/Next.js
        scripts = soup.find_all('script')
        has_nextjs = any('next' in script.get('src', '').lower() for script in scripts if script.get('src'))
        has_react = any('react' in script.get('src', '').lower() for script in scripts if script.get('src'))
        
        print(f"⚛️  Next.js detectado: {has_nextjs}")
        print(f"⚛️  React detectado: {has_react}")
        
        if has_nextjs or has_react:
            print("⚠️  ALERTA: Site usa framework JavaScript - pode ser necessário aguardar carregamento dinâmico")
        
        return True
        
    except requests.RequestException as e:
        print(f"❌ Erro de conexão: {e}")
        return False
    except Exception as e:
        print(f"💥 Erro inesperado: {e}")
        return False

def test_selenium_quick():
    """Teste rápido com Selenium para elementos dinâmicos"""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        import time
        
        print("\n🤖 Testando com Selenium (rápido)...")
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=800,600')
        
        service = Service('/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        driver.get('https://consultadanfe.com/')
        time.sleep(3)  # Aguardar carregamento
        
        print(f"📍 URL final: {driver.current_url}")
        print(f"📝 Título: {driver.title}")
        
        # Procurar elementos input
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        print(f"🔍 Selenium encontrou {len(inputs)} inputs:")
        
        for i, inp in enumerate(inputs):
            try:
                input_type = inp.get_attribute('type') or ''
                placeholder = inp.get_attribute('placeholder') or ''
                input_id = inp.get_attribute('id') or ''
                name = inp.get_attribute('name') or ''
                visible = inp.is_displayed()
                
                print(f"   {i+1}. type='{input_type}', placeholder='{placeholder}', id='{input_id}', name='{name}', visible={visible}")
                
            except Exception as e:
                print(f"   {i+1}. Erro ao analisar input: {e}")
        
        # Procurar botões
        buttons = driver.find_elements(By.TAG_NAME, 'button')
        print(f"🔘 Selenium encontrou {len(buttons)} botões:")
        
        for i, btn in enumerate(buttons):
            try:
                btn_text = btn.text.strip()
                btn_type = btn.get_attribute('type') or ''
                visible = btn.is_displayed()
                
                print(f"   {i+1}. text='{btn_text}', type='{btn_type}', visible={visible}")
                
            except Exception as e:
                print(f"   {i+1}. Erro ao analisar botão: {e}")
        
        driver.quit()
        print("✅ Teste Selenium concluído")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste Selenium: {e}")
        return False

if __name__ == "__main__":
    print("🧪 TESTE RÁPIDO - consultadanfe.com")
    print("="*50)
    
    # Teste 1: Estrutura HTML estática
    success1 = test_site_structure()
    
    # Teste 2: Elementos dinâmicos com Selenium
    success2 = test_selenium_quick()
    
    print("\n" + "="*50)
    print("📊 RESULTADO DOS TESTES:")
    print(f"HTML estático: {'✅' if success1 else '❌'}")
    print(f"Selenium dinâmico: {'✅' if success2 else '❌'}")