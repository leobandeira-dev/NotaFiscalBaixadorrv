"""
Correções para ambiente de produção - Chrome WebDriver
Diagnóstico e fixes para problemas de download em produção
"""

import os
import subprocess
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)

def diagnose_production_environment():
    """Diagnosticar ambiente de produção para Chrome WebDriver"""
    
    print("=== DIAGNÓSTICO DO AMBIENTE DE PRODUÇÃO ===")
    
    # 1. Verificar se Chrome está instalado
    try:
        result = subprocess.run(['google-chrome', '--version'], capture_output=True, text=True)
        print(f"✅ Chrome Version: {result.stdout.strip()}")
    except:
        try:
            result = subprocess.run(['chromium', '--version'], capture_output=True, text=True)
            print(f"✅ Chromium Version: {result.stdout.strip()}")
        except:
            print("❌ Chrome/Chromium não encontrado")
    
    # 2. Verificar ChromeDriver
    chromedriver_paths = [
        '/nix/store/*/bin/chromedriver',
        '/usr/bin/chromedriver',
        '/usr/local/bin/chromedriver',
        'chromedriver'
    ]
    
    for path in chromedriver_paths:
        if '*' in path:
            # Expandir wildcard
            import glob
            matches = glob.glob(path)
            for match in matches:
                if os.path.exists(match):
                    try:
                        result = subprocess.run([match, '--version'], capture_output=True, text=True)
                        print(f"✅ ChromeDriver encontrado: {match}")
                        print(f"   Versão: {result.stdout.strip()}")
                        break
                    except:
                        pass
        else:
            if os.path.exists(path):
                try:
                    result = subprocess.run([path, '--version'], capture_output=True, text=True)
                    print(f"✅ ChromeDriver encontrado: {path}")
                    print(f"   Versão: {result.stdout.strip()}")
                    break
                except:
                    pass
    
    # 3. Verificar diretório de downloads
    downloads_dir = os.path.abspath('downloads')
    print(f"📁 Diretório downloads: {downloads_dir}")
    print(f"   Existe: {os.path.exists(downloads_dir)}")
    if os.path.exists(downloads_dir):
        print(f"   Permissões: {oct(os.stat(downloads_dir).st_mode)[-3:]}")
    
    # 4. Testar inicialização do WebDriver
    print("\n=== TESTE DE WEBDRIVER ===")
    try:
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        # Tentar com WebDriver Manager primeiro
        try:
            from webdriver_manager.chrome import ChromeDriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
            print("✅ WebDriver inicializado com WebDriverManager")
            driver.quit()
        except Exception as e:
            print(f"❌ WebDriverManager falhou: {e}")
            
            # Tentar com ChromeDriver do sistema
            try:
                driver = webdriver.Chrome(options=chrome_options)
                print("✅ WebDriver inicializado com ChromeDriver do sistema")
                driver.quit()
            except Exception as e2:
                print(f"❌ ChromeDriver do sistema falhou: {e2}")
    
    except Exception as e:
        print(f"❌ Erro crítico no WebDriver: {e}")

def create_production_automation():
    """Criar versão do automation otimizada para produção"""
    
    automation_code = '''
import os
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

class ProductionInvoiceDownloader:
    def __init__(self):
        self.driver = None
    
    def setup_driver(self):
        """Setup Chrome WebDriver otimizado para produção"""
        try:
            logger.info("Configurando WebDriver para produção...")
            
            downloads_dir = os.path.abspath('downloads')
            os.makedirs(downloads_dir, exist_ok=True)
            
            chrome_options = Options()
            # Configurações essenciais para produção
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-web-security')
            chrome_options.add_argument('--allow-running-insecure-content')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-background-networking')
            chrome_options.add_argument('--no-first-run')
            chrome_options.add_argument('--disable-default-apps')
            
            # Configurações de download
            prefs = {
                "download.default_directory": downloads_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False,
                "profile.default_content_settings.popups": 0,
                "profile.default_content_setting_values.automatic_downloads": 1
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Tentar múltiplas estratégias de inicialização
            driver_initialized = False
            
            # Estratégia 1: WebDriverManager
            try:
                from webdriver_manager.chrome import ChromeDriverManager
                service = Service(ChromeDriverManager().install())
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                driver_initialized = True
                logger.info("✅ WebDriver inicializado com WebDriverManager")
            except Exception as e:
                logger.warning(f"WebDriverManager falhou: {e}")
            
            # Estratégia 2: ChromeDriver do sistema
            if not driver_initialized:
                try:
                    self.driver = webdriver.Chrome(options=chrome_options)
                    driver_initialized = True
                    logger.info("✅ WebDriver inicializado com ChromeDriver do sistema")
                except Exception as e:
                    logger.warning(f"ChromeDriver do sistema falhou: {e}")
            
            # Estratégia 3: Caminhos específicos do Nix
            if not driver_initialized:
                import glob
                nix_paths = glob.glob('/nix/store/*/bin/chromedriver')
                for path in nix_paths:
                    try:
                        service = Service(path)
                        self.driver = webdriver.Chrome(service=service, options=chrome_options)
                        driver_initialized = True
                        logger.info(f"✅ WebDriver inicializado com Nix path: {path}")
                        break
                    except Exception as e:
                        logger.warning(f"Nix path {path} falhou: {e}")
            
            if not driver_initialized:
                raise Exception("Todas as estratégias de inicialização do WebDriver falharam")
            
            # Configurar timeouts
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(10)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao configurar WebDriver: {e}")
            return False
    
    def test_connection(self):
        """Testar conexão do sistema"""
        try:
            if not self.setup_driver():
                return {"status": "error", "message": "Falha ao inicializar WebDriver"}
            
            logger.info("Testando conexão com sistema de notas fiscais...")
            self.driver.get("https://meudanfe.com.br/")
            
            # Verificar se a página carregou
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            
            title = self.driver.title
            url = self.driver.current_url
            
            self.cleanup()
            
            return {
                "status": "success",
                "message": f"Conexão estabelecida - Título: {title}",
                "url": url
            }
            
        except Exception as e:
            logger.error(f"Erro no teste de conexão: {e}")
            self.cleanup()
            return {"status": "error", "message": str(e)}
    
    def cleanup(self):
        """Limpar recursos"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver fechado")
            except:
                pass
            self.driver = None
'''
    
    with open('production_automation.py', 'w') as f:
        f.write(automation_code)
    
    print("✅ Arquivo production_automation.py criado")

if __name__ == "__main__":
    diagnose_production_environment()
    create_production_automation()