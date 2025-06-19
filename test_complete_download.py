#!/usr/bin/env python3
"""
Teste completo do sistema de download com interface funcional
"""
import requests
import time
import json

def test_complete_system():
    """Teste completo do sistema - criação de usuário, login e download"""
    base_url = "http://localhost:5000"
    session = requests.Session()
    
    print("🔧 Iniciando teste completo do sistema de download")
    
    # 1. Registrar usuário de teste
    print("👤 Registrando usuário de teste...")
    register_data = {
        'username': 'testuser_real',
        'email': 'test_real@example.com',
        'password': 'testpass123',
        'confirm_password': 'testpass123'
    }
    
    response = session.post(f"{base_url}/register", data=register_data)
    if response.status_code == 200:
        print("✅ Usuário registrado com sucesso")
    else:
        print("❌ Erro no registro, tentando login direto...")
    
    # 2. Fazer login
    print("🔐 Fazendo login...")
    login_data = {
        'email': 'test_real@example.com',
        'password': 'testpass123'
    }
    
    response = session.post(f"{base_url}/login", data=login_data)
    if "dashboard" in response.url or response.status_code == 200:
        print("✅ Login realizado com sucesso")
    else:
        print("❌ Erro no login")
        return False
    
    # 3. Iniciar download com chave real
    print("📥 Iniciando download com chave real...")
    invoice_key = "35250513516247000107550010000113401146202508"
    
    download_data = {
        'invoice_keys': invoice_key
    }
    
    response = session.post(f"{base_url}/submit_keys", data=download_data, allow_redirects=False)
    
    if response.status_code == 302 and "Location" in response.headers:
        # Extrair job_id da URL de redirecionamento
        location = response.headers["Location"]
        if "/download/" in location:
            job_id = location.split("/download/")[-1]
            print(f"✅ Job criado com sucesso: {job_id}")
        else:
            print(f"❌ Redirecionamento inesperado: {location}")
            return False
    else:
        print(f"❌ Erro na resposta: {response.status_code}")
        return False
        
        # 4. Monitorar progresso
        print("⏳ Monitorando progresso do download...")
        for attempt in range(30):  # 30 tentativas, 2 segundos cada = 1 minuto
            try:
                status_response = session.get(f"{base_url}/job_status/{job_id}")
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"📊 Status: {status_data['status']} - {status_data['processed']}/{status_data['total_keys']} ({status_data['progress_percentage']:.1f}%)")
                    
                    if status_data['status'] == 'completed':
                        print(f"🎉 Download concluído! {status_data['successful']} arquivos baixados")
                        
                        # Verificar se há arquivos baixados
                        if status_data['files']:
                            print(f"📁 Arquivos baixados: {', '.join(status_data['files'])}")
                            
                            # Testar download individual
                            first_file = status_data['files'][0]
                            download_response = session.get(f"{base_url}/download/{job_id}/{first_file}")
                            
                            if download_response.status_code == 200:
                                print(f"✅ Download individual testado com sucesso: {len(download_response.content)} bytes")
                            else:
                                print(f"❌ Erro no download individual: {download_response.status_code}")
                        
                        return True
                    elif status_data['status'] == 'failed':
                        print(f"❌ Download falhou: {status_data.get('errors', [])}")
                        return False
                else:
                    print(f"❌ Erro ao consultar status: {status_response.status_code}")
                    
            except Exception as e:
                print(f"⚠️ Erro na consulta de status: {str(e)}")
            
            time.sleep(2)
        
        print("⏰ Timeout aguardando conclusão do download")
        return False
    
    if 'job_id' not in locals():
        print("❌ Job não foi criado corretamente")
        return False

if __name__ == "__main__":
    success = test_complete_system()
    print(f"\n🎯 Resultado final: {'SUCESSO' if success else 'FALHA'}")