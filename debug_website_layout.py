#!/usr/bin/env python3
"""
Debug do layout atual do meudanfe.com.br
Captura HTML e identifica elementos disponíveis
"""
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from performance_solution import PerformanceSolution

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_website_layout():
    """Debug do layout atual do site"""
    driver = None
    try:
        logger.info("Iniciando debug do layout do meudanfe.com.br...")
        
        # Setup Chrome com configurações básicas
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1200,800')
        
        driver = webdriver.Chrome(options=options)
        
        # Navegar para o site
        logger.info("Navegando para https://meudanfe.com.br/...")
        driver.get("https://meudanfe.com.br/")
        
        # Aguardar carregamento
        time.sleep(5)
        
        logger.info("Página carregada. Analisando estrutura...")
        
        # Salvar HTML da página
        page_source = driver.page_source
        with open('debug_page_source.html', 'w', encoding='utf-8') as f:
            f.write(page_source)
        logger.info("HTML da página salvo em debug_page_source.html")
        
        # Buscar elementos de input
        logger.info("\n=== ELEMENTOS DE INPUT ===")
        inputs = driver.find_elements(By.TAG_NAME, "input")
        for i, input_elem in enumerate(inputs):
            try:
                input_id = input_elem.get_attribute("id")
                input_name = input_elem.get_attribute("name")
                input_type = input_elem.get_attribute("type")
                input_placeholder = input_elem.get_attribute("placeholder")
                input_class = input_elem.get_attribute("class")
                
                logger.info(f"Input {i+1}:")
                logger.info(f"  ID: {input_id}")
                logger.info(f"  Name: {input_name}")
                logger.info(f"  Type: {input_type}")
                logger.info(f"  Placeholder: {input_placeholder}")
                logger.info(f"  Class: {input_class}")
                logger.info("")
            except Exception as e:
                logger.info(f"Erro ao analisar input {i+1}: {e}")
        
        # Buscar botões
        logger.info("\n=== BOTÕES ===")
        buttons = driver.find_elements(By.TAG_NAME, "button")
        for i, button in enumerate(buttons):
            try:
                button_id = button.get_attribute("id")
                button_text = button.text
                button_class = button.get_attribute("class")
                button_type = button.get_attribute("type")
                
                logger.info(f"Button {i+1}:")
                logger.info(f"  ID: {button_id}")
                logger.info(f"  Text: {button_text}")
                logger.info(f"  Class: {button_class}")
                logger.info(f"  Type: {button_type}")
                logger.info("")
            except Exception as e:
                logger.info(f"Erro ao analisar button {i+1}: {e}")
        
        # Buscar links que podem ser botões
        logger.info("\n=== LINKS (possíveis botões) ===")
        links = driver.find_elements(By.TAG_NAME, "a")
        for i, link in enumerate(links):
            try:
                link_id = link.get_attribute("id")
                link_text = link.text
                link_class = link.get_attribute("class")
                link_href = link.get_attribute("href")
                
                # Filtrar apenas links que podem ser botões de busca
                if any(keyword in (link_text or "").lower() for keyword in ["buscar", "search", "pesquisar"]) or \
                   any(keyword in (link_id or "").lower() for keyword in ["search", "btn", "buscar"]):
                    logger.info(f"Link {i+1} (possível botão):")
                    logger.info(f"  ID: {link_id}")
                    logger.info(f"  Text: {link_text}")
                    logger.info(f"  Class: {link_class}")
                    logger.info(f"  Href: {link_href}")
                    logger.info("")
            except Exception as e:
                logger.info(f"Erro ao analisar link {i+1}: {e}")
        
        # Agora testar o processo de busca
        logger.info("\n=== TESTANDO PROCESSO DE BUSCA ===")
        invoice_key = "35250513516247000107550010000113401146202508"
        
        # Tentar encontrar campo de entrada
        input_found = False
        input_selectors = [
            ("id", "searchTxt"),
            ("name", "searchTxt"),
            ("css", "input[type='text']"),
            ("css", "input[placeholder*='chave']"),
            ("css", "input[placeholder*='Chave']"),
            ("xpath", "//input[@type='text']")
        ]
        
        for selector_type, selector_value in input_selectors:
            try:
                if selector_type == "id":
                    input_element = driver.find_element(By.ID, selector_value)
                elif selector_type == "name":
                    input_element = driver.find_element(By.NAME, selector_value)
                elif selector_type == "css":
                    input_element = driver.find_element(By.CSS_SELECTOR, selector_value)
                elif selector_type == "xpath":
                    input_element = driver.find_element(By.XPATH, selector_value)
                
                if input_element.is_displayed() and input_element.is_enabled():
                    logger.info(f"✅ Campo de entrada encontrado: {selector_type}='{selector_value}'")
                    
                    # Tentar inserir a chave
                    input_element.clear()
                    input_element.send_keys(invoice_key)
                    logger.info(f"✅ Chave inserida com sucesso")
                    input_found = True
                    break
                    
            except Exception as e:
                logger.info(f"❌ Seletor {selector_type}='{selector_value}' falhou: {e}")
        
        if not input_found:
            logger.error("❌ Nenhum campo de entrada funcional encontrado!")
            return
        
        # Tentar encontrar e clicar no botão de busca
        button_selectors = [
            ("id", "searchBtn"),
            ("xpath", "//a[contains(text(), 'BUSCAR')]"),
            ("xpath", "//button[contains(text(), 'BUSCAR')]"),
            ("css", "a[id='searchBtn']"),
            ("xpath", "//a[@id='searchBtn']")
        ]
        
        button_found = False
        for selector_type, selector_value in button_selectors:
            try:
                if selector_type == "id":
                    button_element = driver.find_element(By.ID, selector_value)
                elif selector_type == "css":
                    button_element = driver.find_element(By.CSS_SELECTOR, selector_value)
                elif selector_type == "xpath":
                    button_element = driver.find_element(By.XPATH, selector_value)
                
                if button_element.is_displayed():
                    logger.info(f"✅ Botão de busca encontrado: {selector_type}='{selector_value}'")
                    
                    # Clicar no botão
                    button_element.click()
                    logger.info(f"✅ Botão clicado com sucesso")
                    button_found = True
                    break
                    
            except Exception as e:
                logger.info(f"❌ Seletor de botão {selector_type}='{selector_value}' falhou: {e}")
        
        if not button_found:
            logger.error("❌ Nenhum botão de busca funcional encontrado!")
            return
        
        # Aguardar resultados
        logger.info("Aguardando resultados da busca...")
        time.sleep(8)
        
        # Capturar nova URL e conteúdo
        new_url = driver.current_url
        logger.info(f"Nova URL após busca: {new_url}")
        
        # Buscar botões de download
        logger.info("\n=== PROCURANDO BOTÕES DE DOWNLOAD ===")
        page_content = driver.page_source.lower()
        
        if "baixar xml" in page_content:
            logger.info("✅ Texto 'Baixar XML' encontrado na página")
        elif "xml" in page_content:
            logger.info("⚠️ Texto 'xml' encontrado na página (mas não 'Baixar XML')")
        else:
            logger.info("❌ Nenhum texto relacionado a XML encontrado")
        
        # Buscar todos os botões na página de resultados
        download_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), 'XML') or contains(text(), 'xml') or contains(text(), 'Baixar')]")
        
        logger.info(f"Encontrados {len(download_buttons)} elementos com texto relacionado a download:")
        for i, btn in enumerate(download_buttons):
            try:
                btn_text = btn.text
                btn_tag = btn.tag_name
                btn_id = btn.get_attribute("id")
                btn_class = btn.get_attribute("class")
                
                logger.info(f"Elemento {i+1}:")
                logger.info(f"  Tag: {btn_tag}")
                logger.info(f"  Text: {btn_text}")
                logger.info(f"  ID: {btn_id}")
                logger.info(f"  Class: {btn_class}")
                logger.info("")
            except Exception as e:
                logger.info(f"Erro ao analisar elemento {i+1}: {e}")
        
        # Salvar HTML da página de resultados
        result_page_source = driver.page_source
        with open('debug_result_page_source.html', 'w', encoding='utf-8') as f:
            f.write(result_page_source)
        logger.info("HTML da página de resultados salvo em debug_result_page_source.html")
        
        logger.info("\n=== DEBUG COMPLETO ===")
        logger.info("Verifique os arquivos debug_page_source.html e debug_result_page_source.html para análise detalhada")
        
    except Exception as e:
        logger.error(f"Erro durante debug: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    debug_website_layout()