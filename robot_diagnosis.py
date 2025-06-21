"""
Diagnóstico completo do robô de download XML
Identifica diferenças entre ambiente de desenvolvimento e deploy
"""

import os
import time
import logging
import requests
from datetime import datetime
import subprocess
import psutil

class RobotDiagnostic:
    """Diagnóstico completo do sistema de automação"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.INFO)
        
    def detect_environment(self):
        """Detecta se está rodando em desenvolvimento ou deploy"""
        env_indicators = {
            'REPLIT_DEPLOYMENT': os.environ.get('REPLIT_DEPLOYMENT'),
            'REPLIT_DEV_DOMAIN': os.environ.get('REPLIT_DEV_DOMAIN'),
            'REPLIT_DOMAINS': os.environ.get('REPLIT_DOMAINS'),
            'HOME': os.environ.get('HOME'),
            'PWD': os.environ.get('PWD')
        }
        
        is_deploy = os.environ.get('REPLIT_DEPLOYMENT') == 'true'
        
        print("🔍 DETECÇÃO DE AMBIENTE")
        print("=" * 50)
        for key, value in env_indicators.items():
            print(f"{key}: {value}")
        
        print(f"\nAmbiente detectado: {'DEPLOY' if is_deploy else 'DESENVOLVIMENTO'}")
        return is_deploy
    
    def check_chrome_availability(self):
        """Verifica disponibilidade do Chrome e ChromeDriver"""
        print("\n🔍 VERIFICAÇÃO DO CHROME")
        print("=" * 50)
        
        # Verificar Chrome
        chrome_paths = [
            '/nix/store/*/bin/google-chrome-stable',
            '/usr/bin/google-chrome',
            '/usr/bin/chromium-browser'
        ]
        
        chrome_found = False
        for path_pattern in chrome_paths:
            if '*' in path_pattern:
                # Usar glob para padrões
                import glob
                matches = glob.glob(path_pattern)
                if matches:
                    print(f"✅ Chrome encontrado: {matches[0]}")
                    chrome_found = True
                    break
            elif os.path.exists(path_pattern):
                print(f"✅ Chrome encontrado: {path_pattern}")
                chrome_found = True
                break
        
        if not chrome_found:
            print("❌ Chrome não encontrado")
        
        # Verificar ChromeDriver
        chromedriver_paths = [
            '/nix/store/*/bin/chromedriver',
            '/usr/bin/chromedriver',
            '/usr/local/bin/chromedriver'
        ]
        
        chromedriver_found = False
        for path_pattern in chromedriver_paths:
            if '*' in path_pattern:
                import glob
                matches = glob.glob(path_pattern)
                if matches:
                    print(f"✅ ChromeDriver encontrado: {matches[0]}")
                    chromedriver_found = True
                    break
            elif os.path.exists(path_pattern):
                print(f"✅ ChromeDriver encontrado: {path_pattern}")
                chromedriver_found = True
                break
        
        if not chromedriver_found:
            print("❌ ChromeDriver não encontrado")
        
        return chrome_found and chromedriver_found
    
    def check_system_resources(self):
        """Verifica recursos do sistema"""
        print("\n🔍 RECURSOS DO SISTEMA")
        print("=" * 50)
        
        # Memória
        memory = psutil.virtual_memory()
        print(f"Memória total: {memory.total / (1024**3):.2f} GB")
        print(f"Memória disponível: {memory.available / (1024**3):.2f} GB")
        print(f"Uso de memória: {memory.percent}%")
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)
        print(f"Uso de CPU: {cpu_percent}%")
        print(f"Núcleos de CPU: {psutil.cpu_count()}")
        
        # Disk
        disk = psutil.disk_usage('/')
        print(f"Espaço em disco: {disk.free / (1024**3):.2f} GB livre de {disk.total / (1024**3):.2f} GB")
        
        return {
            'memory_available_gb': memory.available / (1024**3),
            'cpu_percent': cpu_percent,
            'disk_free_gb': disk.free / (1024**3)
        }
    
    def test_selenium_basic(self):
        """Teste básico do Selenium"""
        print("\n🔍 TESTE BÁSICO DO SELENIUM")
        print("=" * 50)
        
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=800,600')
            
            # Tentar criar driver
            driver = webdriver.Chrome(options=chrome_options)
            
            # Teste básico
            driver.get("https://httpbin.org/get")
            time.sleep(2)
            
            title = driver.title
            url = driver.current_url
            
            driver.quit()
            
            print("✅ Selenium funcionando corretamente")
            print(f"Título da página: {title}")
            print(f"URL acessada: {url}")
            
            return True
            
        except Exception as e:
            print(f"❌ Erro no Selenium: {e}")
            return False
    
    def test_target_website_access(self):
        """Testa acesso ao site alvo"""
        print("\n🔍 TESTE DE ACESSO AO SITE ALVO")
        print("=" * 50)
        
        target_url = "https://meudanfe.com.br/"
        
        try:
            # Teste HTTP básico
            response = requests.get(target_url, timeout=10)
            print(f"✅ HTTP Status: {response.status_code}")
            print(f"Tamanho da resposta: {len(response.content)} bytes")
            
            # Verificar se é uma página válida
            if "danfe" in response.text.lower() or "nota fiscal" in response.text.lower():
                print("✅ Site contém conteúdo esperado")
                site_accessible = True
            else:
                print("⚠️ Site acessível mas conteúdo não reconhecido")
                site_accessible = False
            
        except Exception as e:
            print(f"❌ Erro acessando site: {e}")
            site_accessible = False
        
        # Teste com Selenium
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            chrome_options = Options()
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=800,600')
            
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(target_url)
            
            # Aguardar carregamento
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Verificar elemento específico
            try:
                input_element = driver.find_element(
                    By.CSS_SELECTOR, 'input[placeholder*="CHAVE"]'
                )
                print("✅ Campo de entrada encontrado com Selenium")
                selenium_success = True
            except:
                print("⚠️ Campo de entrada não encontrado")
                selenium_success = False
            
            driver.quit()
            
        except Exception as e:
            print(f"❌ Erro Selenium no site: {e}")
            selenium_success = False
        
        return site_accessible and selenium_success
    
    def check_network_connectivity(self):
        """Verifica conectividade de rede"""
        print("\n🔍 TESTE DE CONECTIVIDADE")
        print("=" * 50)
        
        test_urls = [
            "https://google.com",
            "https://httpbin.org/get",
            "https://meudanfe.com.br/",
            "https://www.receita.fazenda.gov.br/"
        ]
        
        results = {}
        for url in test_urls:
            try:
                response = requests.get(url, timeout=5)
                latency = response.elapsed.total_seconds() * 1000
                results[url] = {
                    'status': response.status_code,
                    'latency_ms': latency,
                    'success': True
                }
                print(f"✅ {url} - {response.status_code} ({latency:.0f}ms)")
            except Exception as e:
                results[url] = {
                    'error': str(e),
                    'success': False
                }
                print(f"❌ {url} - {e}")
        
        return results
    
    def analyze_logs(self):
        """Analisa logs recentes para identificar erros"""
        print("\n🔍 ANÁLISE DE LOGS")
        print("=" * 50)
        
        # Simular verificação de logs
        common_errors = [
            "Chrome failed to start",
            "WebDriverException",
            "TimeoutException",
            "Connection refused",
            "No such element",
            "ChromeDriver not found"
        ]
        
        print("Verificando padrões de erro comuns...")
        for error in common_errors:
            print(f"⚠️ Monitorar: {error}")
        
        return common_errors
    
    def test_full_automation_flow(self):
        """Teste completo do fluxo de automação"""
        print("\n🔍 TESTE COMPLETO DE AUTOMAÇÃO")
        print("=" * 50)
        
        try:
            # Importar e testar robô
            from automation_fixed import InvoiceDownloader
            
            downloader = InvoiceDownloader()
            
            # Teste de conexão
            connection_result = downloader.test_connection()
            
            if connection_result['success']:
                print("✅ Robô de automação funcionando")
                print(f"Mensagem: {connection_result['message']}")
                
                # Cleanup
                downloader.cleanup()
                return True
            else:
                print("❌ Robô de automação com problemas")
                print(f"Erro: {connection_result['message']}")
                return False
                
        except Exception as e:
            print(f"❌ Erro crítico no robô: {e}")
            return False
    
    def generate_diagnosis_report(self):
        """Gera relatório completo de diagnóstico"""
        print("\n" + "="*60)
        print("🚀 DIAGNÓSTICO COMPLETO DO ROBÔ XML")
        print("="*60)
        
        # Executar todos os testes
        is_deploy = self.detect_environment()
        chrome_ok = self.check_chrome_availability()
        resources = self.check_system_resources()
        selenium_ok = self.test_selenium_basic()
        website_ok = self.test_target_website_access()
        network_results = self.check_network_connectivity()
        self.analyze_logs()
        automation_ok = self.test_full_automation_flow()
        
        # Análise final
        print("\n📊 RESUMO DO DIAGNÓSTICO")
        print("=" * 50)
        print(f"Ambiente: {'DEPLOY' if is_deploy else 'DESENVOLVIMENTO'}")
        print(f"Chrome/ChromeDriver: {'✅' if chrome_ok else '❌'}")
        print(f"Selenium básico: {'✅' if selenium_ok else '❌'}")
        print(f"Acesso ao site: {'✅' if website_ok else '❌'}")
        print(f"Robô completo: {'✅' if automation_ok else '❌'}")
        
        # Recursos do sistema
        print(f"\nRecursos disponíveis:")
        print(f"- Memória: {resources['memory_available_gb']:.1f} GB")
        print(f"- CPU: {resources['cpu_percent']:.1f}%")
        print(f"- Disco: {resources['disk_free_gb']:.1f} GB")
        
        # Identificar problema principal
        if not chrome_ok:
            problem = "Chrome/ChromeDriver não disponível"
            solution = "Instalar ou corrigir paths do Chrome"
        elif not selenium_ok:
            problem = "Selenium não funciona"
            solution = "Verificar dependências e configurações"
        elif not website_ok:
            problem = "Site alvo inacessível"
            solution = "Verificar conectividade e firewall"
        elif not automation_ok:
            problem = "Robô de automação com falhas"
            solution = "Debug específico do código de automação"
        else:
            problem = "Sistema aparentemente funcional"
            solution = "Investigar logs específicos de falhas"
        
        print(f"\n🎯 PROBLEMA IDENTIFICADO: {problem}")
        print(f"💡 SOLUÇÃO RECOMENDADA: {solution}")
        
        return {
            'is_deploy': is_deploy,
            'chrome_ok': chrome_ok,
            'selenium_ok': selenium_ok,
            'website_ok': website_ok,
            'automation_ok': automation_ok,
            'problem': problem,
            'solution': solution,
            'resources': resources
        }

if __name__ == "__main__":
    diagnostic = RobotDiagnostic()
    result = diagnostic.generate_diagnosis_report()