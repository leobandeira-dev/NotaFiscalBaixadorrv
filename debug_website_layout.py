#!/usr/bin/env python3
"""
Debug do layout atual do meudanfe.com.br
Captura HTML e identifica elementos disponíveis
"""
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_website_layout():
    """Debug do layout atual do site"""
    driver = None
    try:
        # Configurar Chrome
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        
        driver = webdriver.Chrome(options=chrome_options)
        logger.info("Chrome driver inicializado")
        
        # Navegar para o site
        url = "https://meudanfe.com.br/"
        logger.info(f"Navegando para {url}")
        driver.get(url)
        
        # Aguardar carregamento
        time.sleep(5)
        
        # Capturar HTML da página
        page_source = driver.page_source
        
        # Salvar HTML completo
        with open('debug_page_source.html', 'w', encoding='utf-8') as f:
            f.write(page_source)
        logger.info("HTML salvo em debug_page_source.html")
        
        # Encontrar todos os inputs
        inputs = driver.find_elements(By.TAG_NAME, 'input')
        logger.info(f"Encontrados {len(inputs)} elementos input:")
        for i, inp in enumerate(inputs):
            try:
                input_type = inp.get_attribute('type') or 'text'
                placeholder = inp.get_attribute('placeholder') or ''
                name = inp.get_attribute('name') or ''
                id_attr = inp.get_attribute('id') or ''
                classes = inp.get_attribute('class') or ''
                logger.info(f"  Input {i+1}: type='{input_type}', placeholder='{placeholder}', name='{name}', id='{id_attr}', class='{classes}'")
            except Exception as e:
                logger.info(f"  Input {i+1}: Erro ao obter atributos - {e}")
        
        # Encontrar todos os botões
        buttons = driver.find_elements(By.TAG_NAME, 'button')
        logger.info(f"Encontrados {len(buttons)} elementos button:")
        for i, btn in enumerate(buttons):
            try:
                text = btn.text.strip()
                btn_type = btn.get_attribute('type') or ''
                classes = btn.get_attribute('class') or ''
                onclick = btn.get_attribute('onclick') or ''
                logger.info(f"  Button {i+1}: text='{text}', type='{btn_type}', class='{classes}', onclick='{onclick}'")
            except Exception as e:
                logger.info(f"  Button {i+1}: Erro ao obter atributos - {e}")
        
        # Buscar elementos com texto 'BUSCAR' ou 'buscar'
        buscar_elements = driver.find_elements(By.XPATH, "//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'buscar')]")
        logger.info(f"Encontrados {len(buscar_elements)} elementos com texto 'buscar':")
        for i, elem in enumerate(buscar_elements):
            try:
                tag = elem.tag_name
                text = elem.text.strip()
                classes = elem.get_attribute('class') or ''
                logger.info(f"  Buscar {i+1}: tag='{tag}', text='{text}', class='{classes}'")
            except Exception as e:
                logger.info(f"  Buscar {i+1}: Erro ao obter atributos - {e}")
        
        # Testar entrada de chave
        invoice_key = "35250513516247000107550010000113401146202508"
        logger.info(f"Testando entrada da chave: {invoice_key}")
        
        # Tentar encontrar e preencher campo de entrada
        input_selectors = [
            (By.CSS_SELECTOR, 'input[type="text"]'),
            (By.CSS_SELECTOR, 'input[placeholder*="Chave"]'),
            (By.CSS_SELECTOR, 'input[placeholder*="chave"]'),
            (By.CSS_SELECTOR, 'input[name*="chave"]'),
            (By.CSS_SELECTOR, 'input[id*="chave"]'),
            (By.XPATH, "//input[@type='text' or not(@type)]")
        ]
        
        input_field = None
        for selector in input_selectors:
            try:
                input_field = WebDriverWait(driver, 3).until(
                    EC.element_to_be_clickable(selector)
                )
                logger.info(f"Campo de entrada encontrado com seletor: {selector}")
                break
            except:
                continue
        
        if input_field:
            try:
                input_field.clear()
                input_field.send_keys(invoice_key)
                logger.info("Chave inserida com sucesso")
                
                # Aguardar um pouco
                time.sleep(2)
                
                # Tentar encontrar botão de busca após inserir chave
                submit_selectors = [
                    (By.XPATH, "//button[contains(text(), 'BUSCAR')]"),
                    (By.XPATH, "//button[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'buscar')]"),
                    (By.CSS_SELECTOR, "button[type='submit']"),
                    (By.CSS_SELECTOR, "input[type='submit']"),
                    (By.CSS_SELECTOR, "button"),
                    (By.XPATH, "//button"),
                    (By.XPATH, "//*[@onclick]")
                ]
                
                submit_button = None
                for selector in submit_selectors:
                    try:
                        submit_button = WebDriverWait(driver, 2).until(
                            EC.element_to_be_clickable(selector)
                        )
                        logger.info(f"Botão submit encontrado com seletor: {selector}")
                        break
                    except:
                        continue
                
                if submit_button:
                    logger.info(f"Botão encontrado: text='{submit_button.text}', tag='{submit_button.tag_name}'")
                else:
                    logger.warning("Nenhum botão de submit encontrado")
                    
            except Exception as e:
                logger.error(f"Erro ao inserir chave: {e}")
        else:
            logger.error("Nenhum campo de entrada encontrado")
        
        logger.info("Debug concluído")
        
    except Exception as e:
        logger.error(f"Erro durante debug: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    debug_website_layout()