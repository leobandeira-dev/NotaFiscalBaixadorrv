#!/usr/bin/env python3
"""
Simulação Manual do Site consultadanfe.com
Teste detalhado para identificar problemas na automação
"""

import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import os

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_manual_driver():
    """Configurar Chrome driver para simulação manual"""
    chrome_options = Options()
    
    # Configurações básicas - não usar headless para debug visual
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1200,800')
    
    # Configurações para melhor debugging
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # User agent real
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    try:
        service = Service('/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver')
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # Executar script para remover webdriver property
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        logger.info("✅ Chrome driver configurado com sucesso para simulação manual")
        return driver
        
    except Exception as e:
        logger.error(f"❌ Erro ao configurar Chrome driver: {e}")
        return None

def simulate_manual_consultation(invoice_key="35250513516247000107550010000113401146202508"):
    """
    Simular consulta manual detalhada no site consultadanfe.com
    """
    driver = None
    
    try:
        logger.info("🚀 Iniciando simulação manual da consulta...")
        
        # 1. Configurar driver
        driver = setup_manual_driver()
        if not driver:
            return {"success": False, "error": "Falha ao configurar driver"}
        
        # 2. Acessar o site
        logger.info("🌐 Acessando consultadanfe.com...")
        driver.get("https://consultadanfe.com/")
        time.sleep(3)
        
        # 3. Verificar se a página carregou
        logger.info(f"📍 URL atual: {driver.current_url}")
        logger.info(f"📝 Título da página: {driver.title}")
        
        # 4. Procurar campo de entrada da chave
        logger.info("🔍 Procurando campo de entrada da chave...")
        
        # Tentar diferentes seletores possíveis
        input_selectors = [
            "input[placeholder*='chave']",
            "input[placeholder*='Chave']",
            "input[placeholder*='Digite']",
            "input[type='text']",
            "input[id*='chave']",
            "input[name*='chave']",
            ".form-control",
            "#chave",
            "input"
        ]
        
        input_field = None
        for selector in input_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    logger.info(f"🎯 Encontrado(s) {len(elements)} elemento(s) com seletor: {selector}")
                    for i, element in enumerate(elements):
                        try:
                            placeholder = element.get_attribute('placeholder') or ''
                            id_attr = element.get_attribute('id') or ''
                            name_attr = element.get_attribute('name') or ''
                            logger.info(f"   Elemento {i}: placeholder='{placeholder}', id='{id_attr}', name='{name_attr}'")
                            
                            # Se encontrou um campo que parece ser para chave
                            if any(term in placeholder.lower() for term in ['chave', 'digite', 'nf']) or \
                               any(term in id_attr.lower() for term in ['chave', 'nf']) or \
                               any(term in name_attr.lower() for term in ['chave', 'nf']):
                                input_field = element
                                logger.info(f"✅ Campo de chave identificado: {selector}")
                                break
                        except Exception as e:
                            logger.warning(f"⚠️  Erro ao analisar elemento {i}: {e}")
                            
                if input_field:
                    break
                    
            except Exception as e:
                logger.debug(f"Seletor {selector} não encontrado: {e}")
        
        if not input_field:
            logger.error("❌ Nenhum campo de entrada encontrado")
            
            # Salvar screenshot para debug
            driver.save_screenshot("debug_no_input_field.png")
            logger.info("📸 Screenshot salvo: debug_no_input_field.png")
            
            # Capturar HTML da página
            with open("debug_page_source.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            logger.info("📄 HTML da página salvo: debug_page_source.html")
            
            return {"success": False, "error": "Campo de entrada não encontrado"}
        
        # 5. Inserir a chave
        logger.info(f"⌨️  Inserindo chave: {invoice_key}")
        input_field.clear()
        input_field.send_keys(invoice_key)
        time.sleep(1)
        
        # 6. Procurar botão de consulta
        logger.info("🔍 Procurando botão de consulta...")
        
        button_selectors = [
            "button[type='submit']",
            "input[type='submit']",
            "button:contains('Consultar')",
            "button:contains('CONSULTAR')",
            "button:contains('Gerar')",
            ".btn-primary",
            ".btn",
            "button"
        ]
        
        submit_button = None
        for selector in button_selectors:
            try:
                if ":contains(" in selector:
                    # Usar XPath para texto
                    text_to_find = selector.split(':contains(')[1].split(')')[0].strip("'")
                    xpath = f"//button[contains(text(), '{text_to_find}')]"
                    elements = driver.find_elements(By.XPATH, xpath)
                else:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    
                if elements:
                    logger.info(f"🎯 Encontrado(s) {len(elements)} botão(ões) com seletor: {selector}")
                    for i, element in enumerate(elements):
                        try:
                            text = element.text or ''
                            type_attr = element.get_attribute('type') or ''
                            logger.info(f"   Botão {i}: text='{text}', type='{type_attr}'")
                            
                            # Se encontrou um botão que parece ser de submissão
                            if any(term in text.lower() for term in ['consultar', 'gerar', 'buscar']) or \
                               type_attr == 'submit':
                                submit_button = element
                                logger.info(f"✅ Botão de consulta identificado: {selector}")
                                break
                        except Exception as e:
                            logger.warning(f"⚠️  Erro ao analisar botão {i}: {e}")
                            
                if submit_button:
                    break
                    
            except Exception as e:
                logger.debug(f"Seletor de botão {selector} não encontrado: {e}")
        
        if not submit_button:
            logger.error("❌ Nenhum botão de consulta encontrado")
            
            # Salvar screenshot para debug
            driver.save_screenshot("debug_no_submit_button.png")
            logger.info("📸 Screenshot salvo: debug_no_submit_button.png")
            
            return {"success": False, "error": "Botão de consulta não encontrado"}
        
        # 7. Clicar no botão
        logger.info("🖱️  Clicando no botão de consulta...")
        driver.execute_script("arguments[0].scrollIntoView(true);", submit_button)
        time.sleep(1)
        submit_button.click()
        
        # 8. Aguardar resultado
        logger.info("⏳ Aguardando resultado da consulta...")
        time.sleep(5)
        
        # 9. Verificar se houve redirecionamento ou resultado
        new_url = driver.current_url
        logger.info(f"📍 URL após consulta: {new_url}")
        
        # 10. Procurar indicadores de sucesso ou erro
        success_indicators = [
            "DANFE gerado com sucesso",
            "download",
            "XML",
            "PDF",
            "sucesso"
        ]
        
        error_indicators = [
            "não encontrada",
            "inválida",
            "erro",
            "falha"
        ]
        
        page_text = driver.page_source.lower()
        
        found_success = any(indicator.lower() in page_text for indicator in success_indicators)
        found_error = any(indicator.lower() in page_text for indicator in error_indicators)
        
        logger.info(f"✅ Indicadores de sucesso encontrados: {found_success}")
        logger.info(f"❌ Indicadores de erro encontrados: {found_error}")
        
        # Salvar screenshot final
        driver.save_screenshot("debug_final_result.png")
        logger.info("📸 Screenshot final salvo: debug_final_result.png")
        
        # Salvar HTML final
        with open("debug_final_page.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logger.info("📄 HTML final salvo: debug_final_page.html")
        
        result = {
            "success": True,
            "initial_url": "https://consultadanfe.com/",
            "final_url": new_url,
            "found_input_field": True,
            "found_submit_button": True,
            "success_indicators": found_success,
            "error_indicators": found_error,
            "invoice_key": invoice_key
        }
        
        logger.info("🎉 Simulação manual concluída com sucesso!")
        return result
        
    except Exception as e:
        logger.error(f"💥 Erro durante simulação manual: {e}")
        if driver:
            driver.save_screenshot("debug_error.png")
            logger.info("📸 Screenshot de erro salvo: debug_error.png")
        return {"success": False, "error": str(e)}
        
    finally:
        if driver:
            logger.info("🔚 Fechando driver...")
            time.sleep(2)  # Dar tempo para ver resultado
            driver.quit()

if __name__ == "__main__":
    print("🧪 Iniciando simulação manual do consultadanfe.com...")
    result = simulate_manual_consultation()
    
    print("\n" + "="*50)
    print("📊 RESULTADO DA SIMULAÇÃO:")
    print("="*50)
    
    for key, value in result.items():
        print(f"{key}: {value}")
    
    if result.get("success"):
        print("\n✅ Simulação executada com sucesso!")
    else:
        print(f"\n❌ Simulação falhou: {result.get('error')}")