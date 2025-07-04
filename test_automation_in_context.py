#!/usr/bin/env python3
"""
Teste da automação dentro do contexto Flask
"""
from new_app import app
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_automation_with_flask_context():
    """Testa automação com contexto Flask"""
    with app.app_context():
        try:
            logger.info("Testando automação corrigida...")
            
            from automation_fixed import InvoiceDownloader
            
            downloader = InvoiceDownloader()
            
            # Chave de teste
            invoice_key = "35250513516247000107550010000113401146202508"
            job_id = "test-flask-context"
            
            result = downloader.download_invoice_xml(
                invoice_key=invoice_key,
                job_id=job_id,
                download_type='xml',
                user_id=1
            )
            
            logger.info(f"Resultado: {result}")
            
            if result['success']:
                print("✅ AUTOMAÇÃO FUNCIONANDO")
            else:
                print(f"❌ ERRO: {result.get('error', 'Desconhecido')}")
                
            downloader.cleanup()
            return result
            
        except Exception as e:
            logger.error(f"Erro no teste: {e}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    test_automation_with_flask_context()