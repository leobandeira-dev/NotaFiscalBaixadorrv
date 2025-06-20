#!/usr/bin/env python3
"""
Integrador Web CROSSWMS - Upload Automático de XMLs
Monitora pasta C:\CROSSWMS\XMLs_Baixados e faz upload automático para o sistema web
"""

import os
import time
import requests
import json
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import tkinter as tk
from tkinter import messagebox, ttk
import threading
from datetime import datetime

class MonitorXMLHandler(FileSystemEventHandler):
    def __init__(self, integrador):
        self.integrador = integrador
    
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.xml'):
            self.integrador.log(f"Novo XML detectado: {os.path.basename(event.src_path)}")
            # Aguarda arquivo completar
            time.sleep(2)
            self.integrador.processar_xml(event.src_path)

class IntegradorWebCROSSWMS:
    def __init__(self):
        self.pasta_xmls = "C:\\CROSSWMS\\XMLs_Baixados"
        self.url_sistema = "http://localhost:5000"  # URL do sistema CROSSWMS
        self.janela = None
        self.log_texto = None
        self.observer = None
        self.status_label = None
        self.contador_uploads = 0
        
        # Configurações de upload
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        self.setup_pasta()
    
    def setup_pasta(self):
        """Cria pasta se não existir"""
        try:
            os.makedirs(self.pasta_xmls, exist_ok=True)
        except Exception as e:
            print(f"Erro ao criar pasta: {e}")
    
    def log(self, mensagem):
        """Adiciona mensagem ao log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_completo = f"[{timestamp}] {mensagem}"
        print(log_completo)
        
        if hasattr(self, 'log_texto') and self.log_texto:
            self.log_texto.insert(tk.END, log_completo + "\n")
            self.log_texto.see(tk.END)
            if self.janela:
                self.janela.update()
    
    def criar_interface(self):
        """Cria interface gráfica"""
        self.janela = tk.Tk()
        self.janela.title("Integrador Web CROSSWMS - Monitor de XMLs")
        self.janela.geometry("650x450")
        
        # Frame principal
        frame_principal = tk.Frame(self.janela, padx=20, pady=20)
        frame_principal.pack(fill=tk.BOTH, expand=True)
        
        # Título
        titulo = tk.Label(frame_principal, text="Integrador Web CROSSWMS", 
                         font=("Arial", 16, "bold"))
        titulo.pack(pady=(0, 10))
        
        # Status
        frame_status = tk.Frame(frame_principal)
        frame_status.pack(fill="x", pady=(0, 15))
        
        tk.Label(frame_status, text="Status:", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        self.status_label = tk.Label(frame_status, text="Parado", 
                                   fg="red", font=("Arial", 10))
        self.status_label.pack(side=tk.LEFT, padx=(5, 0))
        
        # Configurações
        frame_config = tk.Frame(frame_principal)
        frame_config.pack(fill="x", pady=(0, 15))
        
        tk.Label(frame_config, text="URL Sistema:", font=("Arial", 10)).pack(side=tk.LEFT)
        self.url_entry = tk.Entry(frame_config, width=40)
        self.url_entry.insert(0, self.url_sistema)
        self.url_entry.pack(side=tk.LEFT, padx=(5, 10))
        
        # Botões
        frame_botoes = tk.Frame(frame_principal)
        frame_botoes.pack(pady=(0, 15))
        
        self.btn_iniciar = tk.Button(frame_botoes, text="Iniciar Monitor", 
                                   command=self.iniciar_monitor,
                                   bg="#4CAF50", fg="white", 
                                   font=("Arial", 11, "bold"),
                                   padx=15, pady=8)
        self.btn_iniciar.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_parar = tk.Button(frame_botoes, text="Parar Monitor", 
                                 command=self.parar_monitor,
                                 bg="#f44336", fg="white", 
                                 font=("Arial", 11),
                                 padx=15, pady=8, state="disabled")
        self.btn_parar.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_testar = tk.Button(frame_botoes, text="Testar Conexão", 
                                  command=self.testar_conexao,
                                  bg="#2196F3", fg="white", 
                                  font=("Arial", 11),
                                  padx=15, pady=8)
        self.btn_testar.pack(side=tk.LEFT, padx=(0, 10))
        
        self.btn_pasta = tk.Button(frame_botoes, text="Abrir Pasta", 
                                 command=self.abrir_pasta,
                                 bg="#FF9800", fg="white", 
                                 font=("Arial", 11),
                                 padx=15, pady=8)
        self.btn_pasta.pack(side=tk.LEFT)
        
        # Informações
        frame_info = tk.Frame(frame_principal)
        frame_info.pack(fill="x", pady=(0, 10))
        
        self.info_label = tk.Label(frame_info, 
                                 text=f"Monitorando: {self.pasta_xmls} | Uploads: 0",
                                 font=("Arial", 9), fg="gray")
        self.info_label.pack()
        
        # Área de log
        tk.Label(frame_principal, text="Log do Sistema:", 
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
        self.log("Integrador Web CROSSWMS iniciado")
        self.log(f"Pasta monitorada: {self.pasta_xmls}")
        self.log("Configure a URL do sistema e clique em 'Iniciar Monitor'")
    
    def testar_conexao(self):
        """Testa conexão com sistema web"""
        url = self.url_entry.get().strip()
        self.url_sistema = url
        
        try:
            self.log(f"Testando conexão com: {url}")
            response = requests.get(url, timeout=10, headers=self.headers)
            
            if response.status_code == 200:
                self.log("✅ Conexão estabelecida com sucesso!")
                messagebox.showinfo("Sucesso", "Conexão com sistema web estabelecida!")
            else:
                self.log(f"⚠️ Resposta HTTP {response.status_code}")
                messagebox.showwarning("Aviso", f"Sistema respondeu com código {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.log(f"❌ Erro de conexão: {e}")
            messagebox.showerror("Erro", f"Erro de conexão:\n{e}")
    
    def iniciar_monitor(self):
        """Inicia monitoramento da pasta"""
        try:
            self.url_sistema = self.url_entry.get().strip()
            
            if not self.url_sistema:
                messagebox.showerror("Erro", "URL do sistema é obrigatória")
                return
            
            # Configura observer
            self.observer = Observer()
            event_handler = MonitorXMLHandler(self)
            self.observer.schedule(event_handler, self.pasta_xmls, recursive=False)
            self.observer.start()
            
            # Atualiza interface
            self.status_label.config(text="Ativo", fg="green")
            self.btn_iniciar.config(state="disabled")
            self.btn_parar.config(state="normal")
            
            self.log("🔍 Monitor iniciado - aguardando novos XMLs...")
            self.log(f"Sistema web: {self.url_sistema}")
            
            # Verifica XMLs existentes
            self.verificar_xmls_existentes()
            
        except Exception as e:
            self.log(f"Erro ao iniciar monitor: {e}")
            messagebox.showerror("Erro", f"Erro ao iniciar monitor:\n{e}")
    
    def parar_monitor(self):
        """Para monitoramento"""
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join()
                self.observer = None
            
            # Atualiza interface
            self.status_label.config(text="Parado", fg="red")
            self.btn_iniciar.config(state="normal")
            self.btn_parar.config(state="disabled")
            
            self.log("🛑 Monitor parado")
            
        except Exception as e:
            self.log(f"Erro ao parar monitor: {e}")
    
    def verificar_xmls_existentes(self):
        """Verifica XMLs já existentes na pasta"""
        try:
            if not os.path.exists(self.pasta_xmls):
                return
            
            arquivos_xml = [f for f in os.listdir(self.pasta_xmls) if f.endswith('.xml')]
            
            if arquivos_xml:
                self.log(f"Encontrados {len(arquivos_xml)} XMLs existentes")
                
                resposta = messagebox.askyesno(
                    "XMLs Existentes", 
                    f"Encontrados {len(arquivos_xml)} XMLs na pasta.\n\n"
                    f"Deseja fazer upload automático destes arquivos?"
                )
                
                if resposta:
                    for arquivo in arquivos_xml:
                        caminho_completo = os.path.join(self.pasta_xmls, arquivo)
                        self.processar_xml(caminho_completo)
                        time.sleep(1)  # Evita sobrecarga
            
        except Exception as e:
            self.log(f"Erro ao verificar XMLs existentes: {e}")
    
    def processar_xml(self, caminho_xml):
        """Processa um arquivo XML para upload"""
        try:
            nome_arquivo = os.path.basename(caminho_xml)
            self.log(f"📤 Processando: {nome_arquivo}")
            
            # Lê conteúdo do XML
            with open(caminho_xml, 'r', encoding='utf-8', errors='ignore') as f:
                conteudo_xml = f.read()
            
            # Extrai chave NFe do nome do arquivo ou conteúdo
            chave_nfe = self.extrair_chave_nfe(nome_arquivo, conteudo_xml)
            
            if not chave_nfe:
                self.log(f"❌ Chave NFe não encontrada em: {nome_arquivo}")
                return
            
            # Faz upload para o sistema
            sucesso = self.upload_xml(chave_nfe, conteudo_xml, nome_arquivo)
            
            if sucesso:
                self.contador_uploads += 1
                self.atualizar_contador()
                self.log(f"✅ Upload concluído: {nome_arquivo}")
                
                # Move arquivo para pasta processados
                self.mover_arquivo_processado(caminho_xml)
            else:
                self.log(f"❌ Falha no upload: {nome_arquivo}")
                
        except Exception as e:
            self.log(f"Erro ao processar {caminho_xml}: {e}")
    
    def extrair_chave_nfe(self, nome_arquivo, conteudo_xml):
        """Extrai chave NFe do arquivo"""
        import re
        
        # Tenta extrair do nome do arquivo
        match = re.search(r'(\d{44})', nome_arquivo)
        if match:
            return match.group(1)
        
        # Tenta extrair do conteúdo XML
        patterns = [
            r'<chNFe>(\d{44})</chNFe>',
            r'chave="(\d{44})"',
            r'Id="NFe(\d{44})"'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, conteudo_xml)
            if match:
                return match.group(1)
        
        return None
    
    def upload_xml(self, chave_nfe, conteudo_xml, nome_arquivo):
        """Faz upload do XML para o sistema web"""
        try:
            # Prepara dados para upload
            files = {
                'xml': (nome_arquivo, conteudo_xml, 'application/xml')
            }
            
            data = {
                'chave': chave_nfe,
                'fonte': 'automacao_local'
            }
            
            # Endpoint de upload (ajustar conforme API do sistema)
            url_upload = f"{self.url_sistema}/api/xml/upload"
            
            # Faz upload
            response = requests.post(
                url_upload, 
                files=files, 
                data=data, 
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                try:
                    resultado = response.json()
                    if resultado.get('success'):
                        return True
                    else:
                        self.log(f"Sistema rejeitou upload: {resultado.get('error', 'Erro desconhecido')}")
                        return False
                except:
                    # Se não é JSON, mas status 200, considera sucesso
                    return True
            else:
                self.log(f"Erro HTTP {response.status_code}: {response.text[:100]}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.log(f"Erro de rede no upload: {e}")
            return False
        except Exception as e:
            self.log(f"Erro no upload: {e}")
            return False
    
    def mover_arquivo_processado(self, caminho_xml):
        """Move arquivo para pasta de processados"""
        try:
            pasta_processados = os.path.join(os.path.dirname(caminho_xml), "Processados")
            os.makedirs(pasta_processados, exist_ok=True)
            
            nome_arquivo = os.path.basename(caminho_xml)
            novo_caminho = os.path.join(pasta_processados, nome_arquivo)
            
            # Se arquivo já existe, adiciona timestamp
            if os.path.exists(novo_caminho):
                nome_base, ext = os.path.splitext(nome_arquivo)
                timestamp = datetime.now().strftime("_%Y%m%d_%H%M%S")
                novo_nome = f"{nome_base}{timestamp}{ext}"
                novo_caminho = os.path.join(pasta_processados, novo_nome)
            
            os.rename(caminho_xml, novo_caminho)
            self.log(f"📁 Arquivo movido para: Processados/{os.path.basename(novo_caminho)}")
            
        except Exception as e:
            self.log(f"Erro ao mover arquivo: {e}")
    
    def atualizar_contador(self):
        """Atualiza contador de uploads na interface"""
        if self.info_label:
            self.info_label.config(
                text=f"Monitorando: {self.pasta_xmls} | Uploads: {self.contador_uploads}"
            )
    
    def abrir_pasta(self):
        """Abre pasta de XMLs"""
        try:
            import subprocess
            if os.path.exists(self.pasta_xmls):
                subprocess.Popen(f'explorer "{self.pasta_xmls}"')
            else:
                messagebox.showwarning("Aviso", "Pasta não existe ainda")
        except Exception as e:
            self.log(f"Erro ao abrir pasta: {e}")
    
    def sair(self):
        """Fecha aplicação"""
        self.parar_monitor()
        if self.janela:
            self.janela.destroy()
    
    def executar(self):
        """Executa aplicação"""
        self.criar_interface()
        
        # Configura fechamento
        self.janela.protocol("WM_DELETE_WINDOW", self.sair)
        
        self.janela.mainloop()

def main():
    """Ponto de entrada principal"""
    print("Iniciando Integrador Web CROSSWMS...")
    
    # Verificar dependências
    try:
        import watchdog
        print("✅ Watchdog instalado")
    except ImportError:
        print("❌ Watchdog não instalado. Execute: pip install watchdog")
        input("Pressione Enter para sair...")
        return
    
    try:
        import requests
        print("✅ Requests instalado")
    except ImportError:
        print("❌ Requests não instalado. Execute: pip install requests")
        input("Pressione Enter para sair...")
        return
    
    # Iniciar aplicação
    app = IntegradorWebCROSSWMS()
    app.executar()

if __name__ == "__main__":
    main()