#!/usr/bin/env python3
"""
Teste do sistema de fallback corrigido
"""

import sys
import os
sys.path.append('.')

def test_fallback_system():
    """Testar sistema de fallback com chave específica"""
    try:
        from fallback_automation import FallbackDownloader
        
        # Criar instância do downloader de fallback
        fallback = FallbackDownloader()
        
        # Chave de teste específica
        test_invoice_key = "35250513516247000107550010000113401146202508"
        test_job_id = "test_fallback_001"
        test_user_id = 9
        
        print(f"🧪 Testando fallback com chave: {test_invoice_key}")
        print(f"📋 Job ID: {test_job_id}")
        print(f"👤 User ID: {test_user_id}")
        print("="*60)
        
        # Executar download via fallback
        result = fallback.download_xml_fallback(
            invoice_key=test_invoice_key,
            job_id=test_job_id,
            user_id=test_user_id
        )
        
        print("\n📊 RESULTADO DO TESTE:")
        print("="*40)
        
        if result.get('success'):
            print("✅ Fallback funcionou com sucesso!")
            print(f"📄 Arquivo: {result.get('filename', 'N/A')}")
            print(f"📁 Caminho: {result.get('file_path', 'N/A')}")
            print(f"📏 Tamanho: {result.get('file_size', 'N/A')} bytes")
        else:
            print("❌ Fallback falhou")
            print(f"🚫 Erro: {result.get('error', 'N/A')}")
            
        print(f"⏱️  Tempo: {result.get('elapsed_time', 'N/A')} segundos")
        
        # Limpar recursos
        if hasattr(fallback, 'cleanup'):
            fallback.cleanup()
            
        return result.get('success', False)
        
    except Exception as e:
        print(f"💥 Erro no teste: {e}")
        return False

if __name__ == "__main__":
    print("🚀 TESTE SISTEMA DE FALLBACK CORRIGIDO")
    print("="*60)
    
    success = test_fallback_system()
    
    print("\n" + "="*60)
    print(f"🎯 RESULTADO FINAL: {'SUCESSO' if success else 'FALHA'}")