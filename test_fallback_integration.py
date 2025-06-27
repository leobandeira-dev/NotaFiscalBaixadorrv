#!/usr/bin/env python3
"""
Teste do sistema integrado com fallback consultardanfe.com
Testa meudanfe.com (principal) → consultardanfe.com (fallback)
"""

import logging
from automation_fixed import InvoiceDownloader

# Configurar logging
logging.basicConfig(level=logging.INFO)

def test_integrated_fallback():
    """Testar sistema integrado com fallback"""
    print("🧪 TESTE SISTEMA INTEGRADO COM FALLBACK")
    print("========================================")
    
    # Chave de teste
    test_key = "35250513516247000107550010000113401146202508"
    job_id = "fallback_test_001"
    user_id = 1
    
    print(f"🔑 Testando chave: {test_key}")
    print(f"📋 Job ID: {job_id}")
    print(f"👤 User ID: {user_id}")
    print()
    
    downloader = InvoiceDownloader()
    
    try:
        print("🚀 INICIANDO DOWNLOAD COM SISTEMA PRINCIPAL + FALLBACK...")
        print("=" * 60)
        
        result = downloader.download_invoice_xml(
            invoice_key=test_key,
            job_id=job_id,
            user_id=user_id
        )
        
        print("\n" + "=" * 60)
        print("📊 RESULTADO FINAL:")
        print("=" * 60)
        
        if result['success']:
            print("✅ SUCESSO!")
            print(f"📁 Arquivo: {result.get('filename', 'N/A')}")
            print(f"🎯 Sistema usado: {result.get('source', 'meudanfe')}")
            print(f"🔄 Fallback usado: {'Sim' if result.get('fallback_used', False) else 'Não'}")
            print(f"💬 Mensagem: {result.get('message', 'N/A')}")
        else:
            print("❌ FALHA!")
            print(f"⚠️  Erro: {result.get('error', 'Erro desconhecido')}")
            print(f"💬 Mensagem: {result.get('message', 'N/A')}")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ ERRO NO TESTE: {str(e)}")
    
    finally:
        try:
            downloader.cleanup()
        except:
            pass

if __name__ == "__main__":
    test_integrated_fallback()