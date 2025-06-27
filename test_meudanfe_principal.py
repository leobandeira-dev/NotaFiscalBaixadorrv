#!/usr/bin/env python3
"""
Teste do sistema principal: meudanfe.com.br
"""
import logging
from automation_consultardanfe import InvoiceDownloader

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_meudanfe_principal():
    """Testar sistema principal meudanfe.com.br"""
    print("🧪 TESTE SISTEMA PRINCIPAL - meudanfe.com.br")
    print("=" * 50)
    
    downloader = InvoiceDownloader()
    
    try:
        # Chave de teste conhecida
        test_key = "35250513516247000107550010000113401146202508"
        job_id = "test_001"
        user_id = None  # Teste sem usuário
        
        print(f"🔑 Testando chave: {test_key}")
        print(f"📋 Job ID: {job_id}")
        
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
    success = test_meudanfe_principal()
    print("\n" + "=" * 50)
    if success:
        print("🎯 Resultado: TESTE BEM-SUCEDIDO")
    else:
        print("💥 Resultado: TESTE FALHOU")