"""
Otimizações específicas para ambiente deploy
Detecta automaticamente se está em produção e aplica configurações otimizadas
"""
import os
import logging
import time
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger(__name__)

class DeployOptimizer:
    """Otimizações específicas para ambiente deploy vs desenvolvimento"""
    
    @staticmethod
    def is_deploy_environment():
        """Detecta se está rodando no ambiente deploy"""
        # Check for custom domain usage (crossxml.com.br)
        from flask import has_request_context, request
        is_custom_domain = False
        
        if has_request_context():
            is_custom_domain = 'crossxml.com.br' in request.host
        
        return (
            os.environ.get('REPLIT_DEPLOYMENT') or 
            os.environ.get('REPL_ID') or 
            '/home/runner' in os.getcwd() or
            is_custom_domain  # Force deploy optimizations for custom domain
        )
    
    @staticmethod
    def get_optimized_chrome_options():
        """Retorna opções do Chrome otimizadas para o ambiente"""
        chrome_options = Options()
        
        # Opções básicas para todos os ambientes
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-gpu')
        
        if DeployOptimizer.is_deploy_environment():
            logger.info("🚀 Aplicando otimizações para ambiente DEPLOY")
            
            # DEPLOY: Máxima otimização de recursos
            chrome_options.add_argument('--window-size=600,400')  # Menor ainda
            chrome_options.add_argument('--memory-pressure-off')
            chrome_options.add_argument('--max_old_space_size=2048')  # Reduzido
            chrome_options.add_argument('--single-process')
            chrome_options.add_argument('--no-zygote')
            
            # DEPLOY: Desabilitar recursos desnecessários
            chrome_options.add_argument('--disable-background-networking')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-client-side-phishing-detection')
            chrome_options.add_argument('--disable-component-extensions-with-background-pages')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-css-animations')
            chrome_options.add_argument('--disable-transitions')
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--silent')
            
            # DEPLOY: Otimizações de rede para compensar latência
            chrome_options.add_argument('--aggressive-cache-discard')
            chrome_options.add_argument('--disable-domain-reliability')
            chrome_options.add_argument('--disable-sync')
            
        else:
            logger.info("⚡ Aplicando otimizações para ambiente DESENVOLVIMENTO")
            
            # DESENVOLVIMENTO: Configuração mais conservadora
            chrome_options.add_argument('--window-size=800,600')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            
        return chrome_options
    
    @staticmethod
    def get_optimized_timeouts():
        """Retorna timeouts otimizados para cada ambiente"""
        if DeployOptimizer.is_deploy_environment():
            return {
                'page_load': 8,      # Aumentado para compensar latência de rede
                'element_wait': 5,   # Aumentado para ambiente deploy
                'xml_button': 4,     # Aumentado para ambiente deploy
                'download_wait': 1.2, # Aumentado para ambiente deploy
                'download_poll': 0.8,  # Aumentado para ambiente deploy
                'max_attempts': 15   # Mais tentativas no deploy
            }
        else:
            return {
                'page_load': 5,      # Mais rápido em desenvolvimento
                'element_wait': 3,   # Mais rápido em desenvolvimento
                'xml_button': 2,     # Mais rápido em desenvolvimento
                'download_wait': 0.8, # Mais rápido em desenvolvimento
                'download_poll': 0.5,  # Mais rápido em desenvolvimento
                'max_attempts': 10   # Menos tentativas necessárias
            }
    
    @staticmethod
    def log_environment_info():
        """Log informações do ambiente para debugging"""
        env_type = "DEPLOY" if DeployOptimizer.is_deploy_environment() else "DESENVOLVIMENTO"
        timeouts = DeployOptimizer.get_optimized_timeouts()
        
        logger.info(f"🎯 Ambiente detectado: {env_type}")
        logger.info(f"⏱️  Timeouts otimizados: {timeouts}")
        
        if DeployOptimizer.is_deploy_environment():
            logger.info("💡 Otimizações deploy ativas:")
            logger.info("   - Recursos mínimos do Chrome")
            logger.info("   - Timeouts aumentados para latência de rede")
            logger.info("   - Máximas tentativas de download")
            logger.info("   - Cache agressivo desabilitado")