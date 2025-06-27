#!/usr/bin/env python3
"""
Teste básico do sistema de fallback - apenas identificação de elementos
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def test_element_identification():
    """Testar identificação de elementos no site consultadanfe.com"""
    driver = None
    
    try:
        print("🤖 Configurando Chrome driver...")
        
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=800,600')
        chrome_options.add_argument('--disable-gpu')
        
        service = Service('/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        print("🌐 Navegando para consultadanfe.com...")
        driver.get('https://consultadanfe.com/')
        
        # Aguardar carregamento
        time.sleep(5)
        
        print(f"📍 URL: {driver.current_url}")
        print(f"📝 Título: {driver.title}")
        
        # Tentar encontrar campo de entrada
        print("\n🔍 Procurando campo de entrada...")
        
        wait = WebDriverWait(driver, 10)
        
        # Método 1: Por ID
        try:
            input_field = wait.until(EC.presence_of_element_located((By.ID, "chave")))
            if input_field.is_displayed():
                print("✅ Campo 'chave' encontrado via ID e está visível")
                
                # Testar inserção de texto
                input_field.clear()
                test_key = "35250513516247000107550010000113401146202508"
                input_field.send_keys(test_key)
                print(f"✅ Texto inserido: {test_key[:10]}...")
                
                # Verificar se o texto foi inserido
                inserted_value = input_field.get_attribute('value')
                if inserted_value == test_key:
                    print("✅ Texto verificado com sucesso")
                else:
                    print(f"⚠️ Texto esperado: {test_key}, obtido: {inserted_value}")
                    
            else:
                print("❌ Campo 'chave' encontrado mas não está visível")
        except Exception as e:
            print(f"❌ Campo 'chave' não encontrado via ID: {e}")
        
        # Procurar botão de submissão
        print("\n🔘 Procurando botão de submissão...")
        
        try:
            # Método por texto do botão
            button = driver.find_element(By.XPATH, "//button[contains(text(), 'Buscar DANFE / XML')]")
            if button.is_displayed():
                print("✅ Botão 'Buscar DANFE / XML' encontrado e visível")
                print(f"   Texto: '{button.text}'")
                print(f"   Tipo: {button.get_attribute('type')}")
                print(f"   Habilitado: {button.is_enabled()}")
            else:
                print("❌ Botão encontrado mas não está visível")
        except Exception as e:
            print(f"❌ Botão não encontrado: {e}")
            
            # Tentar outros métodos
            try:
                buttons = driver.find_elements(By.TAG_NAME, 'button')
                print(f"🔍 Encontrados {len(buttons)} botões no total:")
                for i, btn in enumerate(buttons):
                    if btn.is_displayed():
                        print(f"   {i+1}. '{btn.text}' (type: {btn.get_attribute('type')})")
            except Exception as e2:
                print(f"❌ Erro ao listar botões: {e2}")
        
        print("\n✅ Teste de identificação de elementos concluído")
        return True
        
    except Exception as e:
        print(f"💥 Erro no teste: {e}")
        return False
        
    finally:
        if driver:
            driver.quit()
            print("🧹 Driver finalizado")

if __name__ == "__main__":
    print("🧪 TESTE BÁSICO - Identificação de Elementos")
    print("="*50)
    
    success = test_basic_fallback()
    
    print(f"\n🎯 Resultado: {'SUCESSO' if success else 'FALHA'}")