"""
Automação Otimizada para Velocidade
Versão simplificada e ultra-rápida do sistema de download
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
import threading

logger = logging.getLogger(__name__)

class SpeedOptimizedDownloader:
    def __init__(self):
        self.driver = None
        self.setup_speed_optimized_driver()
    
    def setup_speed_optimized_driver(self):
        """Setup Chrome WebDriver com configurações ultra-otimizadas"""
        try:
            chrome_options = Options()
            
            # CONFIGURAÇÕES OTIMIZADAS PARA VELOCIDADE MÁXIMA
            chrome_options.add_argument('--headless=new')
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            
            # JANELA MÍNIMA PARA VELOCIDADE
            chrome_options.add_argument('--window-size=400,300')
            
            # DESABILITAR RECURSOS PESADOS
            chrome_options.add_argument('--disable-images')
            chrome_options.add_argument('--disable-plugins')
            chrome_options.add_argument('--disable-extensions')
            chrome_options.add_argument('--disable-background-timer-throttling')
            chrome_options.add_argument('--disable-backgrounding-occluded-windows')
            chrome_options.add_argument('--disable-renderer-backgrounding')
            chrome_options.add_argument('--disable-features=TranslateUI')
            chrome_options.add_argument('--disable-default-apps')
            chrome_options.add_argument('--disable-sync')
            chrome_options.add_argument('--disable-background-networking')
            
            # CONFIGURAÇÕES DE MEMÓRIA E PROCESSO
            chrome_options.add_argument('--single-process')
            chrome_options.add_argument('--memory-pressure-off')
            chrome_options.add_argument('--max_old_space_size=100')
            
            # LOGS MÍNIMOS
            chrome_options.add_argument('--log-level=3')
            chrome_options.add_argument('--silent')
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            
            # USER AGENT SIMPLES
            chrome_options.add_argument('--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36')
            
            # Downloads directory
            downloads_dir = os.path.abspath('downloads')
            os.makedirs(downloads_dir, exist_ok=True)
            
            prefs = {
                "download.default_directory": downloads_dir,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": False,
                "profile.default_content_settings.popups": 0,
                "profile.managed_default_content_settings.images": 2
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Tentar chromedriver paths
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
            
            # TIMEOUTS ULTRA-AGRESSIVOS
            self.driver.set_page_load_timeout(2)  # 2 segundos máximo
            self.driver.implicitly_wait(0.3)  # 0.3 segundos máximo
            
            logger.info("Speed Optimized Chrome WebDriver initialized")
            
        except Exception as e:
            logger.error(f"Failed to setup Speed Optimized WebDriver: {str(e)}")
            raise
    
    def download_xml_speed_optimized(self, invoice_key: str, job_id: str, user_id: int = None) -> Dict[str, Any]:
        """Download XML com velocidade otimizada"""
        start_time = time.time()
        
        try:
            logger.info(f"[Job {job_id}] SPEED download iniciado para: {invoice_key}")
            
            # Navegar rapidamente para o site
            url = "https://meudanfe.com.br/"
            self.driver.get(url)
            
            # Aguardar campo de entrada com timeout agressivo
            input_element = WebDriverWait(self.driver, 1.0).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[placeholder="Digite a CHAVE DE ACESSO"]'))
            )
            
            # Inserir chave rapidamente
            input_element.clear()
            input_element.send_keys(invoice_key)
            
            # Clicar no botão submit
            button = WebDriverWait(self.driver, 0.8).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]'))
            )
            button.click()
            
            # Aguardar e clicar no link de XML
            xml_link = WebDriverWait(self.driver, 1.5).until(
                EC.element_to_be_clickable((By.XPATH, '//a[contains(@href, ".xml") or contains(text(), "XML")]'))
            )
            
            xml_url = xml_link.get_attribute('href')
            
            # Download via requests (mais rápido)
            session = requests.Session()
            response = session.get(xml_url, timeout=3)
            
            if response.status_code == 200 and response.content:
                # Criar diretório do job
                job_dir = os.path.join('downloads', job_id)
                os.makedirs(job_dir, exist_ok=True)
                
                # Salvar arquivo
                filename = f"{invoice_key}.xml"
                file_path = os.path.join(job_dir, filename)
                
                with open(file_path, 'wb') as f:
                    f.write(response.content)
                
                # Salvar no banco se user_id fornecido
                if user_id:
                    self._save_xml_to_database_simple(response.content.decode('utf-8'), invoice_key, user_id)
                
                elapsed = time.time() - start_time
                logger.info(f"[Job {job_id}] Download concluído em {elapsed:.2f}s")
                
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
    
    def _save_xml_to_database_simple(self, xml_content: str, invoice_key: str, user_id: int):
        """Salvar XML no banco de dados de forma simplificada"""
        try:
            from models import XMLFile
            from new_app import app, db
            
            with app.app_context():
                # Verificar se já existe
                existing = XMLFile.query.filter_by(
                    invoice_key=invoice_key,
                    user_id=user_id
                ).first()
                
                if existing:
                    logger.info(f"XML {invoice_key} já existe no banco para usuário {user_id}")
                    return
                
                # Extrair dados básicos do XML
                xml_data = self._extract_basic_xml_data(xml_content)
                
                # Criar novo registro
                xml_file = XMLFile()
                xml_file.user_id = user_id
                xml_file.invoice_key = invoice_key
                xml_file.filename = f"{invoice_key}.xml"
                xml_file.xml_content = xml_content
                xml_file.import_type = 'SISTEMA'
                
                # Campos básicos extraídos
                xml_file.numero_nf = xml_data.get('numero_nf')
                xml_file.serie_nf = xml_data.get('serie_nf')
                xml_file.data_emissao = xml_data.get('data_emissao')
                xml_file.valor_total = xml_data.get('valor_total')
                xml_file.peso_bruto = xml_data.get('peso_bruto')
                xml_file.quantidade_volumes = xml_data.get('quantidade_volumes', 1)
                xml_file.nome_emitente = xml_data.get('nome_emitente')
                xml_file.destinatario_razao = xml_data.get('nome_destinatario')
                
                db.session.add(xml_file)
                db.session.commit()
                
                logger.info(f"XML {invoice_key} salvo no banco para usuário {user_id}")
                
        except Exception as e:
            logger.error(f"Erro ao salvar XML no banco: {str(e)}")
    
    def _extract_basic_xml_data(self, xml_content: str) -> Dict[str, Any]:
        """Extrair dados básicos do XML de forma rápida"""
        try:
            import xml.etree.ElementTree as ET
            import re
            
            # Parse básico do XML
            root = ET.fromstring(xml_content)
            
            # Buscar dados básicos com XPath simples
            data = {}
            
            # Número da NF
            nf_num = root.find('.//nNF')
            data['numero_nf'] = nf_num.text if nf_num is not None else None
            
            # Série
            serie = root.find('.//serie')
            data['serie_nf'] = serie.text if serie is not None else None
            
            # Data de emissão
            data_em = root.find('.//dhEmi')
            if data_em is not None:
                from datetime import datetime
                try:
                    data['data_emissao'] = datetime.fromisoformat(data_em.text.replace('Z', '+00:00'))
                except:
                    data['data_emissao'] = None
            else:
                data['data_emissao'] = None
            
            # Valor total
            vtotal = root.find('.//vNF')
            if vtotal is not None:
                try:
                    data['valor_total'] = float(vtotal.text)
                except:
                    data['valor_total'] = 0.0
            else:
                data['valor_total'] = 0.0
            
            # Peso bruto
            peso = root.find('.//pesoB')
            if peso is not None:
                try:
                    data['peso_bruto'] = float(peso.text)
                except:
                    data['peso_bruto'] = 0.0
            else:
                data['peso_bruto'] = 0.0
            
            # Quantidade de volumes
            vol = root.find('.//qVol')
            if vol is not None:
                try:
                    data['quantidade_volumes'] = int(vol.text)
                except:
                    data['quantidade_volumes'] = 1
            else:
                data['quantidade_volumes'] = 1
            
            # Nome do emitente
            emit_nome = root.find('.//emit/xNome')
            data['nome_emitente'] = emit_nome.text if emit_nome is not None else None
            
            # Nome do destinatário
            dest_nome = root.find('.//dest/xNome')
            data['nome_destinatario'] = dest_nome.text if dest_nome is not None else None
            
            return data
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados do XML: {str(e)}")
            return {}
    
    def cleanup(self):
        """Limpeza rápida dos recursos"""
        try:
            if self.driver:
                self.driver.quit()
        except Exception as e:
            logger.error(f"Erro na limpeza: {str(e)}")

# Função principal para integração
def process_xml_downloads_speed_optimized(job_id: str, invoice_keys: list, user_id: int) -> Dict[str, Any]:
    """Processar downloads com velocidade otimizada"""
    start_time = time.time()
    downloader = None
    
    try:
        downloader = SpeedOptimizedDownloader()
        results = []
        successful = 0
        failed = 0
        
        logger.info(f"[Job {job_id}] Iniciando {len(invoice_keys)} downloads otimizados")
        
        for i, invoice_key in enumerate(invoice_keys):
            logger.info(f"[Job {job_id}] Processando {i+1}/{len(invoice_keys)}: {invoice_key}")
            
            result = downloader.download_xml_speed_optimized(invoice_key, job_id, user_id)
            result['invoice_key'] = invoice_key
            results.append(result)
            
            if result['success']:
                successful += 1
            else:
                failed += 1
        
        elapsed = time.time() - start_time
        logger.info(f"[Job {job_id}] Concluído: {successful}/{len(invoice_keys)} sucessos em {elapsed:.2f}s")
        
        return {
            'success': True,
            'results': results,
            'total_time': elapsed,
            'successful_count': successful,
            'total_count': len(invoice_keys),
            'files': [{'filename': r.get('filename'), 'size': r.get('size', 0)} for r in results if r['success']],
            'errors': [{'invoice_key': r['invoice_key'], 'error': r.get('error')} for r in results if not r['success']]
        }
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"[Job {job_id}] Erro crítico após {elapsed:.2f}s: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'total_time': elapsed
        }
    finally:
        if downloader:
            downloader.cleanup()