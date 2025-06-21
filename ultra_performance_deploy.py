"""
Ultra Performance Deploy Configuration
Configurações otimizadas para máxima velocidade em ambiente de produção
"""
import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger(__name__)

class UltraPerformanceDeploy:
    """Configurações ultra-otimizadas para deploy em produção"""
    
    @staticmethod
    def is_deploy_environment():
        """Detecta se está rodando em ambiente de deploy"""
        indicators = {
            'replit_deployment': os.environ.get('REPLIT_DEPLOYMENT', '').lower() not in ['', 'none', 'false'],
            'not_localhost': os.environ.get('REPLIT_DEV_DOMAIN', '').find('localhost') == -1,
            'has_domains': bool(os.environ.get('REPLIT_DOMAINS')),
            'port_5000': os.environ.get('PORT', '5000') == '5000',
            'production_domain': any(domain in os.environ.get('REPLIT_DEV_DOMAIN', '') 
                                   for domain in ['replit.dev', 'crossxml.com.br'])
        }
        
        is_deploy = sum(indicators.values()) >= 3
        logger.info(f"🔍 Deploy detection: {is_deploy} | Indicators: {indicators}")
        return is_deploy
    
    @staticmethod
    def get_ultra_chrome_options():
        """Configurações Chrome ultra-otimizadas para deploy"""
        options = Options()
        
        # PERFORMANCE CRÍTICA PARA DEPLOY
        options.add_argument('--headless=new')  # Novo modo headless mais rápido
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')  # Não carregar imagens
        # options.add_argument('--disable-javascript')  # JavaScript necessário para o site funcionar
        
        # ULTRA VELOCIDADE - CONFIGURAÇÕES AGRESSIVAS
        options.add_argument('--aggressive-cache-discard')
        options.add_argument('--disable-background-networking')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-client-side-phishing-detection')
        options.add_argument('--disable-component-extensions-with-background-pages')
        options.add_argument('--disable-default-apps')
        options.add_argument('--disable-features=TranslateUI')
        options.add_argument('--disable-hang-monitor')
        options.add_argument('--disable-ipc-flooding-protection')
        options.add_argument('--disable-popup-blocking')
        options.add_argument('--disable-prompt-on-repost')
        options.add_argument('--disable-sync')
        options.add_argument('--disable-translate')
        options.add_argument('--disable-web-resources')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        
        # MEMÓRIA E RECURSOS ULTRA-LIMITADOS PARA DEPLOY
        options.add_argument('--memory-pressure-off')
        options.add_argument('--max_old_space_size=256')  # Limite JS
        options.add_argument('--aggressive-cache-discard')
        options.add_argument('--single-process')  # Um só processo
        options.add_argument('--disable-site-isolation-trials')
        
        # JANELA MÍNIMA PARA DEPLOY (economia extrema de recursos)
        options.add_argument('--window-size=400,300')  # Janela ultra-pequena
        
        # NETWORK ULTRA-OTIMIZADA
        options.add_argument('--aggressive-cache-discard')
        options.add_argument('--disable-background-networking')
        options.add_argument('--disable-dns-prefetch')
        options.add_argument('--disable-preconnect')
        
        # USER AGENT PARA EVITAR DETECÇÃO
        options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        logger.info("🚀 ULTRA Chrome options configured for DEPLOY SPEED")
        return options
    
    @staticmethod
    def get_ultra_timeouts():
        """Timeouts ultra-otimizados para deploy"""
        if UltraPerformanceDeploy.is_deploy_environment():
            return {
                'page_load': 8,      # Reduzido de 15 para 8
                'element_wait': 3,   # Reduzido de 12 para 3  
                'xml_button': 2,     # Reduzido de 10 para 2
                'download_poll': 0.5, # Reduzido de 2.0 para 0.5
                'max_attempts': 15   # Reduzido de 30 para 15
            }
        else:
            return {
                'page_load': 10,
                'element_wait': 5,
                'xml_button': 4,
                'download_poll': 1.0,
                'max_attempts': 20
            }
    
    @staticmethod
    def apply_ultra_performance():
        """Aplica todas as otimizações de performance"""
        is_deploy = UltraPerformanceDeploy.is_deploy_environment()
        timeouts = UltraPerformanceDeploy.get_ultra_timeouts()
        
        logger.info(f"🔧 ULTRA PERFORMANCE: Environment={'DEPLOY' if is_deploy else 'DEV'}")
        logger.info(f"⚡ Ultra timeouts: {timeouts}")
        
        return {
            'environment': 'DEPLOY' if is_deploy else 'DEV',
            'timeouts': timeouts,
            'chrome_optimized': True,
            'ultra_mode': True
        }

class ChromeDriverManager:
    """Gerenciador otimizado do ChromeDriver para deploy"""
    
    @staticmethod
    def get_optimized_driver():
        """Cria driver Chrome ultra-otimizado"""
        options = UltraPerformanceDeploy.get_ultra_chrome_options()
        
        # Download preferences mínimas
        downloads_dir = os.path.abspath('downloads')
        os.makedirs(downloads_dir, exist_ok=True)
        
        prefs = {
            "download.default_directory": downloads_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": False,  # Desabilitar para velocidade
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.notifications": 2
        }
        options.add_experimental_option("prefs", prefs)
        
        # Buscar chromedriver
        chromedriver_paths = [
            '/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver',
            '/usr/bin/chromedriver',
            '/usr/local/bin/chromedriver'
        ]
        
        chromedriver_path = None
        for path in chromedriver_paths:
            if os.path.exists(path):
                chromedriver_path = path
                break
        
        if chromedriver_path:
            logger.info(f"🚀 Creating ULTRA driver with: {chromedriver_path}")
            from selenium.webdriver.chrome.service import Service
            service = Service(chromedriver_path)
            return webdriver.Chrome(service=service, options=options)
        else:
            logger.info("🚀 Creating ULTRA driver with system chromedriver")
            return webdriver.Chrome(options=options)