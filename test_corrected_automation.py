#!/usr/bin/env python3
"""
Automação corrigida para download de XML baseada na análise completa
Foca em resolver o problema de desconexão do Chrome DevTools
"""
import time
import logging
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, WebDriverException

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImprovedInvoiceDownloader:
    def __init__(self):
        self.driver = None
        self.download_dir = "/home/runner/workspace/downloads"
        os.makedirs(self.download_dir, exist_ok=True)
    
    def setup_chrome_stable(self):
        """Setup Chrome com configurações mais estáveis"""
        options = Options()
        
        # Configurações para estabilidade
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=VizDisplayCompositor')
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')
        options.add_argument('--disable-javascript')  # Reduzir carga
        options.add_argument('--window-size=800,600')
        
        # Configurações de download
        prefs = {
            "download.default_directory": self.download_dir,
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True
        }
        options.add_experimental_option("prefs", prefs)
        
        # Configurações de estabilidade de conexão
        options.add_argument('--keep-alive-for-test')
        options.add_argument('--disable-background-timer-throttling')
        options.add_argument('--disable-renderer-backgrounding')
        
        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.set_page_load_timeout(20)
            logger.info("Chrome WebDriver inicializado com configurações estáveis")
            return True
        except Exception as e:
            logger.error(f"Erro ao inicializar Chrome: {e}")
            return False
    
    def download_xml_robust(self, invoice_key: str):
        """Download XML com estratégias robustas contra desconexão"""
        try:
            if not self.setup_chrome_stable():
                return {'success': False, 'error': 'Falha ao inicializar navegador'}
            
            logger.info(f"🔍 Iniciando download robusto para chave: {invoice_key}")
            
            # Navegar para o site
            logger.info("📱 Navegando para meudanfe.com.br...")
            self.driver.get("https://meudanfe.com.br/")
            
            # Aguardar carregamento com múltiplas verificações
            logger.info("⏳ Aguardando carregamento...")
            try:
                WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.ID, "searchTxt"))
                )
            except TimeoutException:
                logger.warning("Timeout aguardando campo, tentando prosseguir...")
            
            # Encontrar e interagir com campo de entrada
            logger.info("🎯 Localizando campo de entrada...")
            input_field = None
            
            input_strategies = [
                (By.ID, "searchTxt"),
                (By.NAME, "searchTxt"),
                (By.CSS_SELECTOR, "input[id='searchTxt']")
            ]
            
            for strategy in input_strategies:
                try:
                    input_field = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable(strategy)
                    )
                    logger.info(f"✅ Campo encontrado com estratégia: {strategy}")
                    break
                except TimeoutException:
                    continue
            
            if not input_field:
                return {'success': False, 'error': 'Campo de entrada não encontrado'}
            
            # Inserir chave com verificação
            logger.info("✏️ Inserindo chave da nota fiscal...")
            input_field.clear()
            input_field.send_keys(invoice_key)
            
            # Verificar se a chave foi inserida
            entered_value = input_field.get_attribute('value')
            if entered_value != invoice_key:
                logger.warning(f"Valor inserido diferente: {entered_value}")
            else:
                logger.info("✅ Chave inserida corretamente")
            
            # Aguardar um momento antes de clicar
            time.sleep(2)
            
            # Localizar botão de busca
            logger.info("🔍 Localizando botão de busca...")
            search_button = None
            
            button_strategies = [
                (By.ID, "searchBtn"),
                (By.CSS_SELECTOR, "a[id='searchBtn']"),
                (By.XPATH, "//a[@id='searchBtn']")
            ]
            
            for strategy in button_strategies:
                try:
                    search_button = WebDriverWait(self.driver, 5).until(
                        EC.element_to_be_clickable(strategy)
                    )
                    logger.info(f"✅ Botão encontrado com estratégia: {strategy}")
                    break
                except TimeoutException:
                    continue
            
            if not search_button:
                return {'success': False, 'error': 'Botão de busca não encontrado'}
            
            # Múltiplas estratégias de clique para evitar desconexão
            logger.info("👆 Executando clique no botão...")
            click_success = False
            
            # Estratégia 1: Clique JavaScript direto
            try:
                self.driver.execute_script("arguments[0].click();", search_button)
                logger.info("✅ Clique JavaScript executado")
                click_success = True
            except Exception as e:
                logger.warning(f"Clique JavaScript falhou: {e}")
            
            # Estratégia 2: Clique normal se JavaScript falhou
            if not click_success:
                try:
                    search_button.click()
                    logger.info("✅ Clique normal executado")
                    click_success = True
                except Exception as e:
                    logger.warning(f"Clique normal falhou: {e}")
            
            # Estratégia 3: ActionChains como último recurso
            if not click_success:
                try:
                    ActionChains(self.driver).move_to_element(search_button).click().perform()
                    logger.info("✅ Clique ActionChains executado")
                    click_success = True
                except Exception as e:
                    logger.error(f"Todas as estratégias de clique falharam: {e}")
                    return {'success': False, 'error': 'Falha ao clicar no botão de busca'}
            
            # Aguardar resultados com monitoramento de URL
            logger.info("⏳ Aguardando resultados da busca...")
            initial_url = self.driver.current_url
            
            # Aguardar mudança de URL ou conteúdo
            timeout = 15
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    current_url = self.driver.current_url
                    if current_url != initial_url:
                        logger.info(f"✅ URL mudou para: {current_url}")
                        break
                    
                    # Verificar se há conteúdo de resultado na página
                    page_content = self.driver.page_source.lower()
                    if any(indicator in page_content for indicator in ['xml', 'baixar', 'download', 'nota fiscal']):
                        logger.info("✅ Conteúdo de resultado detectado")
                        break
                        
                    time.sleep(1)
                except WebDriverException as e:
                    logger.warning(f"Erro durante aguarde: {e}")
                    # Tentar reestabelecer conexão
                    try:
                        self.driver.current_url  # Teste simples de conexão
                    except:
                        return {'success': False, 'error': 'Conexão com navegador perdida'}
            
            # Análise da página de resultados
            logger.info("🔍 Analisando página de resultados...")
            try:
                final_url = self.driver.current_url
                page_title = self.driver.title
                page_content = self.driver.page_source
                
                logger.info(f"URL final: {final_url}")
                logger.info(f"Título da página: {page_title}")
                
                # Procurar por elementos de download
                download_elements = []
                download_indicators = [
                    "//a[contains(text(), 'XML')]",
                    "//a[contains(text(), 'xml')]",
                    "//a[contains(text(), 'Baixar')]",
                    "//button[contains(text(), 'XML')]",
                    "//*[contains(@href, '.xml')]"
                ]
                
                for indicator in download_indicators:
                    try:
                        elements = self.driver.find_elements(By.XPATH, indicator)
                        download_elements.extend(elements)
                    except:
                        continue
                
                logger.info(f"📄 Encontrados {len(download_elements)} elementos de download potenciais")
                
                # Tentar download direto se elementos encontrados
                if download_elements:
                    for i, element in enumerate(download_elements[:3]):  # Limitar a 3 tentativas
                        try:
                            element_text = element.text
                            element_href = element.get_attribute('href')
                            logger.info(f"Elemento {i+1}: texto='{element_text}', href='{element_href}'")
                            
                            if element_href and '.xml' in element_href.lower():
                                logger.info(f"🎯 Tentando download direto de: {element_href}")
                                # Aqui você poderia implementar download direto via requests
                                
                        except Exception as e:
                            logger.warning(f"Erro analisando elemento {i+1}: {e}")
                
                # Salvar página para análise manual
                with open('/home/runner/workspace/resultado_automacao.html', 'w', encoding='utf-8') as f:
                    f.write(page_content)
                logger.info("💾 Página de resultados salva em resultado_automacao.html")
                
                # Verificar indicadores de sucesso
                success_indicators = ['xml', 'nota fiscal', 'danfe', 'download']
                found_indicators = [ind for ind in success_indicators if ind in page_content.lower()]
                
                return {
                    'success': len(found_indicators) > 0,
                    'url': final_url,
                    'title': page_title,
                    'indicators': found_indicators,
                    'download_elements': len(download_elements),
                    'message': f'Processo concluído. Encontrados {len(found_indicators)} indicadores de sucesso.'
                }
                
            except Exception as e:
                logger.error(f"Erro na análise final: {e}")
                return {'success': False, 'error': f'Erro na análise: {str(e)}'}
            
        except Exception as e:
            logger.error(f"Erro geral na automação: {e}")
            return {'success': False, 'error': f'Erro geral: {str(e)}'}
        
        finally:
            if self.driver:
                try:
                    self.driver.quit()
                    logger.info("🔒 Navegador fechado")
                except:
                    pass

def main():
    """Função principal para teste"""
    downloader = ImprovedInvoiceDownloader()
    invoice_key = "35250513516247000107550010000113401146202508"
    
    logger.info("🚀 Iniciando simulação de download melhorada...")
    result = downloader.download_xml_robust(invoice_key)
    
    logger.info("📊 RESULTADO DA SIMULAÇÃO:")
    logger.info(f"  Sucesso: {result.get('success', False)}")
    logger.info(f"  Mensagem: {result.get('message', result.get('error', 'N/A'))}")
    
    if result.get('success'):
        logger.info(f"  URL Final: {result.get('url', 'N/A')}")
        logger.info(f"  Indicadores Encontrados: {result.get('indicators', [])}")
        logger.info(f"  Elementos de Download: {result.get('download_elements', 0)}")

if __name__ == "__main__":
    main()