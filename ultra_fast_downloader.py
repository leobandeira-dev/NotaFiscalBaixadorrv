"""
Ultra Fast XML Downloader
Sistema de download ultra-otimizado para XMLs com foco em velocidade máxima
"""
import os
import time
import logging
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, WebDriverException
from typing import Dict, Any
import re
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger(__name__)

class UltraFastDownloader:
    def __init__(self):
        self.driver = None
        self.session = requests.Session()
        self.setup_ultra_fast_driver()
    
    def setup_ultra_fast_driver(self):
        """Setup Chrome WebDriver com configurações ultra-otimizadas para velocidade máxima"""
        try:
            chrome_options = Options()
            
            # CONFIGURAÇÕES ULTRA-OTIMIZADAS PARA VELOCIDADE MÁXIMA
            chrome_options.add_argument('--headless=new')  # Modo headless mais rápido
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--disable-software-rasterizer')
            
            # TAMANHO MÍNIMO DE JANELA PARA VELOCIDADE MÁXIMA
            chrome_options.add_argument('--window-size=300,200')
            
            # DESABILITAR RECURSOS DESNECESSÁRIOS
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-javascript')  # Para sites que não precisam de JS
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-features=TranslateUI')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-sync')
            chrome_options.add_argument('--disable-background-networking')
            
            # CONFIGURAÇÕES DE REDE ULTRA-RÁPIDAS
            chrome_options.add_argument('--aggressive-cache-discard')
            chrome_options.add_argument('--memory-pressure-off')
            chrome_options.add_argument('--max_old_space_size=100')
            
            # CONFIGURAÇÕES DE PROCESSO ÚNICO PARA VELOCIDADE
            chrome_options.add_argument('--single-process')
            chrome_options.add_argument('--no-zygote')
            
            # TIMEOUTS ULTRA-AGRESSIVOS
            chrome_options.add_argument('--timeout=3000')
            chrome_options.add_argument('--page-load-strategy=none')
            
            # Desabilitar logs desnecessários
            chrome_options.add_argument('--log-level=3')
            chrome_options.add_argument('--silent')
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            # User agent rápido
            chrome_options.add_argument('--user-agent=FastBot/1.0')
            
            # Downloads directory
            downloads_dir = os.path.abspath('downloads')
            os.makedirs(downloads_dir, exist_ok=True)
            
            prefs = {
                "download.default_directory": downloads_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False,  # Desabilitar para velocidade
                "profile.default_content_settings.popups": 0,
                "profile.managed_default_content_settings.images": 2  # Bloquear imagens
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Tentar paths do chromedriver
            possible_paths = [
                '/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver',
                '/usr/bin/chromedriver',
                '/usr/local/bin/chromedriver'
            ]
            
            chromedriver_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    chromedriver_path = path
                    break
            
            if chromedriver_path:
                from selenium.webdriver.chrome.service import Service
                service = Service(chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
            else:
                self.driver = webdriver.Chrome(options=chrome_options)
            
            # Configurar timeouts ultra-agressivos
            self.driver.set_page_load_timeout(3)  # 3 segundos máximo
            self.driver.implicitly_wait(0.5)  # 0.5 segundos máximo
            
            logger.info("Ultra Fast Chrome WebDriver initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup Ultra Fast WebDriver: {str(e)}")
            raise
    
    def download_xml_ultra_fast(self, invoice_key: str, job_id: str, user_id: int = None) -> Dict[str, Any]:
        """Download XML com velocidade ultra-otimizada"""
        start_time = time.time()
        
        try:
            logger.info(f"[Job {job_id}] ULTRA FAST download iniciado para: {invoice_key}")
            
            # ESTRATÉGIA 1: Tentar download direto via requests primeiro (mais rápido)
            direct_result = self._try_direct_download(invoice_key, job_id)
            if direct_result['success']:
                elapsed = time.time() - start_time
                logger.info(f"[Job {job_id}] Download direto concluído em {elapsed:.2f}s")
                return direct_result
            
            # ESTRATÉGIA 2: Selenium ultra-otimizado
            logger.info(f"[Job {job_id}] Usando Selenium ultra-otimizado...")
            
            # Navegar rapidamente
            url = "https://meudanfe.com.br/"
            self.driver.get(url)
            
            # Aguardar campo de entrada (timeout ultra-agressivo)
            input_element = WebDriverWait(self.driver, 1.5).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[placeholder="Digite a CHAVE DE ACESSO"]'))
            )
            
            # Inserir chave rapidamente
            input_element.clear()
            input_element.send_keys(invoice_key)
            
            # Clicar no botão (timeout ultra-agressivo)
            button = WebDriverWait(self.driver, 1.0).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))
            )
            button.click()
            
            # Aguardar e clicar no link de XML (timeout ultra-agressivo)
            xml_link = WebDriverWait(self.driver, 2.0).until(
                EC.element_to_be_clickable((By.XPATH, '//a[contains(@href, ".xml") or contains(text(), "XML")]'))
            )
            
            xml_url = xml_link.get_attribute('href')
            
            # Download direto via requests (mais rápido que Selenium)
            response = self.session.get(xml_url, timeout=5)
            
            if response.status_code == 200 and response.content:
                # Salvar arquivo
                filename = f"{invoice_key}.xml"
                file_path = os.path.join('downloads', job_id, filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                # Registrar no banco se user_id fornecido
                if user_id:
                    self._save_xml_to_database(response.content.decode('utf-8'), invoice_key, user_id)
                
                elapsed = time.time() - start_time
                logger.info(f"[Job {job_id}] Download Selenium concluído em {elapsed:.2f}s")
                
                return {
                    'success': True,
                    'file_path': file_path,
                    'filename': filename,
                    'size': len(response.content),
                    'download_time': elapsed
                }
            
            return {'success': False, 'error': 'Falha no download do XML'}
            
        except TimeoutException:
            elapsed = time.time() - start_time
            logger.warning(f"[Job {job_id}] Timeout após {elapsed:.2f}s")
            return {'success': False, 'error': f'Timeout após {elapsed:.2f}s'}
            
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"[Job {job_id}] Erro após {elapsed:.2f}s: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _try_direct_download(self, invoice_key: str, job_id: str) -> Dict[str, Any]:
        """Tentar download direto via API/requests (mais rápido que Selenium)"""
        try:
            # Tentar construir URL direta se possível
            # Isso seria específico para cada site de consulta
            # Por enquanto, retornar que não foi possível
            return {'success': False, 'error': 'Direct download not available'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _save_xml_to_database(self, xml_content: str, invoice_key: str, user_id: int):
        """Salvar XML no banco de dados com contexto Flask"""
        try:
            from models import XMLFile
            from new_app import app, db
            from xml_processor import parse_xml_content
            
            with app.app_context():
                # Verificar se já existe
                existing = XMLFile.query.filter_by(
                    invoice_key=invoice_key,
                    user_id=user_id
                ).first()
                
                if existing:
                    logger.info(f"XML {invoice_key} já existe no banco para usuário {user_id}")
                    return
                
                # Extrair dados do XML
                xml_data = parse_xml_content(xml_content)
                
                # Criar novo registro
                xml_file = XMLFile(
                    user_id=user_id,
                    invoice_key=invoice_key,
                    filename=f"{invoice_key}.xml",
                    xml_content=xml_content,
                    import_type='SISTEMA',
                    # Campos extraídos
                    numero_nf=xml_data.get('numero_nf'),
                    serie_nf=xml_data.get('serie_nf'),
                    data_emissao=xml_data.get('data_emissao'),
                    valor_total=xml_data.get('valor_total'),
                    peso_bruto=xml_data.get('peso_bruto'),
                    quantidade_volumes=xml_data.get('quantidade_volumes'),
                    nome_emitente=xml_data.get('nome_emitente'),
                    cidade_emitente=xml_data.get('cidade_emitente'),
                    uf_emitente=xml_data.get('uf_emitente'),
                    cnpj_emitente=xml_data.get('cnpj_emitente'),
                    nome_destinatario=xml_data.get('nome_destinatario'),
                    cidade_destinatario=xml_data.get('cidade_destinatario'),
                    uf_destinatario=xml_data.get('uf_destinatario'),
                    destinatario_cnpj_cpf=xml_data.get('destinatario_cnpj_cpf'),
                    nome_transportadora=xml_data.get('nome_transportadora')
                )
                
                db.session.add(xml_file)
                db.session.commit()
                
                logger.info(f"XML {invoice_key} salvo no banco para usuário {user_id}")
                
        except Exception as e:
            logger.error(f"Erro ao salvar XML no banco: {str(e)}")
    
    def batch_download_ultra_fast(self, invoice_keys: list, job_id: str, user_id: int = None) -> Dict[str, Any]:
        """Download em lote com paralelização ultra-otimizada"""
        start_time = time.time()
        results = []
        
        # Usar ThreadPoolExecutor para downloads paralelos
        max_workers = min(len(invoice_keys), 3)  # Máximo 3 threads paralelas
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submeter todas as tarefas
            future_to_key = {
                executor.submit(self.download_xml_ultra_fast, key, f"{job_id}_{i}", user_id): key 
                for i, key in enumerate(invoice_keys)
            }
            
            # Coletar resultados conforme completam
            for future in as_completed(future_to_key):
                invoice_key = future_to_key[future]
                try:
                    result = future.result()
                    result['invoice_key'] = invoice_key
                    results.append(result)
                    
                    if result['success']:
                        logger.info(f"[Batch {job_id}] {invoice_key}: Sucesso em {result.get('download_time', 0):.2f}s")
                    else:
                        logger.warning(f"[Batch {job_id}] {invoice_key}: Falha - {result.get('error', 'Erro desconhecido')}")
                        
                except Exception as e:
                    logger.error(f"[Batch {job_id}] {invoice_key}: Exceção - {str(e)}")
                    results.append({
                        'success': False,
                        'invoice_key': invoice_key,
                        'error': str(e)
                    })
        
        elapsed = time.time() - start_time
        successful = len([r for r in results if r['success']])
        
        logger.info(f"[Batch {job_id}] Concluído: {successful}/{len(invoice_keys)} sucessos em {elapsed:.2f}s")
        
        return {
            'success': True,
            'results': results,
            'total_time': elapsed,
            'successful_count': successful,
            'total_count': len(invoice_keys)
        }
    
    def cleanup(self):
        """Limpeza rápida dos recursos"""
        try:
            if self.driver:
                self.driver.quit()
            if self.session:
                self.session.close()
        except Exception as e:
            logger.error(f"Erro na limpeza: {str(e)}")