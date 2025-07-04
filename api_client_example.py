#!/usr/bin/env python3
"""
Cliente Python para a API do XML Downloader
Exemplo completo de uso da API para download automático de XMLs
"""

import requests
import time
import os
from typing import List, Dict, Optional

class XMLDownloaderAPIClient:
    """Cliente para a API do XML Downloader"""
    
    def __init__(self, base_url: str = "https://crossxml.com.br"):
        """
        Inicializa o cliente da API
        
        Args:
            base_url: URL base da API (ex: https://crossxml.com.br)
        """
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api/v1"
        
    def health_check(self) -> Dict:
        """Verifica se a API está funcionando"""
        response = requests.get(f"{self.api_url}/health")
        response.raise_for_status()
        return response.json()
    
    def create_job(self, invoice_keys: List[str], callback_url: Optional[str] = None) -> Dict:
        """
        Cria um novo job de download
        
        Args:
            invoice_keys: Lista de chaves de notas fiscais (44 dígitos cada)
            callback_url: URL opcional para webhook de callback
            
        Returns:
            Dados do job criado
        """
        payload = {"invoice_keys": invoice_keys}
        if callback_url:
            payload["callback_url"] = callback_url
            
        response = requests.post(f"{self.api_url}/jobs", json=payload)
        response.raise_for_status()
        return response.json()
    
    def get_job_status(self, job_id: str) -> Dict:
        """Obtém o status de um job específico"""
        response = requests.get(f"{self.api_url}/jobs/{job_id}")
        response.raise_for_status()
        return response.json()
    
    def list_jobs(self, status: Optional[str] = None, limit: int = 50, offset: int = 0) -> Dict:
        """
        Lista jobs com filtros opcionais
        
        Args:
            status: Filtrar por status ('running', 'completed', 'failed')
            limit: Número máximo de jobs por página
            offset: Número de jobs a pular
        """
        params = {"limit": limit, "offset": offset}
        if status:
            params["status"] = status
            
        response = requests.get(f"{self.api_url}/jobs", params=params)
        response.raise_for_status()
        return response.json()
    
    def list_job_files(self, job_id: str) -> Dict:
        """Lista arquivos de um job específico"""
        response = requests.get(f"{self.api_url}/jobs/{job_id}/files")
        response.raise_for_status()
        return response.json()
    
    def download_file(self, job_id: str, filename: str, save_path: str = ".") -> str:
        """
        Baixa um arquivo XML específico
        
        Args:
            job_id: ID do job
            filename: Nome do arquivo
            save_path: Diretório para salvar o arquivo
            
        Returns:
            Caminho completo do arquivo baixado
        """
        response = requests.get(f"{self.api_url}/jobs/{job_id}/files/{filename}")
        response.raise_for_status()
        
        file_path = os.path.join(save_path, filename)
        
        with open(file_path, 'wb') as f:
            f.write(response.content)
            
        return file_path
    
    def test_connection(self) -> Dict:
        """Testa a conexão do sistema de automação"""
        response = requests.post(f"{self.api_url}/test")
        response.raise_for_status()
        return response.json()
    
    def wait_for_completion(self, job_id: str, poll_interval: int = 5, timeout: int = 300) -> Dict:
        """
        Aguarda a conclusão de um job com polling
        
        Args:
            job_id: ID do job
            poll_interval: Intervalo entre verificações em segundos
            timeout: Timeout máximo em segundos
            
        Returns:
            Status final do job
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            status = self.get_job_status(job_id)
            
            print(f"Job {job_id}: {status['progress']['percentage']:.1f}% completo "
                  f"({status['progress']['processed']}/{status['progress']['total_keys']})")
            
            if status['status'] in ['completed', 'failed']:
                return status
                
            time.sleep(poll_interval)
        
        raise TimeoutError(f"Job {job_id} não completou dentro do timeout de {timeout}s")
    
    def download_invoices(self, invoice_keys: List[str], save_directory: str = "./downloads") -> List[str]:
        """
        Método conveniente para baixar XMLs de forma completa
        
        Args:
            invoice_keys: Lista de chaves de notas fiscais
            save_directory: Diretório para salvar os arquivos
            
        Returns:
            Lista de caminhos dos arquivos baixados
        """
        # Criar diretório se não existir
        os.makedirs(save_directory, exist_ok=True)
        
        print(f"Criando job para {len(invoice_keys)} chaves...")
        job = self.create_job(invoice_keys)
        job_id = job['job_id']
        
        print(f"Job criado: {job_id}")
        print("Aguardando conclusão...")
        
        # Aguardar conclusão
        final_status = self.wait_for_completion(job_id)
        
        if final_status['status'] == 'failed':
            print("Job falhou!")
            if final_status.get('errors'):
                for error in final_status['errors']:
                    print(f"Erro para chave {error['invoice_key']}: {error['error']}")
            return []
        
        print(f"Job concluído! {final_status['progress']['successful']} arquivos baixados com sucesso")
        
        # Listar e baixar arquivos
        files_info = self.list_job_files(job_id)
        downloaded_files = []
        
        for file_info in files_info['files']:
            print(f"Baixando {file_info['filename']} ({file_info['size']} bytes)...")
            
            file_path = self.download_file(job_id, file_info['filename'], save_directory)
            downloaded_files.append(file_path)
            
            print(f"Salvo em: {file_path}")
        
        return downloaded_files

def main():
    """Exemplo de uso do cliente da API"""
    
    # Inicializar cliente
    client = XMLDownloaderAPIClient("http://localhost:5000")
    
    # Verificar se a API está funcionando
    print("Verificando status da API...")
    health = client.health_check()
    print(f"API Status: {health['status']} (v{health['version']})")
    
    # Testar conexão do sistema
    print("\nTestando conexão do sistema de automação...")
    try:
        test_result = client.test_connection()
        print(f"Teste de conexão: {test_result['status']}")
    except Exception as e:
        print(f"Erro no teste de conexão: {e}")
    
    # Chaves de exemplo (substitua pelas suas chaves reais)
    invoice_keys = [
        "35250162954987000130550020001854371034511150"
        # Adicione mais chaves aqui
    ]
    
    print(f"\nIniciando download de {len(invoice_keys)} XML(s)...")
    
    try:
        # Baixar XMLs
        downloaded_files = client.download_invoices(invoice_keys, "./xmls_baixados")
        
        print(f"\nDownload concluído! {len(downloaded_files)} arquivo(s) baixado(s):")
        for file_path in downloaded_files:
            print(f"  - {file_path}")
            
    except Exception as e:
        print(f"Erro durante o download: {e}")
    
    # Listar jobs recentes
    print("\nListando jobs recentes...")
    try:
        jobs = client.list_jobs(limit=5)
        print(f"Total de jobs: {jobs['total']}")
        
        for job in jobs['jobs']:
            print(f"  Job {job['job_id'][:8]}... - {job['status']} "
                  f"({job['successful']}/{job['total_keys']} sucessos)")
            
    except Exception as e:
        print(f"Erro ao listar jobs: {e}")

if __name__ == "__main__":
    main()