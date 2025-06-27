#!/usr/bin/env python3
"""
Teste do sistema simplificado (apenas meudanfe.com.br)
"""
import logging
from simple_meudanfe_system import SimpleMeuDanfeDownloader

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_simple_system():
    """Testar sistema simplificado"""
    print("🧪 TESTE SISTEMA SIMPLIFICADO - meudanfe.com.br APENAS")
    print("=" * 60)
    
    downloader = SimpleMeuDanfeDownloader()
    
    try:
        # Chave de teste conhecida
        test_key = "35250513516247000107550010000113401146202508"
        job_id = "simple_test_001"
        user_id = 1  # Usuário de teste
        
        print(f"🔑 Testando chave: {test_key}")
        print(f"📋 Job ID: {job_id}")
        print(f"👤 User ID: {user_id}")
        
        result = downloader.download_invoice_xml(
            invoice_key=test_key,
            job_id=job_id,
            download_type='xml',
            user_id=user_id
        )
        
        print(f"\n📊 RESULTADO:")
        print(f"   Sucesso: {result.get('success', False)}")
        print(f"   Erro: {result.get('error', 'N/A')}")
        print(f"   Tempo: {result.get('elapsed_time', 0):.2f}s")
        
        if result.get('file_path'):
            print(f"   Arquivo: {result.get('file_path')}")
            
        return result.get('success', False)
        
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        return False
        
    finally:
        downloader.cleanup()

if __name__ == "__main__":
    success = test_simple_system()
    print("\n" + "=" * 60)
    if success:
        print("🎯 Resultado: TESTE BEM-SUCEDIDO")
    else:
        print("💥 Resultado: TESTE FALHOU")