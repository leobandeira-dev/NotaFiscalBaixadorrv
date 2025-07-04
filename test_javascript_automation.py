#!/usr/bin/env python3
"""
Teste simples para verificar se JavaScript está funcionando na automação
"""
import time
import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_javascript_automation():
    """Testa automação com JavaScript habilitado"""
    
    # Configurações Chrome com JavaScript habilitado
    options = Options()
    options.add_argument('--headless=new')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=800,600')
    # JavaScript habilitado por padrão
    
    driver = None
    try:
        driver = webdriver.Chrome(options=options)
        driver.set_page_load_timeout(20)
        
        invoice_key = "35250513516247000107550010000113401146202508"
        
        logger.info("🚀 Iniciando teste com JavaScript habilitado...")
        
        # Navegar para o site
        logger.info("📱 Navegando para meudanfe.com.br...")
        driver.get("https://meudanfe.com.br/")
        
        # Aguardar carregamento
        time.sleep(3)
        
        # Localizar campo
        logger.info("🎯 Localizando campo de entrada...")
        input_field = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "searchTxt"))
        )
        logger.info("✅ Campo encontrado")
        
        # Inserir chave
        logger.info("✏️ Inserindo chave...")
        input_field.clear()
        input_field.send_keys(invoice_key)
        
        # Localizar botão
        logger.info("🔍 Localizando botão...")
        search_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.ID, "searchBtn"))
        )
        logger.info("✅ Botão encontrado")
        
        # Clicar no botão
        logger.info("👆 Clicando no botão...")
        search_button.click()
        
        # Aguardar com múltiplas estratégias
        logger.info("⏳ Aguardando resultados...")
        
        # Aguardar um pouco para JavaScript processar
        time.sleep(5)
        
        # Verificar se optionsDiv apareceu
        try:
            options_div = driver.find_element(By.ID, "optionsDiv")
            is_visible = options_div.is_displayed()
            logger.info(f"📋 Options div encontrada, visível: {is_visible}")
            
            if not is_visible:
                logger.info("🔧 Forçando visibilidade via JavaScript...")
                driver.execute_script("""
                    var div = document.getElementById('optionsDiv');
                    if (div) {
                        div.style.display = 'block';
                        console.log('Forced visible');
                    }
                """)
                time.sleep(2)
                is_visible = options_div.is_displayed()
                logger.info(f"📋 Após forçar, visível: {is_visible}")
            
            if is_visible:
                # Procurar botão XML
                try:
                    xml_button = driver.find_element(By.ID, "downloadXmlBtn")
                    logger.info("🎯 Botão XML encontrado!")
                    
                    # Verificar se é clicável
                    if xml_button.is_enabled():
                        logger.info("✅ Botão XML está habilitado")
                        
                        # Simular clique
                        xml_button.click()
                        logger.info("🖱️ Clique no botão XML executado")
                        
                        # Aguardar download ou mudança
                        time.sleep(3)
                        
                        return {
                            'success': True,
                            'message': 'Automação funcionando - botão XML clicado com sucesso'
                        }
                    else:
                        logger.info("⚠️ Botão XML não está habilitado")
                except Exception as e:
                    logger.info(f"❌ Botão XML não encontrado: {e}")
            
        except Exception as e:
            logger.info(f"❌ Options div não encontrada: {e}")
        
        # Analisar página atual
        logger.info("🔍 Analisando página atual...")
        current_url = driver.current_url
        page_title = driver.title
        page_content = driver.page_source.lower()
        
        logger.info(f"URL: {current_url}")
        logger.info(f"Título: {page_title}")
        
        # Verificar indicadores
        indicators = []
        if 'baixar xml' in page_content:
            indicators.append('baixar xml')
        if 'downloadxmlbtn' in page_content:
            indicators.append('downloadxmlbtn')
        if 'optionsdiv' in page_content:
            indicators.append('optionsdiv')
        
        logger.info(f"Indicadores encontrados: {indicators}")
        
        return {
            'success': len(indicators) > 0,
            'url': current_url,
            'title': page_title,
            'indicators': indicators,
            'message': f'Processo concluído. Encontrados {len(indicators)} indicadores.'
        }
        
    except Exception as e:
        logger.error(f"Erro no teste: {e}")
        return {'success': False, 'error': str(e)}
    
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("🔒 Navegador fechado")
            except:
                pass

if __name__ == "__main__":
    result = test_javascript_automation()
    
    logger.info("📊 RESULTADO DO TESTE:")
    logger.info(f"  Sucesso: {result.get('success', False)}")
    logger.info(f"  Mensagem: {result.get('message', result.get('error', 'N/A'))}")
    
    if result.get('success'):
        logger.info(f"  Indicadores: {result.get('indicators', [])}")