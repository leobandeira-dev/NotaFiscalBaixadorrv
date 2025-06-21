"""
Deploy Robot Fix
Correções específicas para garantir que o robô Selenium funcione no ambiente de deploy
"""

import os
import logging
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)

class DeployRobotFix:
    """Correções específicas para robô Selenium em ambiente de deploy"""
    
    @staticmethod
    def is_deploy_environment():
        """Detecta se está em ambiente de deploy"""
        # Detecção mais robusta baseada nos indicadores disponíveis
        replit_domains = os.environ.get('REPLIT_DOMAINS', '')
        
        # Se tem domínio Replit ou crossxml, é deploy
        deploy_indicators = [
            'spock.replit.dev' in replit_domains,
            'crossxml.com.br' in replit_domains,
            replit_domains and '.' in replit_domains,  # Qualquer domínio válido
        ]
        
        return any(deploy_indicators)
    
    @staticmethod
    def get_deploy_chrome_options():
        """Configurações Chrome específicas para deploy"""
        options = Options()
        
        # Configurações essenciais para deploy
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')
        options.add_argument('--disable-javascript')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-ipc-flooding-protection')
        
        # Configurações de memória para deploy
        options.add_argument('--memory-pressure-off')
        options.add_argument('--max_old_space_size=4096')
        options.add_argument('--single-process')
        
        # Configurações de rede para deploy
        options.add_argument('--disable-background-networking')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-sync')
        
        # Janela otimizada para deploy
        options.add_argument('--window-size=800,600')
        
        # User agent para evitar detecção
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Download preferences para deploy
        prefs = {
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False,
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.notifications": 2
        }
        options.add_experimental_option("prefs", prefs)
        
        return options
    
    @staticmethod
    def get_deploy_timeouts():
        """Timeouts específicos para deploy - mais conservadores"""
        return {
            'page_load': 20,       # Tempo extra para carregamento no deploy
            'element_wait': 12,    # Espera estendida para elementos
            'xml_button': 10,      # Mais tempo para botão XML aparecer
            'download_poll': 2.0,  # Polling mais lento no deploy
            'max_attempts': 30     # Mais tentativas no deploy
        }
    
    @staticmethod
    def create_deploy_driver():
        """Cria driver específico para deploy"""
        try:
            logger.info("🚀 Creating DEPLOY-specific Chrome driver...")
            
            options = DeployRobotFix.get_deploy_chrome_options()
            
            # Buscar chromedriver no deploy
            chromedriver_paths = [
                '/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver',
                '/usr/bin/chromedriver',
                '/usr/local/bin/chromedriver',
                'chromedriver'
            ]
            
            driver = None
            for path in chromedriver_paths:
                try:
                    if os.path.exists(path):
                        logger.info(f"🔧 Using chromedriver: {path}")
                        service = Service(path)
                        driver = webdriver.Chrome(service=service, options=options)
                        break
                except Exception as e:
                    logger.debug(f"Failed with {path}: {e}")
                    continue
            
            if not driver:
                logger.info("🔧 Using default chromedriver")
                driver = webdriver.Chrome(options=options)
            
            # Configurações adicionais para deploy
            driver.set_page_load_timeout(15)
            
            logger.info("✅ DEPLOY Chrome driver created successfully")
            return driver
            
        except Exception as e:
            logger.error(f"❌ Failed to create deploy driver: {e}")
            return None
    
    @staticmethod
    def test_deploy_connection():
        """Testa conectividade no ambiente de deploy"""
        try:
            logger.info("🧪 Testing deploy robot connection...")
            
            driver = DeployRobotFix.create_deploy_driver()
            if not driver:
                return False
            
            # Teste básico de conectividade
            driver.get("https://meudanfe.com.br/")
            time.sleep(3)
            
            # Verificar se página carregou
            if "meudanfe" in driver.current_url.lower():
                logger.info("✅ Deploy robot connection successful")
                driver.quit()
                return True
            else:
                logger.error("❌ Deploy robot connection failed")
                driver.quit()
                return False
                
        except Exception as e:
            logger.error(f"❌ Deploy robot test failed: {e}")
            return False
    
    @staticmethod
    def apply_deploy_fixes():
        """Aplica todas as correções para deploy"""
        logger.info("🔧 Applying deploy robot fixes...")
        
        # Configurar variáveis de ambiente para deploy
        deploy_env = {
            'DISPLAY': ':99',
            'CHROME_NO_SANDBOX': '1',
            'CHROME_DISABLE_GPU': '1'
        }
        
        for key, value in deploy_env.items():
            os.environ[key] = value
            
        logger.info("✅ Deploy robot fixes applied")
        return True