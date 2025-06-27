#!/usr/bin/env python3
"""
Simulação forçada do sistema de fallback consultardanfe.com
Testa diretamente o fallback sem tentar o sistema principal
"""

import logging
from consultardanfe_updated import ConsultarDanfeFallback

# Configurar logging detalhado
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')

def test_fallback_direct():
    """Testar fallback consultardanfe.com diretamente"""
    print("🔄 SIMULAÇÃO DIRETA DO SISTEMA FALLBACK")
    print("=====================================")
    
    # Chave de teste fornecida pelo usuário
    test_key = "35250513516247000107550010000113401146202508"
    job_id = "fallback_simulation_001"
    user_id = 1
    
    print(f"🔑 Chave: {test_key}")
    print(f"📋 Job ID: {job_id}")
    print(f"🏢 Sistema: consultardanfe.com (FALLBACK)")
    print()
    
    fallback = ConsultarDanfeFallback()
    
    try:
        print("🚀 INICIANDO DOWNLOAD VIA SISTEMA FALLBACK...")
        print("=" * 50)
        
        result = fallback.download_invoice_xml(
            invoice_key=test_key,
            job_id=job_id,
            user_id=user_id
        )
        
        print("\n" + "=" * 50)
        print("📊 RESULTADO DA SIMULAÇÃO:")
        print("=" * 50)
        
        if result['success']:
            print("✅ SUCESSO NO FALLBACK!")
            print(f"📁 Arquivo: {result.get('filename', 'N/A')}")
            print(f"🎯 Sistema: consultardanfe.com")
            print(f"📦 Tamanho: {result.get('size', 'N/A')} bytes")
            print(f"💬 Mensagem: {result.get('message', 'N/A')}")
        else:
            print("❌ FALHA NO FALLBACK!")
            print(f"⚠️  Erro: {result.get('error', 'Erro desconhecido')}")
            print(f"💬 Mensagem: {result.get('message', 'N/A')}")
            print(f"🔧 Detalhes: {result.get('details', 'N/A')}")
        
        print("\n" + "=" * 50)
        
        return result
        
    except Exception as e:
        print(f"❌ ERRO NA SIMULAÇÃO: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        print("🧹 Limpando recursos...")
        try:
            fallback.cleanup()
        except:
            pass

if __name__ == "__main__":
    test_fallback_direct()