#!/usr/bin/env python3
"""
Teste de download real usando a chave fornecida
Simula um usuário fazendo download através do sistema principal
"""

import requests
import time
import json

def test_real_download():
    """Testa download real da chave fornecida"""
    
    # Chave fornecida pelo usuário
    invoice_key = "35250513516247000107550010000113401146202508"
    
    print(f"=== TESTE DE DOWNLOAD REAL ===")
    print(f"Chave da NF: {invoice_key}")
    print(f"Sistema: CROSS XML Downloader PRO\n")
    
    try:
        # 1. Testar conexão básica com o sistema
        print("1. Testando conexão com o sistema...")
        base_url = "http://localhost:5000"
        
        response = requests.get(f"{base_url}/", timeout=10)
        if response.status_code == 200:
            print("✓ Sistema CROSS XML está online")
        else:
            print(f"❌ Sistema não está respondendo: {response.status_code}")
            return False
            
        # 2. Fazer login ou verificar se sistema permite acesso direto
        print("\n2. Verificando acesso ao sistema...")
        
        # Tentar acessar página de download direto (se autenticação permitir)
        response = requests.get(f"{base_url}/dashboard", timeout=10)
        if response.status_code == 200:
            print("✓ Acesso direto ao dashboard disponível")
        else:
            print("⚠ Requer autenticação - usando simulação de download")
            
        # 3. Simular processo de download através da automação
        print(f"\n3. Iniciando download da NF {invoice_key}...")
        
        # Usar diretamente o sistema de automação
        from automation_fixed import InvoiceDownloader
        
        downloader = InvoiceDownloader()
        job_id = f"test_{int(time.time())}"
        user_id = 1  # Usuário de teste
        
        print(f"Job ID: {job_id}")
        print("Executando download via sistema principal...")
        
        # Tentar download principal
        result = downloader.download_invoice_xml(
            invoice_key=invoice_key,
            job_id=job_id,
            download_type='xml',
            user_id=user_id
        )
        
        print(f"Resultado do download principal: {result.get('success', False)}")
        
        if not result.get('success'):
            print("⚠ Sistema principal falhou, tentando fallback...")
            
            # Usar sistema de fallback
            fallback_result = downloader.try_fallback_download(
                invoice_key=invoice_key,
                job_id=job_id,
                user_id=user_id
            )
            
            print(f"Resultado do fallback: {fallback_result.get('success', False)}")
            
            if fallback_result.get('success'):
                print("✓ Download concluído via sistema de fallback!")
                print(f"Arquivo salvo: {fallback_result.get('filename', 'N/A')}")
                print(f"Tamanho: {fallback_result.get('file_size', 'N/A')} bytes")
                
                # Verificar se arquivo foi criado
                import os
                expected_file = f"downloads/{invoice_key}.xml"
                if os.path.exists(expected_file):
                    file_size = os.path.getsize(expected_file)
                    print(f"✓ Arquivo confirmado no disco: {file_size} bytes")
                    
                    # Ler primeiras linhas do XML
                    with open(expected_file, 'r', encoding='utf-8') as f:
                        first_lines = f.read(200)
                        if '<?xml' in first_lines and 'NFe' in first_lines:
                            print("✓ Conteúdo XML válido confirmado")
                        else:
                            print("⚠ Conteúdo pode não ser XML válido")
                            
                else:
                    print("❌ Arquivo não encontrado no disco")
                    
            else:
                print("❌ Ambos os sistemas falharam")
                print(f"Erro: {fallback_result.get('error', 'Desconhecido')}")
                
        else:
            print("✓ Download concluído via sistema principal!")
            print(f"Arquivo salvo: {result.get('filename', 'N/A')}")
            
        print(f"\n=== RESULTADO FINAL ===")
        
        if result.get('success') or (fallback_result and fallback_result.get('success')):
            print("🎉 DOWNLOAD REALIZADO COM SUCESSO!")
            print("📄 XML da nota fiscal baixado e processado")
            print("💾 Arquivo disponível para uso")
            return True
        else:
            print("❌ DOWNLOAD FALHOU")
            print("🔧 Sistema pode estar indisponível temporariamente")
            return False
            
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_real_download()
    exit(0 if success else 1)