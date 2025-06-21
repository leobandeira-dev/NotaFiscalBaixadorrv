"""
Correção específica do robô de download XML para ambiente de deploy
Identifica e corrige diferenças entre desenvolvimento e produção
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

class RobotDeployFix:
    """Correção específica para problemas do robô em deploy"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        
    def detect_environment_type(self):
        """Detecta se está em desenvolvimento ou deploy"""
        # Verificar variáveis de ambiente específicas
        is_deploy = (
            os.environ.get('REPLIT_DEPLOYMENT') == 'true' or
            'crossxml.com.br' in os.environ.get('REPLIT_DOMAINS', '') or
            os.environ.get('REPLIT_DEV_DOMAIN') != os.environ.get('REPLIT_DOMAINS')
        )
        
        env_type = "DEPLOY" if is_deploy else "DESENVOLVIMENTO"
        self.logger.info(f"Ambiente detectado: {env_type}")
        
        return is_deploy
    
    def get_optimized_chrome_options(self, is_deploy=False):
        """Obtém opções otimizadas do Chrome para cada ambiente"""
        options = Options()
        
        # Opções básicas obrigatórias
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        
        if is_deploy:
            # Configurações específicas para deploy (mais restritivas)
            self.logger.info("Aplicando configurações de DEPLOY")
            options.add_argument('--window-size=400,300')  # Janela menor
            options.add_argument('--memory-pressure-off')
            options.add_argument('--max_old_space_size=512')
            options.add_argument('--disable-background-networking')
            options.add_argument('--disable-background-timer-throttling')
            options.add_argument('--disable-backgrounding-occluded-windows')
            options.add_argument('--disable-renderer-backgrounding')
            options.add_argument('--disable-extensions')
            options.add_argument('--disable-plugins')
            options.add_argument('--disable-images')
            options.add_argument('--disable-javascript')  # Removido para funcionalidade
            options.add_argument('--single-process')
        else:
            # Configurações para desenvolvimento (mais conservadoras)
            self.logger.info("Aplicando configurações de DESENVOLVIMENTO")
            options.add_argument('--window-size=800,600')
            options.add_argument('--disable-extensions')
        
        # Diretório de download
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
    
    def get_environment_timeouts(self, is_deploy=False):
        """Retorna timeouts otimizados para cada ambiente"""
        if is_deploy:
            return {
                'page_load': 20,     # Mais tempo para deploy
                'element_wait': 8,   # Mais tempo para elementos
                'xml_button': 6,     # Mais tempo para botão XML
                'download_poll': 1.0, # Polling mais lento
                'max_attempts': 20   # Mais tentativas
            }
        else:
            return {
                'page_load': 10,
                'element_wait': 5,
                'xml_button': 3,
                'download_poll': 0.5,
                'max_attempts': 10
            }
    
    def create_robust_driver(self):
        """Cria driver robusto adaptado ao ambiente"""
        is_deploy = self.detect_environment_type()
        
        try:
            # Configurações otimizadas
            options = self.get_optimized_chrome_options(is_deploy)
            
            # Paths específicos do sistema
            chromedriver_path = "/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver"
            
            if os.path.exists(chromedriver_path):
                from selenium.webdriver.chrome.service import Service
                service = Service(chromedriver_path)
                driver = webdriver.Chrome(service=service, options=options)
            else:
                driver = webdriver.Chrome(options=options)
            
            # Timeouts específicos do ambiente
            timeouts = self.get_environment_timeouts(is_deploy)
            driver.set_page_load_timeout(timeouts['page_load'])
            driver.implicitly_wait(timeouts['element_wait'])
            
            self.logger.info(f"Driver criado com sucesso para ambiente {['DESENVOLVIMENTO', 'DEPLOY'][is_deploy]}")
            return driver, timeouts
            
        except Exception as e:
            self.logger.error(f"Erro criando driver: {e}")
            raise
    
    def test_robust_xml_download(self, invoice_key="44250485179240000239550020004175361171503396"):
        """Teste robusto de download XML com configurações específicas do ambiente"""
        driver = None
        
        try:
            # Criar driver otimizado
            driver, timeouts = self.create_robust_driver()
            
            self.logger.info(f"Iniciando teste com chave: {invoice_key[:20]}...")
            
            # Navegar para o site
            target_url = "https://meudanfe.com.br/"
            self.logger.info(f"Navegando para: {target_url}")
            driver.get(target_url)
            
            # Aguardar carregamento da página com timeout específico
            wait = WebDriverWait(driver, timeouts['element_wait'])
            
            # Localizar campo de entrada
            self.logger.info("Procurando campo de entrada...")
            input_element = wait.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'input[placeholder*="CHAVE"]'))
            )
            
            # Limpar e inserir chave
            self.logger.info("Inserindo chave de acesso...")
            input_element.clear()
            input_element.send_keys(invoice_key)
            
            # Aguardar um pouco para processamento
            time.sleep(1)
            
            # Procurar botão de busca/consulta
            self.logger.info("Procurando botão de consulta...")
            try:
                # Tentar diferentes seletores para o botão
                search_button = None
                selectors = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button.btn-primary',
                    'button.btn',
                    'input[value*="Consultar"]',
                    'button'
                ]
                
                for selector in selectors:
                    try:
                        buttons = driver.find_elements(By.CSS_SELECTOR, selector)
                        for btn in buttons:
                            if btn.is_displayed() and btn.is_enabled():
                                btn_text = btn.get_attribute('value') or btn.text
                                if any(word in btn_text.lower() for word in ['consultar', 'buscar', 'submit', 'pesquisar']):
                                    search_button = btn
                                    break
                        if search_button:
                            break
                    except:
                        continue
                
                if not search_button:
                    # Fallback: clicar no primeiro botão visível
                    buttons = driver.find_elements(By.TAG_NAME, 'button')
                    for btn in buttons:
                        if btn.is_displayed() and btn.is_enabled():
                            search_button = btn
                            break
                
                if search_button:
                    search_button.click()
                else:
                    raise Exception("Nenhum botão de consulta encontrado")
            except Exception as e:
                self.logger.error(f"Erro ao procurar botão: {e}")
                # Tentar submeter o formulário diretamente
                input_element.submit()
            
            # Aguardar resultado com timeout maior
            self.logger.info("Aguardando resultado da consulta...")
            time.sleep(timeouts['xml_button'])
            
            # Procurar botão de download XML
            self.logger.info("Procurando botão de download XML...")
            xml_button = None
            
            # Tentar diferentes estratégias para encontrar botão XML
            xml_selectors = [
                "//button[contains(text(), 'XML')]",
                "//a[contains(text(), 'XML')]",
                "//input[@value='XML']",
                "//button[contains(@class, 'xml')]",
                "//a[contains(@class, 'xml')]"
            ]
            
            for selector in xml_selectors:
                try:
                    xml_button = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
                    if xml_button:
                        break
                except:
                    continue
            
            # Fallback: procurar por texto contendo "xml" em qualquer elemento clicável
            if not xml_button:
                try:
                    all_clickable = driver.find_elements(By.XPATH, "//button | //a | //input[@type='button']")
                    for element in all_clickable:
                        if element.is_displayed() and element.is_enabled():
                            text = (element.text or element.get_attribute('value') or '').lower()
                            if 'xml' in text:
                                xml_button = element
                                break
                except:
                    pass
            
            if not xml_button:
                raise Exception("Botão XML não encontrado")
            
            # Clicar no botão XML
            self.logger.info("Clicando no botão XML...")
            xml_button.click()
            
            # Aguardar download
            self.logger.info("Aguardando download...")
            time.sleep(3)
            
            # Verificar se arquivo foi baixado
            downloads_dir = os.path.join(os.getcwd(), 'downloads')
            files = os.listdir(downloads_dir)
            xml_files = [f for f in files if f.endswith('.xml')]
            
            if xml_files:
                self.logger.info(f"✅ Download bem-sucedido: {xml_files[-1]}")
                return {
                    'success': True,
                    'file': xml_files[-1],
                    'message': 'XML baixado com sucesso'
                }
            else:
                self.logger.warning("Nenhum arquivo XML encontrado")
                return {
                    'success': False,
                    'message': 'Download não detectado'
                }
            
        except TimeoutException as e:
            self.logger.error(f"Timeout durante operação: {e}")
            return {
                'success': False,
                'message': f'Timeout: {e}'
            }
        except WebDriverException as e:
            self.logger.error(f"Erro do WebDriver: {e}")
            return {
                'success': False,
                'message': f'WebDriver: {e}'
            }
        except Exception as e:
            self.logger.error(f"Erro inesperado: {e}")
            return {
                'success': False,
                'message': f'Erro: {e}'
            }
        finally:
            if driver:
                try:
                    driver.quit()
                    self.logger.info("Driver encerrado")
                except:
                    pass
    
    def fix_automation_for_deploy(self):
        """Aplica correções específicas para o ambiente de deploy"""
        is_deploy = self.detect_environment_type()
        
        if is_deploy:
            self.logger.info("🔧 APLICANDO CORREÇÕES PARA DEPLOY")
            
            # 1. Verificar e criar diretórios necessários
            dirs_to_create = ['downloads', 'temp', 'logs']
            for dir_name in dirs_to_create:
                dir_path = os.path.join(os.getcwd(), dir_name)
                os.makedirs(dir_path, exist_ok=True)
                self.logger.info(f"Diretório criado/verificado: {dir_path}")
            
            # 2. Configurar variáveis de ambiente para deploy
            deploy_env_vars = {
                'DISPLAY': ':99',
                'CHROME_DISABLE_GPU': '1',
                'CHROME_NO_SANDBOX': '1'
            }
            
            for key, value in deploy_env_vars.items():
                os.environ[key] = value
                self.logger.info(f"Variável configurada: {key}={value}")
            
            # 3. Testar conexão básica
            connection_test = self.test_basic_connection()
            if not connection_test['success']:
                self.logger.error(f"Teste de conexão falhou: {connection_test['message']}")
                return False
            
            self.logger.info("✅ Correções para deploy aplicadas com sucesso")
            return True
        else:
            self.logger.info("Ambiente de desenvolvimento - sem correções necessárias")
            return True
    
    def test_basic_connection(self):
        """Teste básico de conectividade"""
        try:
            import requests
            response = requests.get("https://meudanfe.com.br/", timeout=10)
            if response.status_code == 200:
                return {'success': True, 'message': 'Conectividade OK'}
            else:
                return {'success': False, 'message': f'HTTP {response.status_code}'}
        except Exception as e:
            return {'success': False, 'message': f'Erro de conexão: {e}'}
    
    def run_complete_diagnosis(self):
        """Executa diagnóstico completo e aplica correções"""
        self.logger.info("🚀 INICIANDO DIAGNÓSTICO COMPLETO DO ROBÔ XML")
        
        # 1. Detectar ambiente
        is_deploy = self.detect_environment_type()
        
        # 2. Aplicar correções específicas
        fix_result = self.fix_automation_for_deploy()
        
        # 3. Testar robô com configurações otimizadas
        if fix_result:
            self.logger.info("🧪 TESTANDO ROBÔ COM CONFIGURAÇÕES OTIMIZADAS")
            test_result = self.test_robust_xml_download()
            
            if test_result['success']:
                self.logger.info("✅ ROBÔ FUNCIONANDO CORRETAMENTE")
                return {
                    'success': True,
                    'environment': 'DEPLOY' if is_deploy else 'DESENVOLVIMENTO',
                    'test_result': test_result,
                    'message': 'Robô funcionando após correções'
                }
            else:
                self.logger.error("❌ ROBÔ AINDA COM PROBLEMAS")
                return {
                    'success': False,
                    'environment': 'DEPLOY' if is_deploy else 'DESENVOLVIMENTO',
                    'test_result': test_result,
                    'message': 'Robô com falhas mesmo após correções'
                }
        else:
            return {
                'success': False,
                'message': 'Falha ao aplicar correções para deploy'
            }

if __name__ == "__main__":
    robot_fix = RobotDeployFix()
    result = robot_fix.run_complete_diagnosis()
    
    print("\n" + "="*60)
    print("📊 RESULTADO FINAL DO DIAGNÓSTICO")
    print("="*60)
    print(f"Sucesso: {'✅' if result['success'] else '❌'}")
    print(f"Ambiente: {result.get('environment', 'N/A')}")
    print(f"Mensagem: {result['message']}")
    
    if 'test_result' in result:
        print(f"Teste: {result['test_result']['message']}")