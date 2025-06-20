#!/usr/bin/env python3
"""
Sistema de Automação CROSSWMS para Download de XMLs NFe
Replica o comportamento manual de usuário no site meudanfe.com.br
"""

import os
import sys
import time
import subprocess
import tkinter as tk
from tkinter import messagebox, ttk
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import glob
from datetime import datetime
import threading

class AutomacaoCROSSWMS:
    def __init__(self):
        self.pasta_base = "C:\\CROSSWMS"
        self.pasta_downloads = os.path.join(self.pasta_base, "XMLs_Baixados")
        self.driver = None
        self.janela = None
        self.progresso = None
        self.log_texto = None
        self.setup_pasta()
        
    def setup_pasta(self):
        """Cria estrutura de pastas necessária"""
        try:
            os.makedirs(self.pasta_base, exist_ok=True)
            os.makedirs(self.pasta_downloads, exist_ok=True)
            self.log(f"Pasta CROSSWMS configurada: {self.pasta_base}")
        except Exception as e:
            self.log(f"Erro ao criar pastas: {e}")
    
    def log(self, mensagem):
        """Adiciona mensagem ao log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_completo = f"[{timestamp}] {mensagem}"
        print(log_completo)
        
        if hasattr(self, 'log_texto') and self.log_texto:
            self.log_texto.insert(tk.END, log_completo + "\n")
            self.log_texto.see(tk.END)
            self.janela.update()
    
    def criar_interface(self):
        """Cria interface gráfica"""
        self.janela = tk.Tk()
        self.janela.title("Automação CROSSWMS - Download XMLs NFe")
        self.janela.geometry("600x500")
        
        # Frame principal
        frame_principal = tk.Frame(self.janela, padx=20, pady=20)
        frame_principal.pack(fill=tk.BOTH, expand=True)
        
        # Título
        titulo = tk.Label(frame_principal, text="Automação CROSSWMS", 
                         font=("Arial", 16, "bold"))
        titulo.pack(pady=(0, 20))
        
        # Campo de entrada da chave NFe
        tk.Label(frame_principal, text="Chave da Nota Fiscal (44 dígitos):", 
                font=("Arial", 10)).pack(anchor="w")
        
        self.entrada_chave = tk.Entry(frame_principal, width=50, font=("Courier", 12))
        self.entrada_chave.pack(pady=(5, 15), fill="x")
        
        # Botões
        frame_botoes = tk.Frame(frame_principal)
        frame_botoes.pack(pady=(0, 20))
        
        self.btn_iniciar = tk.Button(frame_botoes, text="Iniciar Automação", 
                                   command=self.iniciar_automacao,
                                   bg="#4CAF50", fg="white", 
                                   font=("Arial", 12, "bold"),
                                   padx=20, pady=10)
        self.btn_iniciar.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_pasta = tk.Button(frame_botoes, text="Abrir Pasta XMLs", 
                                 command=self.abrir_pasta_downloads,
                                 bg="#2196F3", fg="white", 
                                 font=("Arial", 12),
                                 padx=20, pady=10)
        self.btn_pasta.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_sair = tk.Button(frame_botoes, text="Sair", 
                                command=self.sair,
                                bg="#f44336", fg="white", 
                                font=("Arial", 12),
                                padx=20, pady=10)
        self.btn_sair.pack(side=tk.LEFT)
        
        # Barra de progresso
        self.progresso = ttk.Progressbar(frame_principal, mode='indeterminate')
        self.progresso.pack(fill="x", pady=(0, 10))
        
        # Área de log
        tk.Label(frame_principal, text="Log da Automação:", 
                font=("Arial", 10, "bold")).pack(anchor="w")
        
        frame_log = tk.Frame(frame_principal)
        frame_log.pack(fill=tk.BOTH, expand=True)
        
        self.log_texto = tk.Text(frame_log, height=15, wrap=tk.WORD)
        scrollbar = tk.Scrollbar(frame_log)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_texto.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.log_texto.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_texto.yview)
        
        # Log inicial
        self.log("Sistema de Automação CROSSWMS iniciado")
        self.log(f"Pasta de downloads: {self.pasta_downloads}")
        self.log("Digite a chave NFe e clique em 'Iniciar Automação'")
        
    def validar_chave_nfe(self, chave):
        """Valida formato da chave NFe"""
        if not chave:
            return False, "Chave NFe é obrigatória"
        
        chave = chave.strip().replace(" ", "").replace("-", "")
        
        if len(chave) != 44:
            return False, "Chave NFe deve ter exatamente 44 dígitos"
        
        if not chave.isdigit():
            return False, "Chave NFe deve conter apenas números"
        
        return True, chave
    
    def setup_chrome_driver(self):
        """Configura ChromeDriver para download automático"""
        try:
            chrome_options = Options()
            
            # Configurações de download
            prefs = {
                "download.default_directory": self.pasta_downloads,
                "download.prompt_for_download": False,
                "download.directory_upgrade": True,
                "safebrowsing.enabled": True,
                "profile.default_content_settings.popups": 0
            }
            chrome_options.add_experimental_option("prefs", prefs)
            
            # Configurações do Chrome para simular usuário real
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--window-size=1366,768")
            
            # Tenta usar ChromeDriver local primeiro
            chromedriver_path = os.path.join(os.getcwd(), "chromedriver.exe")
            if os.path.exists(chromedriver_path):
                service = Service(chromedriver_path)
                self.driver = webdriver.Chrome(service=service, options=chrome_options)
                self.log("Usando ChromeDriver local")
            else:
                # Fallback para ChromeDriver do sistema
                self.driver = webdriver.Chrome(options=chrome_options)
                self.log("Usando ChromeDriver do sistema")
            
            # Remove indicadores de automação
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            self.driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            })
            
            return True
            
        except Exception as e:
            self.log(f"Erro ao configurar Chrome: {e}")
            return False
    
    def executar_automacao_real(self, chave_nfe):
        """Executa automação real simulando comportamento humano"""
        try:
            self.log("=== INICIANDO AUTOMAÇÃO REAL ===")
            self.log(f"Chave NFe: {chave_nfe}")
            
            # 1. Configurar Chrome
            if not self.setup_chrome_driver():
                raise Exception("Falha ao configurar ChromeDriver")
            
            # 2. Navegar para o site
            self.log("Navegando para meudanfe.com.br...")
            self.driver.get("https://meudanfe.com.br")
            
            # Simula tempo de carregamento humano
            time.sleep(3)
            
            # 3. Procurar campo de entrada
            self.log("Procurando campo de entrada da chave NFe...")
            
            # Lista de possíveis seletores para o campo de entrada
            seletores_input = [
                'input[placeholder*="chave"]',
                'input[placeholder*="CHAVE"]',
                'input[name*="chave"]',
                'input[id*="chave"]',
                'input[type="text"]',
                'input[type="search"]'
            ]
            
            campo_entrada = None
            for seletor in seletores_input:
                try:
                    campos = self.driver.find_elements(By.CSS_SELECTOR, seletor)
                    for campo in campos:
                        if campo.is_displayed() and campo.is_enabled():
                            campo_entrada = campo
                            break
                    if campo_entrada:
                        break
                except:
                    continue
            
            if not campo_entrada:
                raise Exception("Campo de entrada da chave NFe não encontrado")
            
            self.log("Campo de entrada encontrado!")
            
            # 4. Preencher chave NFe simulando digitação humana
            self.log("Preenchendo chave NFe...")
            campo_entrada.click()
            time.sleep(0.5)
            campo_entrada.clear()
            time.sleep(0.5)
            
            # Digita a chave simulando velocidade humana
            for char in chave_nfe:
                campo_entrada.send_keys(char)
                time.sleep(0.05)  # Simula velocidade de digitação
            
            time.sleep(1)
            
            # 5. Procurar e clicar botão de busca
            self.log("Procurando botão de busca...")
            
            # Lista de possíveis textos e seletores para botão
            botao_busca = None
            
            # Primeiro tenta por texto visível
            textos_botao = ["Buscar", "BUSCAR", "Buscar DANFE/XML", "Consultar"]
            for texto in textos_botao:
                try:
                    elementos = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{texto}')]")
                    for elem in elementos:
                        if elem.tag_name in ["button", "input", "a"] and elem.is_displayed():
                            botao_busca = elem
                            break
                    if botao_busca:
                        break
                except:
                    continue
            
            # Se não encontrou, tenta por seletores
            if not botao_busca:
                seletores_botao = [
                    'button[type="submit"]',
                    'input[type="submit"]',
                    'button',
                    '.btn',
                    '#buscar',
                    '[name="buscar"]'
                ]
                
                for seletor in seletores_botao:
                    try:
                        botoes = self.driver.find_elements(By.CSS_SELECTOR, seletor)
                        for botao in botoes:
                            if botao.is_displayed() and botao.is_enabled():
                                texto_botao = botao.text.lower()
                                if any(palavra in texto_botao for palavra in ["buscar", "consultar", "search"]):
                                    botao_busca = botao
                                    break
                        if botao_busca:
                            break
                    except:
                        continue
            
            if not botao_busca:
                raise Exception("Botão de busca não encontrado")
            
            self.log("Botão de busca encontrado! Clicando...")
            
            # Simula movimento do mouse e clique
            self.driver.execute_script("arguments[0].scrollIntoView(true);", botao_busca)
            time.sleep(0.5)
            botao_busca.click()
            
            # 6. Aguardar resultados
            self.log("Aguardando resultados da busca...")
            time.sleep(5)
            
            # 7. Procurar botão de download
            self.log("Procurando botão de download do XML...")
            
            botao_download = None
            textos_download = ["Baixar XML", "Download XML", "Baixar", "Download", "XML"]
            
            for texto in textos_download:
                try:
                    elementos = self.driver.find_elements(By.XPATH, f"//*[contains(text(), '{texto}')]")
                    for elem in elementos:
                        if elem.tag_name in ["button", "input", "a"] and elem.is_displayed():
                            botao_download = elem
                            break
                    if botao_download:
                        break
                except:
                    continue
            
            # Também procura por links de download
            if not botao_download:
                try:
                    links = self.driver.find_elements(By.TAG_NAME, "a")
                    for link in links:
                        href = link.get_attribute("href") or ""
                        if "xml" in href.lower() or "download" in href.lower():
                            if link.is_displayed():
                                botao_download = link
                                break
                except:
                    pass
            
            if not botao_download:
                # Verifica se a NFe foi encontrada mas não tem download disponível
                page_source = self.driver.page_source.lower()
                if chave_nfe in page_source and ("encontrada" in page_source or "sucesso" in page_source):
                    raise Exception("NFe encontrada mas download não disponível publicamente")
                else:
                    raise Exception("NFe não encontrada no sistema")
            
            self.log("Botão de download encontrado! Iniciando download...")
            
            # 8. Fazer download
            self.driver.execute_script("arguments[0].scrollIntoView(true);", botao_download)
            time.sleep(0.5)
            botao_download.click()
            
            # 9. Aguardar download completar
            self.log("Aguardando download completar...")
            arquivo_xml = self.aguardar_download(chave_nfe, timeout=30)
            
            if arquivo_xml:
                self.log(f"✅ Download concluído: {arquivo_xml}")
                return True, arquivo_xml
            else:
                raise Exception("Download não completou no tempo esperado")
            
        except Exception as e:
            self.log(f"❌ Erro na automação: {str(e)}")
            return False, str(e)
        
        finally:
            if self.driver:
                self.driver.quit()
                self.log("Navegador fechado")
    
    def aguardar_download(self, chave_nfe, timeout=30):
        """Aguarda download do XML completar"""
        inicio = time.time()
        
        while time.time() - inicio < timeout:
            # Procura arquivos XML na pasta
            arquivos_xml = glob.glob(os.path.join(self.pasta_downloads, "*.xml"))
            
            for arquivo in arquivos_xml:
                # Ignora arquivos temporários
                if arquivo.endswith('.crdownload') or arquivo.endswith('.tmp'):
                    continue
                
                try:
                    # Verifica se o arquivo contém a chave NFe
                    with open(arquivo, 'r', encoding='utf-8', errors='ignore') as f:
                        conteudo = f.read()
                        if chave_nfe in conteudo:
                            return arquivo
                except:
                    continue
            
            time.sleep(1)
            self.log("Aguardando download...")
        
        return None
    
    def abrir_pasta_downloads(self):
        """Abre pasta de downloads no Windows Explorer"""
        try:
            if os.path.exists(self.pasta_downloads):
                subprocess.Popen(f'explorer "{self.pasta_downloads}"')
                self.log(f"Pasta aberta: {self.pasta_downloads}")
            else:
                messagebox.showwarning("Aviso", "Pasta de downloads não existe ainda")
        except Exception as e:
            self.log(f"Erro ao abrir pasta: {e}")
    
    def iniciar_automacao(self):
        """Inicia processo de automação"""
        chave = self.entrada_chave.get().strip()
        
        # Validar chave
        valida, resultado = self.validar_chave_nfe(chave)
        if not valida:
            messagebox.showerror("Erro", resultado)
            return
        
        chave_nfe = resultado
        
        # Desabilitar botão e iniciar progresso
        self.btn_iniciar.config(state="disabled")
        self.progresso.start(10)
        
        # Executar em thread separada
        def executar():
            try:
                sucesso, resultado_automacao = self.executar_automacao_real(chave_nfe)
                
                if sucesso:
                    self.log("=== AUTOMAÇÃO CONCLUÍDA COM SUCESSO ===")
                    self.log("Abrindo pasta de downloads...")
                    self.abrir_pasta_downloads()
                    
                    # Pergunta se quer abrir o sistema web
                    resposta = messagebox.askyesno(
                        "Sucesso", 
                        f"XML baixado com sucesso!\n\n"
                        f"Arquivo: {os.path.basename(resultado_automacao)}\n\n"
                        f"Deseja abrir o sistema web CROSSWMS para fazer upload?"
                    )
                    
                    if resposta:
                        self.abrir_sistema_web()
                else:
                    self.log("=== AUTOMAÇÃO FALHOU ===")
                    messagebox.showerror("Erro", f"Automação falhou: {resultado_automacao}")
                
            except Exception as e:
                self.log(f"Erro inesperado: {e}")
                messagebox.showerror("Erro", f"Erro inesperado: {e}")
            
            finally:
                # Reabilitar interface
                self.progresso.stop()
                self.btn_iniciar.config(state="normal")
        
        # Iniciar thread
        thread = threading.Thread(target=executar)
        thread.daemon = True
        thread.start()
    
    def abrir_sistema_web(self):
        """Abre sistema web CROSSWMS"""
        try:
            import webbrowser
            # Substitua pela URL real do seu sistema
            url_sistema = "http://localhost:5000"  # ou a URL de produção
            webbrowser.open(url_sistema)
            self.log(f"Sistema web aberto: {url_sistema}")
        except Exception as e:
            self.log(f"Erro ao abrir sistema web: {e}")
    
    def sair(self):
        """Fecha aplicação"""
        if self.driver:
            self.driver.quit()
        self.janela.destroy()
    
    def executar(self):
        """Executa aplicação"""
        self.criar_interface()
        self.janela.mainloop()

def main():
    """Ponto de entrada principal"""
    print("Iniciando Sistema de Automação CROSSWMS...")
    
    # Verificar se está no Windows
    if os.name != 'nt':
        print("AVISO: Sistema otimizado para Windows")
    
    # Verificar dependências
    try:
        from selenium import webdriver
        print("✅ Selenium instalado")
    except ImportError:
        print("❌ Selenium não instalado. Execute: pip install selenium")
        input("Pressione Enter para sair...")
        return
    
    # Iniciar aplicação
    app = AutomacaoCROSSWMS()
    app.executar()

if __name__ == "__main__":
    main()