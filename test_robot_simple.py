"""
Teste simplificado do robô XML para identificar problema específico
"""

import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_robot_simple():
    """Teste básico do robô XML"""
    
    # Configuração básica de logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    driver = None
    try:
        # Configurações básicas do Chrome
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=800,600')
        
        # Detectar ambiente
        is_deploy = os.environ.get('REPLIT_DEPLOYMENT') == 'true'
        env_type = "DEPLOY" if is_deploy else "DESENVOLVIMENTO"
        logger.info(f"Ambiente: {env_type}")
        
        # Criar driver
        chromedriver_path = "/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver"
        
        if os.path.exists(chromedriver_path):
            from selenium.webdriver.chrome.service import Service
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)
        else:
            driver = webdriver.Chrome(options=options)
        
        logger.info("Driver criado com sucesso")
        
        # Teste básico de navegação
        logger.info("Testando navegação...")
        driver.get("https://httpbin.org/get")
        time.sleep(2)
        
        page_title = driver.title
        logger.info(f"Página carregada: {page_title}")
        
        # Teste do site alvo
        logger.info("Testando site alvo...")
        driver.get("https://meudanfe.com.br/")
        time.sleep(3)
        
        # Verificar se página carregou
        body_present = driver.find_element(By.TAG_NAME, "body")
        if body_present:
            logger.info("Site alvo acessível")
            
            # Procurar campo de entrada de forma simples
            try:
                input_fields = driver.find_elements(By.TAG_NAME, "input")
                logger.info(f"Encontrados {len(input_fields)} campos de entrada")
                
                # Verificar placeholders
                for i, field in enumerate(input_fields):
                    placeholder = field.get_attribute('placeholder') or ''
                    type_attr = field.get_attribute('type') or ''
                    logger.info(f"Campo {i}: type='{type_attr}', placeholder='{placeholder}'")
                
                # Procurar campo específico da chave
                chave_field = None
                for field in input_fields:
                    placeholder = (field.get_attribute('placeholder') or '').lower()
                    if 'chave' in placeholder:
                        chave_field = field
                        logger.info("Campo da chave encontrado!")
                        break
                
                if chave_field:
                    # Testar inserção de dados
                    test_key = "44250485179240000239550020004175361171503396"
                    chave_field.clear()
                    chave_field.send_keys(test_key)
                    logger.info("Chave inserida com sucesso")
                    
                    # Procurar botões
                    buttons = driver.find_elements(By.TAG_NAME, "button")
                    logger.info(f"Encontrados {len(buttons)} botões")
                    
                    for i, btn in enumerate(buttons):
                        btn_text = btn.text or btn.get_attribute('value') or ''
                        btn_type = btn.get_attribute('type') or ''
                        logger.info(f"Botão {i}: text='{btn_text}', type='{btn_type}'")
                    
                    return {
                        'success': True,
                        'environment': env_type,
                        'message': 'Robô funcionando - campo e botões encontrados',
                        'fields_count': len(input_fields),
                        'buttons_count': len(buttons)
                    }
                else:
                    return {
                        'success': False,
                        'environment': env_type,
                        'message': 'Campo da chave não encontrado',
                        'fields_count': len(input_fields)
                    }
                    
            except Exception as e:
                logger.error(f"Erro procurando elementos: {e}")
                return {
                    'success': False,
                    'environment': env_type,
                    'message': f'Erro: {e}'
                }
        else:
            return {
                'success': False,
                'environment': env_type,
                'message': 'Página não carregou corretamente'
            }
            
    except Exception as e:
        logger.error(f"Erro crítico: {e}")
        return {
            'success': False,
            'message': f'Erro crítico: {e}'
        }
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Driver encerrado")
            except:
                pass

if __name__ == "__main__":
    result = test_robot_simple()
    
    print("\n" + "="*50)
    print("RESULTADO DO TESTE SIMPLES")
    print("="*50)
    print(f"Sucesso: {'✅' if result['success'] else '❌'}")
    print(f"Ambiente: {result.get('environment', 'N/A')}")
    print(f"Mensagem: {result['message']}")
    
    if 'fields_count' in result:
        print(f"Campos encontrados: {result['fields_count']}")
    if 'buttons_count' in result:
        print(f"Botões encontrados: {result['buttons_count']}")