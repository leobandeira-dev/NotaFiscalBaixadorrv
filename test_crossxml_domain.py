"""
Teste específico do domínio crossxml.com.br para identificar problemas
"""

import os
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def test_crossxml_domain():
    """Teste completo do domínio crossxml.com.br"""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    driver = None
    try:
        # Configurações otimizadas do Chrome (SEM --disable-javascript)
        options = Options()
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size=1024,768')
        
        # Criar driver
        chromedriver_path = "/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver"
        
        if os.path.exists(chromedriver_path):
            from selenium.webdriver.chrome.service import Service
            service = Service(chromedriver_path)
            driver = webdriver.Chrome(service=service, options=options)
        else:
            driver = webdriver.Chrome(options=options)
        
        driver.set_page_load_timeout(30)
        driver.implicitly_wait(5)
        
        logger.info("Driver criado com sucesso")
        
        # 1. Testar acesso ao domínio crossxml.com.br
        logger.info("Testando acesso ao crossxml.com.br...")
        driver.get("https://crossxml.com.br")
        time.sleep(3)
        
        current_url = driver.current_url
        page_title = driver.title
        logger.info(f"URL atual: {current_url}")
        logger.info(f"Título da página: {page_title}")
        
        # 2. Verificar se redirecionou para login
        if 'login' in current_url.lower() or 'login' in page_title.lower():
            logger.info("Redirecionado para página de login - autenticação necessária")
            
            # Tentar fazer login com dados de teste
            try:
                email_field = driver.find_element(By.ID, "email")
                password_field = driver.find_element(By.ID, "password")
                
                # Usar credenciais de teste
                email_field.send_keys("teste@crossxml.com.br")
                password_field.send_keys("123456")
                
                submit_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                submit_btn.click()
                
                time.sleep(3)
                
                new_url = driver.current_url
                logger.info(f"Após login: {new_url}")
                
                if 'login' not in new_url.lower():
                    logger.info("Login realizado com sucesso")
                else:
                    logger.info("Login falhou - credenciais inválidas")
                    return {
                        'success': False,
                        'issue': 'authentication_required',
                        'message': 'Domínio crossxml.com.br requer autenticação'
                    }
                    
            except Exception as e:
                logger.error(f"Erro no login: {e}")
                return {
                    'success': False,
                    'issue': 'authentication_required',
                    'message': 'Página de login encontrada mas não foi possível autenticar'
                }
        
        # 3. Tentar acessar diretamente a página de download
        logger.info("Testando acesso direto à página de download...")
        driver.get("https://crossxml.com.br/download")
        time.sleep(3)
        
        download_url = driver.current_url
        logger.info(f"URL da página de download: {download_url}")
        
        # 4. Verificar se há formulário de download
        try:
            # Procurar textarea para chaves
            textarea = driver.find_element(By.TAG_NAME, "textarea")
            logger.info("Formulário de download encontrado")
            
            # Inserir chave de teste
            test_key = "35250513516247000107550010000113401146202508"
            textarea.clear()
            textarea.send_keys(test_key)
            
            # Procurar botão de submit
            submit_buttons = driver.find_elements(By.CSS_SELECTOR, "button[type='submit'], input[type='submit']")
            
            if submit_buttons:
                submit_btn = submit_buttons[0]
                logger.info("Botão de download encontrado, clicando...")
                submit_btn.click()
                
                time.sleep(5)
                
                result_url = driver.current_url
                logger.info(f"Após submit: {result_url}")
                
                # Verificar se redirecionou para status
                if 'status' in result_url or 'download' in result_url:
                    return {
                        'success': True,
                        'issue': None,
                        'message': 'Sistema funcionando - download iniciado com sucesso',
                        'final_url': result_url
                    }
                else:
                    return {
                        'success': False,
                        'issue': 'no_redirect',
                        'message': 'Submit realizado mas não redirecionou para página de status'
                    }
            else:
                return {
                    'success': False,
                    'issue': 'no_submit_button',
                    'message': 'Formulário encontrado mas botão de submit não localizado'
                }
                
        except Exception as e:
            logger.error(f"Erro no formulário de download: {e}")
            
            # Verificar se ainda está na página de login
            if 'login' in driver.current_url.lower():
                return {
                    'success': False,
                    'issue': 'authentication_required',
                    'message': 'Redirecionado para login - usuário não autenticado'
                }
            else:
                return {
                    'success': False,
                    'issue': 'form_error',
                    'message': f'Erro no formulário: {e}'
                }
        
    except Exception as e:
        logger.error(f"Erro crítico: {e}")
        return {
            'success': False,
            'issue': 'critical_error',
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
    result = test_crossxml_domain()
    
    print("\n" + "="*60)
    print("🌐 TESTE DO DOMÍNIO CROSSXML.COM.BR")
    print("="*60)
    print(f"Status: {'✅ SUCESSO' if result['success'] else '❌ FALHA'}")
    print(f"Problema: {result.get('issue', 'N/A')}")
    print(f"Mensagem: {result['message']}")
    
    if 'final_url' in result:
        print(f"URL final: {result['final_url']}")
    
    print("="*60)
    
    # Diagnóstico específico
    if not result['success']:
        print("\n🔍 DIAGNÓSTICO:")
        issue = result.get('issue', '')
        
        if issue == 'authentication_required':
            print("- O domínio crossxml.com.br está exigindo autenticação")
            print("- Usuários precisam fazer login antes de acessar o download")
            print("- Isso é diferente do comportamento do domínio Replit")
            
        elif issue == 'no_redirect':
            print("- Formulário funciona mas não redireciona corretamente")
            print("- Possível problema com rotas ou sessões")
            
        elif issue == 'form_error':
            print("- Formulário não está funcionando corretamente")
            print("- Possível problema com JavaScript ou validação")
            
        print("\n💡 RECOMENDAÇÕES:")
        print("- Verificar configuração de autenticação no domínio customizado")
        print("- Confirmar se as rotas estão funcionando corretamente")
        print("- Testar manualmente no navegador para comparar comportamento")