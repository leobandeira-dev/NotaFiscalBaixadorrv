"""
Ultra Speed Optimizer para Robô de Automação
Sistema de otimização extrema para máxima velocidade de processamento
"""

import os
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

logger = logging.getLogger(__name__)

class UltraSpeedOptimizer:
    """Otimizador de velocidade extrema para automação"""
    
    @staticmethod
    def get_ultra_chrome_options():
        """Configurações Chrome ultra-otimizadas para máxima velocidade"""
        options = Options()
        
        # Modo headless mais rápido
        options.add_argument('--headless=new')
        
        # Desabilitar recursos desnecessários para velocidade máxima
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=VizDisplayCompositor')
        
        # Configurações de rede ultra-rápidas
        options.add_argument('--aggressive-cache-discard')
        options.add_argument('--disable-background-networking')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-renderer-backgrounding')
        options.add_argument('--disable-backgrounding-occluded-windows')
        options.add_argument('--disable-client-side-phishing-detection')
        
        # Memória e processamento otimizados
        options.add_argument('--memory-pressure-off')
        options.add_argument('--max_old_space_size=4096')
        options.add_argument('--single-process')
        options.add_argument('--no-zygote')
        
        # Desabilitar recursos visuais para velocidade
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')
        options.add_argument('--disable-javascript')  # Removido - necessário para funcionamento
        options.add_argument('--disable-css3-animations')
        
        # Configurações de janela mínimas
        options.add_argument('--window-size=600,400')
        options.add_argument('--window-position=0,0')
        
        # Desabilitar logs para velocidade
        options.add_argument('--disable-logging')
        options.add_argument('--silent')
        options.add_argument('--log-level=3')
        
        # Configurações experimentais de velocidade
        options.add_experimental_option('useAutomationExtension', False)
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('prefs', {
            'profile.default_content_setting_values': {
                'notifications': 2,
                'media_stream': 2,
                'geolocation': 2
            },
            'profile.managed_default_content_settings': {
                'images': 2  # Bloquear imagens para velocidade
            }
        })
        
        return options
    
    @staticmethod
    def get_ultra_timeouts():
        """Timeouts ultra-otimizados para máxima velocidade"""
        return {
            'page_load': 3,      # Reduzido de 8s para 3s
            'element_wait': 1,   # Reduzido de 3s para 1s
            'xml_button': 1,     # Reduzido de 2s para 1s
            'download_poll': 0.2, # Reduzido de 0.5s para 0.2s
            'max_attempts': 15   # Reduzido de 20 para 15
        }
    
    @staticmethod
    def setup_ultra_fast_driver():
        """Configurar driver Chrome ultra-rápido"""
        try:
            logger.info("🚀 Configurando Chrome ULTRA-RÁPIDO...")
            
            options = UltraSpeedOptimizer.get_ultra_chrome_options()
            
            # Configurar timeout de página ultra-baixo
            options.add_argument('--timeout=3000')  # 3 segundos max
            
            # Detectar chromedriver disponível
            chromedriver_path = None
            possible_paths = [
                '/nix/store/*/bin/chromedriver',
                '/usr/bin/chromedriver',
                'chromedriver'
            ]
            
            import glob
            for pattern in possible_paths:
                matches = glob.glob(pattern)
                if matches:
                    chromedriver_path = matches[0]
                    break
            
            if chromedriver_path and os.path.exists(chromedriver_path):
                from selenium.webdriver.chrome.service import Service
                service = Service(chromedriver_path)
                driver = webdriver.Chrome(service=service, options=options)
            else:
                driver = webdriver.Chrome(options=options)
            
            # Configurar timeouts ultra-baixos
            driver.set_page_load_timeout(3)
            driver.implicitly_wait(0.5)
            
            logger.info("✅ Chrome ULTRA-RÁPIDO configurado com sucesso!")
            return driver
            
        except Exception as e:
            logger.error(f"Erro ao configurar Chrome ultra-rápido: {e}")
            raise

class UltraFastDownloader:
    """Downloader ultra-rápido para XMLs"""
    
    def __init__(self):
        self.driver = None
        self.ultra_timeouts = UltraSpeedOptimizer.get_ultra_timeouts()
        
    def setup_driver(self):
        """Configurar driver ultra-rápido"""
        self.driver = UltraSpeedOptimizer.setup_ultra_fast_driver()
        
    def ultra_fast_xml_download(self, invoice_key: str, job_id: str) -> dict:
        """Download XML ultra-rápido com otimizações extremas"""
        try:
            start_time = time.time()
            logger.info(f"🏃‍♂️ [Job {job_id}] ULTRA-FAST download iniciado: {invoice_key}")
            
            # 1. Navegação ultra-rápida
            self.driver.get("https://meudanfe.com.br/")
            
            # 2. Localizar e preencher campo (timeout mínimo)
            input_field = WebDriverWait(self.driver, self.ultra_timeouts['element_wait']).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[placeholder="Digite a CHAVE DE ACESSO"]'))
            )
            input_field.clear()
            input_field.send_keys(invoice_key)
            
            # 3. Submit ultra-rápido
            submit_btn = WebDriverWait(self.driver, self.ultra_timeouts['element_wait']).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"], input[type="submit"]'))
            )
            submit_btn.click()
            
            # 4. Localizar botão XML (timeout mínimo)
            xml_button = WebDriverWait(self.driver, self.ultra_timeouts['xml_button']).until(
                EC.element_to_be_clickable((By.XPATH, '//a[contains(@href, "xml") or contains(text(), "XML") or contains(@class, "xml")]'))
            )
            xml_button.click()
            
            # 5. Verificação ultra-rápida de download
            downloads_dir = 'downloads'
            os.makedirs(downloads_dir, exist_ok=True)
            
            # Polling ultra-rápido
            for attempt in range(self.ultra_timeouts['max_attempts']):
                files = [f for f in os.listdir(downloads_dir) 
                        if f.endswith('.xml') and invoice_key in f]
                
                if files:
                    file_path = os.path.join(downloads_dir, files[0])
                    elapsed = time.time() - start_time
                    logger.info(f"⚡ [Job {job_id}] ULTRA-FAST sucesso em {elapsed:.2f}s!")
                    
                    return {
                        'success': True,
                        'file_path': file_path,
                        'processing_time': elapsed
                    }
                
                time.sleep(self.ultra_timeouts['download_poll'])
            
            # Timeout
            elapsed = time.time() - start_time
            logger.warning(f"⏱️ [Job {job_id}] Timeout após {elapsed:.2f}s")
            
            return {
                'success': False,
                'error': f'Timeout após {elapsed:.2f}s',
                'processing_time': elapsed
            }
            
        except Exception as e:
            elapsed = time.time() - start_time if 'start_time' in locals() else 0
            logger.error(f"❌ [Job {job_id}] Erro ultra-fast: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'processing_time': elapsed
            }
    
    def cleanup(self):
        """Cleanup ultra-rápido"""
        if self.driver:
            try:
                self.driver.quit()
            except:
                pass
            self.driver = None

# Performance monitor para ultra velocidade
import time

class UltraSpeedMonitor:
    """Monitor de performance para velocidade ultra"""
    
    @staticmethod
    def measure_ultra_speed(func):
        """Decorator para medir velocidade ultra"""
        def wrapper(*args, **kwargs):
            start = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            
            if elapsed < 2:
                logger.info(f"🚀 ULTRA-FAST: {func.__name__} em {elapsed:.2f}s!")
            elif elapsed < 5:
                logger.info(f"⚡ FAST: {func.__name__} em {elapsed:.2f}s")
            else:
                logger.warning(f"🐌 SLOW: {func.__name__} em {elapsed:.2f}s")
            
            return result
        return wrapper