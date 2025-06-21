"""
Sistema de detecção e correção para ambiente de produção
Especificamente para resolver problemas no domínio crossxml.com.br
"""

import os
import logging

logger = logging.getLogger(__name__)

class ProductionFix:
    """Correções específicas para ambiente de produção"""
    
    @staticmethod
    def is_production_environment():
        """Detecta se está rodando em ambiente de produção"""
        # Múltiplos indicadores de produção
        production_indicators = [
            # Domínio customizado
            'crossxml.com.br' in str(os.environ.get('REPLIT_DOMAINS', '')),
            'crossxml.com.br' in str(os.environ.get('REPLIT_DEV_DOMAIN', '')),
            
            # Indicadores de deployment
            bool(os.environ.get('REPLIT_DEPLOYMENT')),
            'deployed' in str(os.environ.get('REPLIT_ENVIRONMENT', '')).lower(),
            
            # Verificação por porta (produção geralmente usa 5000)
            os.environ.get('PORT') == '5000',
            
            # Verificação se não é desenvolvimento local
            'localhost' not in str(os.environ.get('REPLIT_DEV_DOMAIN', '')),
            '127.0.0.1' not in str(os.environ.get('REPLIT_DEV_DOMAIN', '')),
        ]
        
        is_prod = any(production_indicators)
        logger.info(f"🔍 Production detection: {is_prod}")
        logger.info(f"🔍 Indicators checked: {dict(zip(['crossxml_domains', 'crossxml_dev', 'deployment', 'environment', 'port_5000', 'not_localhost', 'not_127'], production_indicators))}")
        
        return is_prod
    
    @staticmethod
    def get_production_timeouts():
        """Timeouts robustos para ambiente de produção"""
        return {
            'page_load': 15,        # Tempo para carregar página
            'element_wait': 12,     # Tempo para encontrar elementos
            'xml_button': 10,       # Tempo para botão XML aparecer
            'download_poll': 2.0,   # Intervalo entre verificações
            'max_attempts': 30      # Máximo de tentativas
        }
    
    @staticmethod
    def get_production_chrome_options():
        """Opções Chrome específicas para produção"""
        from selenium import webdriver
        
        chrome_options = webdriver.ChromeOptions()
        
        # Configurações básicas de produção
        chrome_options.add_argument('--headless=new')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--window-size=1024,768')
        
        # Configurações de estabilidade
        chrome_options.add_argument('--disable-background-timer-throttling')
        chrome_options.add_argument('--disable-backgrounding-occluded-windows')
        chrome_options.add_argument('--disable-renderer-backgrounding')
        chrome_options.add_argument('--disable-features=TranslateUI')
        chrome_options.add_argument('--disable-ipc-flooding-protection')
        
        # Configurações de memória
        chrome_options.add_argument('--memory-pressure-off')
        chrome_options.add_argument('--max_old_space_size=4096')
        
        # User agent confiável
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        logger.info("🔧 Production Chrome options configured")
        return chrome_options
    
    @staticmethod
    def apply_production_fixes():
        """Aplica todas as correções de produção"""
        try:
            if ProductionFix.is_production_environment():
                logger.info("🚀 PRODUCTION ENVIRONMENT DETECTED - Applying fixes...")
                
                # Log informações do ambiente
                logger.info(f"🌍 Domain: {os.environ.get('REPLIT_DEV_DOMAIN', 'Not set')}")
                logger.info(f"🌍 Domains: {os.environ.get('REPLIT_DOMAINS', 'Not set')}")
                logger.info(f"🌍 Deployment: {os.environ.get('REPLIT_DEPLOYMENT', 'Not set')}")
                logger.info(f"🌍 Port: {os.environ.get('PORT', 'Not set')}")
                
                return True
            else:
                logger.info("🔧 Development environment detected")
                return False
                
        except Exception as e:
            logger.error(f"Error in production fixes: {e}")
            return False