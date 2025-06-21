"""
Correção específica para problemas de produção do robô XML
Resolve diferenças entre ambiente de desenvolvimento e deploy
"""

import os
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.keys import Keys

class ProductionFix:
    """Correções específicas para ambiente de produção"""
    
    @staticmethod
    def is_production_environment():
        """Detecta se está em ambiente de produção"""
        return (
            os.environ.get('REPLIT_DEPLOYMENT') == 'true' or
            'crossxml.com.br' in os.environ.get('REPLIT_DOMAINS', '') or
            os.environ.get('REPLIT_DEV_DOMAIN') != os.environ.get('REPLIT_DOMAINS')
        )
    
    @staticmethod
    def get_production_chrome_options():
        """Opções otimizadas do Chrome para produção"""
        options = Options()
        
        # Configurações básicas
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        
        # Configurações específicas para produção
        options.add_argument('--window-size=800,600')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')
        # options.add_argument('--disable-javascript') # Removido para manter funcionalidade
        options.add_argument('--single-process')
        options.add_argument('--memory-pressure-off')
        options.add_argument('--max_old_space_size=512')
        
        # Diretório de downloads
        downloads_dir = os.path.join(os.getcwd(), 'downloads')
        os.makedirs(downloads_dir, exist_ok=True)
        
        prefs = {
            "download.default_directory": downloads_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)
        
        return options
    
    @staticmethod
    def create_production_driver():
        """Cria driver otimizado para produção"""
        try:
            options = ProductionFix.get_production_chrome_options()
            
            # Path específico do ChromeDriver
            chromedriver_path = "/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver"
            
            if os.path.exists(chromedriver_path):
                from selenium.webdriver.chrome.service import Service
                service = Service(chromedriver_path)
                driver = webdriver.Chrome(service=service, options=options)
            else:
                driver = webdriver.Chrome(options=options)
            
            # Timeouts otimizados para produção
            driver.set_page_load_timeout(30)
            driver.implicitly_wait(10)
            
            return driver
            
        except Exception as e:
            logging.error(f"Erro criando driver de produção: {e}")
            raise
    
    @staticmethod
    def robust_element_interaction(driver, element_selectors, action_type="click", input_text=None, timeout=10):
        """
        Interação robusta com elementos da página
        
        Args:
            driver: WebDriver instance
            element_selectors: Lista de seletores para tentar
            action_type: Tipo de ação ("click", "input", "submit")
            input_text: Texto para inserir (se action_type="input")
            timeout: Timeout para encontrar elemento
        
        Returns:
            True se sucesso, False caso contrário
        """
        wait = WebDriverWait(driver, timeout)
        
        for selector_info in element_selectors:
            try:
                # Seletor pode ser string ou dict com by/value
                if isinstance(selector_info, str):
                    by_type = By.CSS_SELECTOR
                    selector = selector_info
                else:
                    by_type = selector_info.get('by', By.CSS_SELECTOR)
                    selector = selector_info.get('selector')
                
                # Tentar encontrar elemento
                element = wait.until(EC.presence_of_element_located((by_type, selector)))
                
                if element and element.is_displayed() and element.is_enabled():
                    if action_type == "click":
                        # Tentar diferentes métodos de clique
                        try:
                            element.click()
                        except:
                            # Fallback: JavaScript click
                            driver.execute_script("arguments[0].click();", element)
                        
                        logging.info(f"Clique realizado com sucesso: {selector}")
                        return True
                        
                    elif action_type == "input" and input_text:
                        element.clear()
                        element.send_keys(input_text)
                        logging.info(f"Texto inserido com sucesso: {selector}")
                        return True
                        
                    elif action_type == "submit":
                        element.submit()
                        logging.info(f"Submit realizado com sucesso: {selector}")
                        return True
                
            except Exception as e:
                logging.debug(f"Falha com seletor {selector}: {e}")
                continue
        
        logging.error(f"Nenhum seletor funcionou para ação: {action_type}")
        return False
    
    @staticmethod
    def production_xml_download(driver, invoice_key, timeout=30):
        """
        Download robusto de XML em ambiente de produção
        
        Args:
            driver: WebDriver instance
            invoice_key: Chave da nota fiscal
            timeout: Timeout total para operação
        
        Returns:
            Dict com resultado da operação
        """
        try:
            # 1. Navegar para o site
            logging.info("Navegando para o site...")
            driver.get("https://meudanfe.com.br/")
            time.sleep(3)
            
            # 2. Encontrar e preencher campo da chave
            logging.info("Procurando campo da chave...")
            input_selectors = [
                'input[placeholder*="CHAVE"]',
                'input[placeholder*="chave"]',
                'input[name*="chave"]',
                'input[id*="chave"]',
                'input[type="text"]'
            ]
            
            success = ProductionFix.robust_element_interaction(
                driver, 
                input_selectors, 
                "input", 
                invoice_key, 
                timeout=10
            )
            
            if not success:
                return {'success': False, 'message': 'Campo da chave não encontrado'}
            
            # 3. Encontrar e clicar botão de consulta
            logging.info("Procurando botão de consulta...")
            
            # Estratégia robusta: tentar múltiplas abordagens
            search_success = False
            
            # Abordagem 1: Botões específicos
            search_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button.btn-primary',
                'button.btn',
                'button'
            ]
            
            for selector in search_selectors:
                try:
                    buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                    for btn in buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            btn_text = (btn.text or btn.get_attribute('value') or '').lower()
                            if any(word in btn_text for word in ['consultar', 'buscar', 'pesquisar', 'submit']):
                                try:
                                    btn.click()
                                    search_success = True
                                    logging.info(f"Botão de consulta clicado: {btn_text}")
                                    break
                                except:
                                    # Fallback: JavaScript click
                                    driver.execute_script("arguments[0].click();", btn)
                                    search_success = True
                                    break
                    if search_success:
                        break
                except:
                    continue
            
            # Abordagem 2: Submit do formulário
            if not search_success:
                try:
                    input_field = driver.find_element(By.CSS_SELECTOR, 'input[placeholder*="CHAVE"]')
                    input_field.send_keys(Keys.RETURN)
                    search_success = True
                    logging.info("Consulta enviada via ENTER")
                except:
                    pass
            
            if not search_success:
                return {'success': False, 'message': 'Botão de consulta não encontrado'}
            
            # 4. Aguardar resultado
            logging.info("Aguardando resultado da consulta...")
            time.sleep(5)
            
            # 5. Procurar botão XML
            logging.info("Procurando botão XML...")
            
            xml_success = False
            xml_selectors = [
                {'by': By.XPATH, 'selector': "//button[contains(text(), 'XML')]"},
                {'by': By.XPATH, 'selector': "//a[contains(text(), 'XML')]"},
                {'by': By.XPATH, 'selector': "//input[@value='XML']"},
                {'by': By.CSS_SELECTOR, 'selector': 'button[value*="xml"]'},
                {'by': By.CSS_SELECTOR, 'selector': 'a[href*="xml"]'}
            ]
            
            for selector_info in xml_selectors:
                try:
                    by_type = selector_info['by']
                    selector = selector_info['selector']
                    
                    elements = driver.find_elements(by_type, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            try:
                                element.click()
                                xml_success = True
                                logging.info("Botão XML clicado com sucesso")
                                break
                            except:
                                # Fallback: JavaScript click
                                driver.execute_script("arguments[0].click();", element)
                                xml_success = True
                                break
                    if xml_success:
                        break
                except:
                    continue
            
            # Fallback final: procurar qualquer elemento com "xml"
            if not xml_success:
                try:
                    all_elements = driver.find_elements(By.XPATH, "//*[contains(text(), 'XML') or contains(@value, 'XML') or contains(@href, 'xml')]")
                    for element in all_elements:
                        if element.is_displayed() and element.is_enabled():
                            try:
                                element.click()
                                xml_success = True
                                logging.info("Botão XML encontrado via fallback")
                                break
                            except:
                                continue
                except:
                    pass
            
            if not xml_success:
                return {'success': False, 'message': 'Botão XML não encontrado'}
            
            # 6. Aguardar download
            logging.info("Aguardando download...")
            time.sleep(5)
            
            # 7. Verificar arquivo baixado
            downloads_dir = os.path.join(os.getcwd(), 'downloads')
            if os.path.exists(downloads_dir):
                files = os.listdir(downloads_dir)
                xml_files = [f for f in files if f.endswith('.xml')]
                
                if xml_files:
                    logging.info(f"XML baixado com sucesso: {xml_files[-1]}")
                    return {
                        'success': True,
                        'message': 'XML baixado com sucesso',
                        'file': xml_files[-1]
                    }
            
            return {'success': False, 'message': 'Arquivo XML não foi baixado'}
            
        except Exception as e:
            logging.error(f"Erro durante download: {e}")
            return {'success': False, 'message': f'Erro: {e}'}
    
    @staticmethod
    def apply_production_fixes():
        """Aplica todas as correções necessárias para produção"""
        
        if ProductionFix.is_production_environment():
            logging.info("🔧 Aplicando correções para ambiente de produção")
            
            # Criar diretórios necessários
            dirs = ['downloads', 'temp', 'logs']
            for dir_name in dirs:
                dir_path = os.path.join(os.getcwd(), dir_name)
                os.makedirs(dir_path, exist_ok=True)
            
            # Configurar variáveis de ambiente
            env_vars = {
                'DISPLAY': ':99',
                'CHROME_DISABLE_GPU': '1',
                'CHROME_NO_SANDBOX': '1'
            }
            
            for key, value in env_vars.items():
                os.environ[key] = value
            
            logging.info("✅ Correções de produção aplicadas")
            return True
        else:
            logging.info("Ambiente de desenvolvimento - sem correções necessárias")
            return True

def test_production_download():
    """Teste completo do sistema em produção"""
    
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Aplicar correções
    ProductionFix.apply_production_fixes()
    
    driver = None
    try:
        # Criar driver de produção
        driver = ProductionFix.create_production_driver()
        logger.info("Driver de produção criado com sucesso")
        
        # Testar download
        invoice_key = "44250485179240000239550020004175361171503396"
        result = ProductionFix.production_xml_download(driver, invoice_key)
        
        return result
        
    except Exception as e:
        logger.error(f"Erro no teste: {e}")
        return {'success': False, 'message': f'Erro: {e}'}
    finally:
        if driver:
            try:
                driver.quit()
                logger.info("Driver encerrado")
            except:
                pass

if __name__ == "__main__":
    result = test_production_download()
    
    print("\n" + "="*60)
    print("🚀 TESTE DE PRODUÇÃO DO ROBÔ XML")
    print("="*60)
    print(f"Resultado: {'✅ SUCESSO' if result['success'] else '❌ FALHA'}")
    print(f"Mensagem: {result['message']}")
    
    if 'file' in result:
        print(f"Arquivo: {result['file']}")
    
    print("\n" + "="*60)