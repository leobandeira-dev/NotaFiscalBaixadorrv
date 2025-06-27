"""
Solução Completa para Problemas de Performance Deploy vs Desenvolvimento
Implementa otimizações específicas e correções direcionadas
"""
import os
import time
import logging
from optimization_deploy import DeployOptimizer

logger = logging.getLogger(__name__)

class PerformanceSolution:
    """Implementa soluções específicas para problemas de performance"""
    
    @staticmethod
    def apply_deploy_performance_fixes():
        """Aplica correções específicas para ambiente deploy"""
        
        # Detecta se está em deploy
        is_deploy = DeployOptimizer.is_deploy_environment()
        
        if not is_deploy:
            logger.info("⚡ Ambiente DESENVOLVIMENTO detectado - usando configurações padrão")
            return {
                'environment': 'DESENVOLVIMENTO',
                'optimizations_applied': ['configuracao_padrao'],
                'expected_performance': 'otima'
            }
        
        logger.info("🚀 Ambiente DEPLOY detectado - aplicando otimizações específicas...")
        
        optimizations = []
        
        # 1. Otimizações de Chrome para deploy
        chrome_fixes = PerformanceSolution._apply_chrome_deploy_fixes()
        optimizations.extend(chrome_fixes)
        
        # 2. Otimizações de rede para deploy
        network_fixes = PerformanceSolution._apply_network_deploy_fixes()
        optimizations.extend(network_fixes)
        
        # 3. Otimizações de sistema para deploy
        system_fixes = PerformanceSolution._apply_system_deploy_fixes()
        optimizations.extend(system_fixes)
        
        logger.info(f"✅ Aplicadas {len(optimizations)} otimizações para deploy")
        
        return {
            'environment': 'DEPLOY',
            'optimizations_applied': optimizations,
            'expected_performance': 'melhorada_significativamente'
        }
    
    @staticmethod
    def _apply_chrome_deploy_fixes():
        """Aplica correções específicas do Chrome para deploy"""
        fixes = []
        
        # Configura variáveis de ambiente para Chrome otimizado
        os.environ['CHROME_NO_SANDBOX'] = '1'
        os.environ['CHROME_DISABLE_GPU'] = '1'
        os.environ['CHROME_SINGLE_PROCESS'] = '1'
        fixes.append('chrome_environment_variables')
        
        # Configurações de memória específicas para deploy
        os.environ['CHROME_MAX_MEMORY'] = '512'
        fixes.append('chrome_memory_limits')
        
        logger.info("🔧 Chrome otimizado para ambiente deploy")
        return fixes
    
    @staticmethod
    def _apply_network_deploy_fixes():
        """Aplica correções de rede para deploy"""
        fixes = []
        
        # Configurações de timeout específicas para deploy
        os.environ['DEPLOY_TIMEOUT_MULTIPLIER'] = '2.0'
        fixes.append('extended_timeouts')
        
        # Configurações de retry para deploy
        os.environ['DEPLOY_MAX_RETRIES'] = '5'
        fixes.append('increased_retries')
        
        logger.info("🌐 Configurações de rede otimizadas para deploy")
        return fixes
    
    @staticmethod
    def _apply_system_deploy_fixes():
        """Aplica correções de sistema para deploy"""
        fixes = []
        
        # Configurações de processo para deploy
        os.environ['DEPLOY_PROCESS_MODE'] = 'optimized'
        fixes.append('process_optimization')
        
        # Configurações de cache para deploy
        os.environ['DEPLOY_CACHE_STRATEGY'] = 'aggressive'
        fixes.append('cache_optimization')
        
        logger.info("💾 Configurações de sistema otimizadas para deploy")
        return fixes

class EnhancedDeployOptimizer:
    """Versão melhorada do otimizador com correções específicas"""
    
    @staticmethod
    def get_enhanced_chrome_options():
        """Retorna opções do Chrome com melhorias específicas para deploy"""
        from selenium.webdriver.chrome.options import Options
        
        chrome_options = Options()
        
        # Detecta ambiente
        is_deploy = DeployOptimizer.is_deploy_environment()
        
        if is_deploy:
            logger.info("🚀 DEPLOY: Aplicando configurações Chrome ultra-otimizadas")
            
            # Configurações básicas ultra-otimizadas
            chrome_options.add_argument('--headless=new')  # Modo headless mais novo
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-software-rasterizer')
            
            # Janela pequena mas funcional para deploy (JS necessita espaço mínimo)
            chrome_options.add_argument('--window-size=800,600')
            chrome_options.add_argument('--window-position=0,0')
            
            # Otimizações de memória específicas para deploy (SEM SINGLE-PROCESS)
            chrome_options.add_argument('--memory-pressure-off')
            chrome_options.add_argument('--max_old_space_size=512')
            # REMOVIDO: --single-process (interfere com JavaScript)
            chrome_options.add_argument('--no-zygote')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            
            # Desabilitar recursos desnecessários em deploy
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript-harmony-shipping')
            chrome_options.add_argument('--disable-background-networking')
            chrome_options.add_argument('--disable-background-mode')
            chrome_options.add_argument('--disable-client-side-phishing-detection')
            chrome_options.add_argument('--disable-component-extensions-with-background-pages')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-domain-reliability')
            chrome_options.add_argument('--disable-sync')
            chrome_options.add_argument('--disable-features=TranslateUI,BlinkGenPropertyTrees')
            chrome_options.add_argument('--disable-ipc-flooding-protection')
            chrome_options.add_argument('--aggressive-cache-discard')
            
            # Configurações de rede para deploy
            chrome_options.add_argument('--dns-prefetch-disable')
            chrome_options.add_argument('--disable-preconnect')
            
            # Configurações de logging otimizadas
            chrome_options.add_argument('--disable-logging')
            chrome_options.add_argument('--silent')
            chrome_options.add_argument('--log-level=3')
            
        else:
            logger.info("⚡ DESENVOLVIMENTO: Usando configurações Chrome conservadoras")
            
            # Configurações mais conservadoras para desenvolvimento
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=800,600')
            chrome_options.add_argument('--disable-extensions')
        
        # Configurações comuns
        chrome_options.add_argument('--disable-web-security')
        chrome_options.add_argument('--allow-running-insecure-content')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36')
        
        return chrome_options
    
    @staticmethod
    def get_enhanced_timeouts():
        """Retorna timeouts otimizados com melhorias específicas"""
        is_deploy = DeployOptimizer.is_deploy_environment()
        
        if is_deploy:
            # Timeouts muito mais conservadores para deploy
            return {
                'page_load': 12,      # Aumentado significativamente
                'element_wait': 8,    # Aumentado significativamente 
                'xml_button': 6,      # Aumentado significativamente
                'download_wait': 2.0, # Aumentado significativamente
                'download_poll': 1.0, # Aumentado para reduzir carga
                'max_attempts': 20    # Muito mais tentativas
            }
        else:
            # Timeouts rápidos para desenvolvimento
            return {
                'page_load': 5,
                'element_wait': 3,
                'xml_button': 2,
                'download_wait': 0.8,
                'download_poll': 0.5,
                'max_attempts': 10
            }

class DeployPerformanceMonitor:
    """Monitor de performance específico para deploy"""
    
    @staticmethod
    def log_performance_metrics(operation_name, start_time, end_time, success=True):
        """Registra métricas de performance para análise"""
        duration = end_time - start_time
        status = "SUCCESS" if success else "FAILED"
        env = "DEPLOY" if DeployOptimizer.is_deploy_environment() else "DEV"
        
        logger.info(f"📊 PERFORMANCE [{env}] {operation_name}: {duration:.3f}s - {status}")
        
        # Log alertas se operação está muito lenta
        if success and duration > 10:
            logger.warning(f"⚠️  SLOW OPERATION [{env}] {operation_name} took {duration:.1f}s")
        elif success and duration < 3:
            logger.info(f"⚡ FAST OPERATION [{env}] {operation_name} completed in {duration:.1f}s")
    
    @staticmethod
    def measure_operation(operation_name):
        """Decorator para medir performance de operações"""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    end_time = time.time()
                    DeployPerformanceMonitor.log_performance_metrics(
                        operation_name, start_time, end_time, True
                    )
                    return result
                except Exception as e:
                    end_time = time.time()
                    DeployPerformanceMonitor.log_performance_metrics(
                        operation_name, start_time, end_time, False
                    )
                    raise e
            return wrapper
        return decorator

# Funções de conveniência para uso direto
def apply_deploy_fixes():
    """Aplica todas as correções de performance para deploy"""
    return PerformanceSolution.apply_deploy_performance_fixes()

def get_optimized_chrome_options():
    """Retorna opções Chrome otimizadas para o ambiente atual"""
    return EnhancedDeployOptimizer.get_enhanced_chrome_options()

def get_optimized_timeouts():
    """Retorna timeouts otimizados para o ambiente atual"""
    return EnhancedDeployOptimizer.get_enhanced_timeouts()