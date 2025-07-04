#!/usr/bin/env python3
"""
Teste da automação corrigida
Testa se as correções para o novo layout funcionam
"""
import logging
import time
from automation_fixed import InvoiceDownloader

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_corrected_automation():
    """Teste da automação corrigida com novo layout"""
    downloader = None
    try:
        logger.info("Iniciando teste da automação corrigida...")
        
        # Criar instância do downloader
        downloader = InvoiceDownloader()
        
        # Chave de teste
        invoice_key = "35250513516247000107550010000113401146202508"
        job_id = "test-corrected-automation"
        
        logger.info(f"Testando download da chave: {invoice_key}")
        
        # Testar download
        result = downloader.download_invoice_xml(
            invoice_key=invoice_key,
            job_id=job_id,
            download_type='xml',
            user_id=1  # Admin user
        )
        
        logger.info(f"Resultado do teste: {result}")
        
        if result['success']:
            logger.info("✅ TESTE APROVADO - Automação funcionando corretamente")
        else:
            logger.error(f"❌ TESTE FALHOU - {result.get('error', 'Erro desconhecido')}")
            
        return result
        
    except Exception as e:
        logger.error(f"❌ ERRO NO TESTE: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {'success': False, 'error': str(e)}
    finally:
        if downloader:
            downloader.cleanup()

if __name__ == "__main__":
    test_corrected_automation()