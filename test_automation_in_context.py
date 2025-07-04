#!/usr/bin/env python3
"""
Teste da automação no contexto correto baseado no mapeamento atual
Testa com a chave 35250513516247000107550010000113401146202508
"""
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_automation():
    """Teste da automação com base no mapeamento atual"""
    driver = None
    try:
        logger.info("🔍 Iniciando teste da automação com mapeamento atualizado...")
        
        # Setup Chrome
        options = Options()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1200,800')
        
        driver = webdriver.Chrome(options=options)
        
        # Navegar para o site
        logger.info("📱 Navegando para https://meudanfe.com.br/...")
        driver.get("https://meudanfe.com.br/")
        
        # Aguardar carregamento
        logger.info("⏳ Aguardando carregamento da página...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "searchTxt"))
        )
        
        # Encontrar campo de entrada
        logger.info("🎯 Procurando campo de entrada searchTxt...")
        input_field = driver.find_element(By.ID, "searchTxt")
        
        # Verificar se está visível e habilitado
        logger.info(f"✅ Campo encontrado - Visível: {input_field.is_displayed()}, Habilitado: {input_field.is_enabled()}")
        
        # Inserir chave
        invoice_key = "35250513516247000107550010000113401146202508"
        logger.info(f"✏️ Inserindo chave: {invoice_key}")
        
        input_field.clear()
        input_field.send_keys(invoice_key)
        
        # Verificar se a chave foi inserida
        current_value = input_field.get_attribute('value')
        logger.info(f"📝 Valor atual no campo: {current_value}")
        
        # Encontrar botão de busca
        logger.info("🔍 Procurando botão searchBtn...")
        search_button = driver.find_element(By.ID, "searchBtn")
        
        logger.info(f"✅ Botão encontrado - Visível: {search_button.is_displayed()}")
        logger.info(f"🏷️ Texto do botão: {search_button.text}")
        logger.info(f"🔗 Tag do botão: {search_button.tag_name}")
        
        # Aguardar um pouco para garantir que a página está pronta
        time.sleep(2)
        
        # Múltiplas estratégias de clique
        logger.info("👆 Tentativa 1: Click normal...")
        try:
            search_button.click()
            logger.info("✅ Click normal realizado com sucesso")
        except Exception as e:
            logger.warning(f"⚠️ Click normal falhou: {e}")
            
            logger.info("👆 Tentativa 2: Click com JavaScript...")
            try:
                driver.execute_script("arguments[0].click();", search_button)
                logger.info("✅ Click JavaScript realizado com sucesso")
            except Exception as e2:
                logger.warning(f"⚠️ Click JavaScript falhou: {e2}")
                
                logger.info("👆 Tentativa 3: Click com ActionChains...")
                try:
                    ActionChains(driver).move_to_element(search_button).click().perform()
                    logger.info("✅ Click ActionChains realizado com sucesso")
                except Exception as e3:
                    logger.error(f"❌ Todas as estratégias de click falharam: {e3}")
                    return
        
        # Aguardar resultados
        logger.info("⏳ Aguardando resultados da busca...")
        time.sleep(8)
        
        # Verificar URL atual
        current_url = driver.current_url
        logger.info(f"🌐 URL atual: {current_url}")
        
        # Procurar por indicadores de sucesso
        page_content = driver.page_source.lower()
        
        success_indicators = [
            "xml",
            "baixar",
            "download",
            "nota fiscal",
            "nfe",
            "danfe"
        ]
        
        found_indicators = []
        for indicator in success_indicators:
            if indicator in page_content:
                found_indicators.append(indicator)
        
        logger.info(f"🎯 Indicadores encontrados na página: {found_indicators}")
        
        # Procurar elementos específicos de resultado
        try:
            # Buscar links ou botões relacionados a XML/DANFE
            xml_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'XML') or contains(text(), 'xml') or contains(text(), 'BAIXAR') or contains(text(), 'Download')]")
            
            logger.info(f"📄 Encontrados {len(xml_elements)} elementos relacionados a XML/Download:")
            
            for i, element in enumerate(xml_elements[:5]):  # Limitar a 5 primeiros
                try:
                    logger.info(f"  {i+1}. Tag: {element.tag_name}, Texto: '{element.text[:50]}...', ID: {element.get_attribute('id')}")
                except:
                    pass
                    
        except Exception as e:
            logger.warning(f"⚠️ Erro ao buscar elementos XML: {e}")
        
        # Salvar página de resultados para análise
        try:
            with open('test_result_page.html', 'w', encoding='utf-8') as f:
                f.write(driver.page_source)
            logger.info("💾 Página de resultados salva em test_result_page.html")
        except Exception as e:
            logger.warning(f"⚠️ Erro ao salvar página: {e}")
        
        logger.info("✅ Teste da automação concluído!")
        
    except Exception as e:
        logger.error(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if driver:
            try:
                driver.quit()
            except:
                pass

if __name__ == "__main__":
    test_automation()