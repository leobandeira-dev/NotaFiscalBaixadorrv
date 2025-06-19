#!/usr/bin/env python3
"""
Teste direto do sistema de download com chave real
"""
import requests
import time
import json

def test_direct_download():
    """Teste direto com chave real confirmada"""
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    print("Testando sistema de download direto")
    
    # 1. Registrar e fazer login
    register_data = {
        'username': 'testuser_direct',
        'email': 'test_direct@example.com',
        'password': 'testpass123',
        'confirm_password': 'testpass123'
    }
    
    session.post(f"{base_url}/register", data=register_data)
    
    login_data = {
        'email': 'test_direct@example.com',
        'password': 'testpass123'
    }
    
    login_response = session.post(f"{base_url}/login", data=login_data)
    print(f"Login status: {login_response.status_code}")
    
    # 2. Testar download com chave real (REAL SINALIZACAO - 4750 bytes)
    invoice_key = "35250513516247000107550010000113401146202508"
    
    download_data = {
        'invoice_keys': invoice_key
    }
    
    print(f"Enviando chave: {invoice_key}")
    response = session.post(f"{base_url}/submit_keys", data=download_data, allow_redirects=False)
    
    print(f"Response status: {response.status_code}")
    print(f"Headers: {dict(response.headers)}")
    
    if response.status_code == 302:
        location = response.headers.get("Location", "")
        print(f"Redirect para: {location}")
        
        if "/download/" in location:
            job_id = location.split("/download/")[-1]
            print(f"Job ID extraído: {job_id}")
            
            # 3. Monitorar job
            for i in range(20):
                try:
                    status_response = session.get(f"{base_url}/job_status/{job_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        print(f"Tentativa {i+1}: {status_data['status']} - {status_data['processed']}/{status_data['total_keys']}")
                        
                        if status_data['status'] == 'completed':
                            print(f"SUCESSO! Arquivos: {status_data['files']}")
                            return True
                        elif status_data['status'] == 'failed':
                            print(f"FALHA: {status_data.get('errors', [])}")
                            return False
                    else:
                        print(f"Erro status: {status_response.status_code}")
                        
                except Exception as e:
                    print(f"Erro consulta: {e}")
                
                time.sleep(3)
            
            print("Timeout")
            return False
    
    print("Erro no redirecionamento")
    return False

if __name__ == "__main__":
    success = test_direct_download()
    print(f"\nResultado: {'SUCESSO' if success else 'FALHA'}")