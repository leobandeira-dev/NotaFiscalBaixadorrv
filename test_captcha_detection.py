#!/usr/bin/env python3
"""
Teste de detecção e resolução de CAPTCHA
Testando especificamente o modal mostrado na imagem do usuário
"""
import logging
import time
from selenium.webdriver.common.by import By
from consultardanfe_automation import ConsultarDanfeAutomation

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_captcha_detection():
    """Testar detecção e resolução de CAPTCHA"""
    print("🧪 TESTE DE CAPTCHA - consultardanfe.com")
    print("=" * 50)
    
    downloader = ConsultarDanfeAutomation()
    
    try:
        if not downloader.setup_driver():
            print("❌ Falha ao configurar WebDriver")
            return False
        
        print("🌐 Navegando para consultardanfe.com...")
        downloader.driver.get(downloader.base_url)
        time.sleep(3)
        
        print(f"📍 URL atual: {downloader.driver.current_url}")
        print(f"📝 Título: {downloader.driver.title}")
        
        # Inserir chave de teste
        test_key = "35250513516247000107550010000113401146202508"
        print(f"🔑 Inserindo chave de teste: {test_key}")
        
        # Encontrar campo de entrada
        input_field = None
        input_selectors = [
            "input[placeholder*='chave']",
            "input[type='text']",
            "input.form-control"
        ]
        
        for selector in input_selectors:
            try:
                elements = downloader.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        placeholder = element.get_attribute('placeholder') or ''
                        if 'chave' in placeholder.lower():
                            input_field = element
                            print(f"✅ Campo encontrado: {selector} (placeholder: '{placeholder}')")
                            break
                if input_field:
                    break
            except Exception as e:
                print(f"❌ Erro com seletor {selector}: {e}")
        
        if not input_field:
            print("❌ Campo de entrada não encontrado")
            return False
        
        # Inserir chave
        input_field.clear()
        input_field.send_keys(test_key)
        print("✅ Chave inserida")
        
        # Procurar botão de busca
        button_selectors = [
            "//button[contains(text(), 'Buscar DANFE/XML')]",
            "//button[contains(text(), 'Buscar')]",
            "button[type='submit']",
            ".btn-primary"
        ]
        
        submit_button = None
        for selector in button_selectors:
            try:
                if selector.startswith("//"):
                    elements = downloader.driver.find_elements(By.XPATH, selector)
                else:
                    elements = downloader.driver.find_elements(By.CSS_SELECTOR, selector)
                
                for element in elements:
                    if element.is_displayed() and element.is_enabled():
                        submit_button = element
                        print(f"✅ Botão encontrado: {selector}")
                        break
                if submit_button:
                    break
            except Exception as e:
                print(f"❌ Erro com seletor de botão {selector}: {e}")
        
        if not submit_button:
            print("❌ Botão de busca não encontrado")
            return False
        
        # Verificar CAPTCHA antes de submeter
        print("🔍 Verificando CAPTCHA antes da submissão...")
        captcha_detected = downloader.detect_captcha()
        if captcha_detected:
            print("🤖 CAPTCHA detectado ANTES da submissão!")
            
            print("🔧 Tentando resolver CAPTCHA...")
            resolved = downloader.handle_simple_captcha()
            if resolved:
                print("✅ CAPTCHA resolvido com sucesso!")
            else:
                print("❌ Falha ao resolver CAPTCHA")
        else:
            print("✅ Nenhum CAPTCHA detectado antes da submissão")
        
        # Clicar no botão
        print("🖱️ Clicando no botão de busca...")
        submit_button.click()
        
        # Aguardar resposta
        print("⏳ Aguardando resposta...")
        time.sleep(5)
        
        # Verificar CAPTCHA após submissão
        print("🔍 Verificando CAPTCHA APÓS submissão...")
        captcha_after = downloader.detect_captcha()
        if captcha_after:
            print("🤖 CAPTCHA apareceu APÓS submissão!")
            print("📋 Detalhes da página:")
            print(f"   URL: {downloader.driver.current_url}")
            print(f"   Título: {downloader.driver.title}")
            
            # Tentar capturar elementos do modal
            try:
                modal_elements = downloader.driver.find_elements(By.CSS_SELECTOR, "div[style*='z-index']")
                print(f"   Modais encontrados: {len(modal_elements)}")
                
                # Procurar texto específico do modal
                page_text = downloader.driver.page_source.lower()
                if 'para visualizar o danfe' in page_text:
                    print("✅ Modal de CAPTCHA confirmado!")
                if 'não sou um robô' in page_text:
                    print("✅ Checkbox reCAPTCHA confirmado!")
                    
            except Exception as e:
                print(f"❌ Erro ao analisar modal: {e}")
            
            print("🔧 Tentando resolver CAPTCHA pós-submissão...")
            resolved_after = downloader.handle_simple_captcha()
            if resolved_after:
                print("✅ CAPTCHA pós-submissão resolvido!")
                
                # Aguardar e verificar se progrediu
                time.sleep(3)
                final_url = downloader.driver.current_url
                final_title = downloader.driver.title
                print(f"🎯 URL final: {final_url}")
                print(f"🎯 Título final: {final_title}")
                
                # Procurar opções de download
                try:
                    download_buttons = downloader.driver.find_elements(By.XPATH, "//button[contains(text(), 'Download')]")
                    if download_buttons:
                        print(f"✅ {len(download_buttons)} botão(ões) de download encontrado(s)!")
                        for i, btn in enumerate(download_buttons):
                            print(f"   Botão {i+1}: {btn.text}")
                    else:
                        print("❌ Nenhum botão de download encontrado")
                except Exception as e:
                    print(f"❌ Erro ao procurar botões de download: {e}")
                    
            else:
                print("❌ Falha ao resolver CAPTCHA pós-submissão")
        else:
            print("✅ Nenhum CAPTCHA detectado após submissão")
            
            # Procurar diretamente por opções de download
            try:
                download_buttons = downloader.driver.find_elements(By.XPATH, "//button[contains(text(), 'Download')]")
                if download_buttons:
                    print(f"✅ {len(download_buttons)} botão(ões) de download encontrado(s) sem CAPTCHA!")
                    for i, btn in enumerate(download_buttons):
                        print(f"   Botão {i+1}: {btn.text}")
                else:
                    print("❌ Nenhum botão de download encontrado")
            except Exception as e:
                print(f"❌ Erro ao procurar botões de download: {e}")
        
        print("✅ Teste de CAPTCHA concluído!")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        return False
        
    finally:
        downloader.cleanup()

if __name__ == "__main__":
    success = test_captcha_detection()
    print("\n" + "=" * 50)
    if success:
        print("🎯 Resultado: TESTE CONCLUÍDO COM SUCESSO")
    else:
        print("💥 Resultado: TESTE FALHOU")