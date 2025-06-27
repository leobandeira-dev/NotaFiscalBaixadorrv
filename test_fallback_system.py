#!/usr/bin/env python3
"""
Teste do sistema de fallback usando consultadanfe.com.br
"""

import time
import logging
from fallback_automation import FallbackDownloader

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_fallback_system():
    """Testar sistema de fallback completo"""
    invoice_key = "42250485179240000239550020004175491355349509"
    
    logger.info("=== Teste do Sistema de Fallback ===")
    logger.info(f"Testando com chave: {invoice_key}")
    
    downloader = FallbackDownloader()
    
    try:
        # Primeiro testar conectividade
        logger.info("1. Testando conectividade do site de fallback...")
        connection_result = downloader.test_fallback_connection()
        logger.info(f"Conectividade: {connection_result}")
        
        if not connection_result['success']:
            logger.error("Site de fallback não acessível")
            return connection_result
        
        # Testar download XML
        logger.info("2. Testando download XML via fallback...")
        result = downloader.download_xml_fallback(invoice_key, "fallback_test")
        
        logger.info(f"Resultado final: {result}")
        
        if result['success']:
            logger.info("✅ FALLBACK FUNCIONANDO!")
            logger.info(f"Tamanho do XML: {result.get('file_size', 'N/A')} bytes")
            logger.info(f"Fonte: {result.get('source', 'N/A')}")
        else:
            logger.error("❌ Fallback falhou")
            logger.error(f"Erro: {result.get('error', 'Erro desconhecido')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Erro no teste de fallback: {e}")
        return {'success': False, 'error': str(e)}

def test_integrated_fallback():
    """Testar fallback integrado na automação principal"""
    from automation_fixed import InvoiceDownloader
    
    invoice_key = "42250485179240000239550020004175491355349509"
    
    logger.info("=== Teste de Fallback Integrado ===")
    logger.info(f"Testando com chave: {invoice_key}")
    
    downloader = InvoiceDownloader()
    
    try:
        # Testar diretamente o método de fallback
        result = downloader.try_fallback_download(invoice_key, "integrated_test")
        
        logger.info(f"Resultado do fallback integrado: {result}")
        
        if result['success']:
            logger.info("✅ FALLBACK INTEGRADO FUNCIONANDO!")
            logger.info(f"Marcado como fallback: {result.get('fallback_used', False)}")
        else:
            logger.error("❌ Fallback integrado falhou")
        
        return result
        
    except Exception as e:
        logger.error(f"Erro no teste de fallback integrado: {e}")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    print("Iniciando testes do sistema de fallback...\n")
    
    # Teste 1: Sistema de fallback isolado
    result1 = test_fallback_system()
    print(f"\nResultado do teste isolado: {result1.get('success', False)}")
    
    # Teste 2: Fallback integrado
    result2 = test_integrated_fallback()
    print(f"\nResultado do teste integrado: {result2.get('success', False)}")
    
    # Resumo
    print("\n" + "="*50)
    print("RESUMO DOS TESTES")
    print("="*50)
    print(f"Fallback isolado: {'✅ PASSOU' if result1.get('success') else '❌ FALHOU'}")
    print(f"Fallback integrado: {'✅ PASSOU' if result2.get('success') else '❌ FALHOU'}")
    
    if result1.get('success') or result2.get('success'):
        print("\n🎉 Sistema de fallback operacional!")
    else:
        print("\n⚠️  Sistema de fallback precisa de ajustes")