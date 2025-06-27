#!/usr/bin/env python3
"""
Sistema de automação para consultardanfe.com
Site mais direto e funcional para download de XMLs
"""

import os
import sys
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConsultarDanfeAutomation:
    """Automação para o site consultardanfe.com"""
    
    def __init__(self):
        self.base_url = "https://consultardanfe.com/"
        self.driver = None
        
    def setup_driver(self):
        """Configurar Chrome WebDriver otimizado"""
        try:
            chrome_options = Options()
            
            # Configurações para ambiente de deploy
            chrome_options.add_argument('--headless')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1024,768')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Configurações de download
            download_dir = os.path.abspath('./downloads')
            os.makedirs(download_dir, exist_ok=True)
            
            prefs = {
                "download.default_directory": download_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Configurar service
            service = Service('/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver')
            
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(30)
            self.driver.implicitly_wait(5)
            
            logger.info("Chrome WebDriver configurado com sucesso")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao configurar WebDriver: {e}")
            return False
    
    def download_xml(self, invoice_key: str, job_id: str, user_id: int = None) -> dict:
        """
        Download XML usando consultardanfe.com
        
        Args:
            invoice_key: Chave da nota fiscal (44 dígitos)
            job_id: ID do job para tracking
            user_id: ID do usuário
            
        Returns:
            dict: Resultado do download
        """
        start_time = time.time()
        
        try:
            logger.info(f"[{job_id}] Iniciando download XML para chave: {invoice_key}")
            
            if not self.setup_driver():
                return {'success': False, 'error': 'Falha ao configurar WebDriver'}
            
            # Navegar para o site
            logger.info(f"[{job_id}] Navegando para {self.base_url}")
            self.driver.get(self.base_url)
            
            # Aguardar carregamento
            wait = WebDriverWait(self.driver, 15)
            time.sleep(3)
            
            logger.info(f"[{job_id}] Página carregada: {self.driver.title}")
            
            # Encontrar campo de entrada
            logger.info(f"[{job_id}] Procurando campo de entrada da chave...")
            
            # Tentar diferentes seletores para o campo de entrada
            input_selectors = [
                "input[placeholder*='chave']",
                "input[type='text']",
                "input.form-control",
                "#chave_acesso",
                "[name*='chave']"
            ]
            
            input_field = None
            for selector in input_selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            # Verificar se é um campo de entrada válido
                            placeholder = element.get_attribute('placeholder') or ''
                            if any(term in placeholder.lower() for term in ['chave', 'código', 'xml']):
                                input_field = element
                                logger.info(f"[{job_id}] Campo encontrado: {selector} (placeholder: '{placeholder}')")
                                break
                    if input_field:
                        break
                except Exception as e:
                    logger.debug(f"[{job_id}] Seletor {selector} falhou: {e}")
            
            if not input_field:
                # Último recurso: tentar primeiro campo de texto visível
                try:
                    text_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='text']")
                    for inp in text_inputs:
                        if inp.is_displayed() and inp.is_enabled():
                            input_field = inp
                            logger.info(f"[{job_id}] Usando primeiro campo de texto visível")
                            break
                except:
                    pass
            
            if not input_field:
                return {'success': False, 'error': 'Campo de entrada não encontrado'}
            
            # Inserir chave da nota fiscal
            logger.info(f"[{job_id}] Inserindo chave da nota fiscal...")
            input_field.clear()
            input_field.send_keys(invoice_key)
            
            # Verificar se a chave foi inserida corretamente
            inserted_value = input_field.get_attribute('value')
            if inserted_value != invoice_key:
                logger.warning(f"[{job_id}] Chave pode não ter sido inserida corretamente")
            
            # Procurar botão de buscar
            logger.info(f"[{job_id}] Procurando botão de busca...")
            
            # Tentar diferentes métodos para encontrar o botão
            button_selectors = [
                "//button[contains(text(), 'Buscar DANFE/XML')]",
                "//button[contains(text(), 'Buscar')]",
                "//button[contains(text(), 'DANFE')]",
                "//input[@value='Buscar']",
                "button[type='submit']",
                ".btn-primary",
                ".btn"
            ]
            
            submit_button = None
            for selector in button_selectors:
                try:
                    if selector.startswith("//"):
                        # XPath
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        # CSS Selector
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if element.is_displayed() and element.is_enabled():
                            submit_button = element
                            logger.info(f"[{job_id}] Botão encontrado: {selector}")
                            break
                    
                    if submit_button:
                        break
                        
                except Exception as e:
                    logger.debug(f"[{job_id}] Seletor de botão {selector} falhou: {e}")
            
            if not submit_button:
                return {'success': False, 'error': 'Botão de busca não encontrado'}
            
            # Clicar no botão de buscar
            logger.info(f"[{job_id}] Clicando no botão de busca...")
            submit_button.click()
            
            # Aguardar resultado
            logger.info(f"[{job_id}] Aguardando resultado...")
            time.sleep(5)
            
            # Procurar modal de sucesso e botão de download XML
            logger.info(f"[{job_id}] Procurando opções de download...")
            
            # Tentar encontrar botão "Download XML"
            xml_download_selectors = [
                "//button[contains(text(), 'Download XML')]",
                "//a[contains(text(), 'Download XML')]",
                "//button[contains(text(), 'XML')]",
                "//a[contains(text(), 'XML')]",
                ".download-xml",
                "#download-xml"
            ]
            
            xml_button = None
            for selector in xml_download_selectors:
                try:
                    if selector.startswith("//"):
                        elements = self.driver.find_elements(By.XPATH, selector)
                    else:
                        elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    
                    for element in elements:
                        if element.is_displayed():
                            xml_button = element
                            logger.info(f"[{job_id}] Botão XML encontrado: {selector}")
                            break
                    
                    if xml_button:
                        break
                        
                except Exception as e:
                    logger.debug(f"[{job_id}] Seletor XML {selector} falhou: {e}")
            
            if not xml_button:
                # Tentar extrair XML da página se não houver botão de download
                return self.extract_xml_from_page(job_id, invoice_key, user_id)
            
            # Clicar no botão de download XML
            logger.info(f"[{job_id}] Clicando em Download XML...")
            xml_button.click()
            
            # Aguardar download
            time.sleep(3)
            
            # Verificar se o arquivo foi baixado
            download_result = self.check_downloaded_file(invoice_key, job_id)
            
            if download_result['success']:
                elapsed_time = time.time() - start_time
                download_result['elapsed_time'] = round(elapsed_time, 2)
                logger.info(f"[{job_id}] Download concluído com sucesso em {elapsed_time:.2f}s")
            
            return download_result
            
        except Exception as e:
            logger.error(f"[{job_id}] Erro durante download: {e}")
            return {
                'success': False,
                'error': f'Erro durante automação: {str(e)}',
                'elapsed_time': round(time.time() - start_time, 2)
            }
        
        finally:
            self.cleanup()
    
    def extract_xml_from_page(self, job_id: str, invoice_key: str, user_id: int = None) -> dict:
        """Extrair XML diretamente da página se não houver download"""
        try:
            logger.info(f"[{job_id}] Tentando extrair XML da página...")
            
            # Procurar por conteúdo XML na página
            page_source = self.driver.page_source
            
            # Procurar por tags XML típicas
            xml_indicators = ['<nfeProc', '<NFe', '<?xml', '<infNFe']
            
            for indicator in xml_indicators:
                if indicator in page_source:
                    logger.info(f"[{job_id}] Conteúdo XML detectado na página")
                    
                    # Tentar extrair XML
                    start_pos = page_source.find('<?xml')
                    if start_pos == -1:
                        start_pos = page_source.find('<nfeProc')
                    if start_pos == -1:
                        start_pos = page_source.find('<NFe')
                    
                    if start_pos != -1:
                        end_pos = page_source.find('</nfeProc>', start_pos)
                        if end_pos == -1:
                            end_pos = page_source.find('</NFe>', start_pos)
                        
                        if end_pos != -1:
                            xml_content = page_source[start_pos:end_pos + 10]  # +10 para incluir tag de fechamento
                            
                            # Salvar XML
                            return self.save_xml_content(xml_content, invoice_key, job_id, user_id)
            
            return {'success': False, 'error': 'XML não encontrado na página'}
            
        except Exception as e:
            logger.error(f"[{job_id}] Erro ao extrair XML da página: {e}")
            return {'success': False, 'error': f'Erro ao extrair XML: {str(e)}'}
    
    def save_xml_content(self, xml_content: str, invoice_key: str, job_id: str, user_id: int = None) -> dict:
        """Salvar conteúdo XML em arquivo"""
        try:
            # Criar diretório de download se não existir
            download_dir = os.path.abspath('./downloads')
            os.makedirs(download_dir, exist_ok=True)
            
            # Nome do arquivo
            filename = f"{invoice_key}.xml"
            file_path = os.path.join(download_dir, filename)
            
            # Salvar arquivo
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            file_size = os.path.getsize(file_path)
            
            logger.info(f"[{job_id}] XML salvo: {filename} ({file_size} bytes)")
            
            return {
                'success': True,
                'filename': filename,
                'file_path': file_path,
                'file_size': file_size,
                'message': 'XML extraído e salvo com sucesso'
            }
            
        except Exception as e:
            logger.error(f"[{job_id}] Erro ao salvar XML: {e}")
            return {'success': False, 'error': f'Erro ao salvar XML: {str(e)}'}
    
    def check_downloaded_file(self, invoice_key: str, job_id: str) -> dict:
        """Verificar se arquivo foi baixado"""
        try:
            download_dir = os.path.abspath('./downloads')
            
            # Possíveis nomes de arquivo
            possible_files = [
                f"{invoice_key}.xml",
                f"nfe_{invoice_key}.xml",
                f"danfe_{invoice_key}.xml",
                "download.xml"
            ]
            
            # Verificar arquivos recentes
            for filename in possible_files:
                file_path = os.path.join(download_dir, filename)
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    
                    # Verificar se o arquivo não está vazio e foi criado recentemente
                    if file_size > 0:
                        file_age = time.time() - os.path.getmtime(file_path)
                        if file_age < 60:  # Arquivo criado nos últimos 60 segundos
                            logger.info(f"[{job_id}] Arquivo encontrado: {filename} ({file_size} bytes)")
                            return {
                                'success': True,
                                'filename': filename,
                                'file_path': file_path,
                                'file_size': file_size
                            }
            
            return {'success': False, 'error': 'Arquivo XML não foi baixado'}
            
        except Exception as e:
            logger.error(f"[{job_id}] Erro ao verificar arquivo: {e}")
            return {'success': False, 'error': f'Erro ao verificar download: {str(e)}'}
    
    def cleanup(self):
        """Limpar recursos"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver finalizado")
            except:
                pass
            self.driver = None

def test_consultardanfe():
    """Função de teste"""
    automation = ConsultarDanfeAutomation()
    
    # Chave de teste
    test_key = "35250513516247000107550010000113401146202508"
    
    result = automation.download_xml(test_key, "test_001")
    
    print("Resultado do teste:")
    print(f"Sucesso: {result.get('success')}")
    print(f"Erro: {result.get('error', 'N/A')}")
    print(f"Arquivo: {result.get('filename', 'N/A')}")
    print(f"Tamanho: {result.get('file_size', 'N/A')} bytes")
    print(f"Tempo: {result.get('elapsed_time', 'N/A')} segundos")

if __name__ == "__main__":
    test_consultardanfe()