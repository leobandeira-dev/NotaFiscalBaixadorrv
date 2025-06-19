#!/usr/bin/env python3
"""
Teste real do sistema de download com a chave fornecida pelo usuário
"""
import sys
import os
sys.path.append('.')

from automation_fixed import InvoiceDownloader
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_real_download():
    """Teste real com a chave 35250513516247000107550010000113401146202508"""
    invoice_key = "35250513516247000107550010000113401146202508"
    job_id = "test-job-real"
    
    logger.info(f"Iniciando teste real com chave: {invoice_key}")
    
    # Criar diretório downloads se não existir
    os.makedirs('downloads', exist_ok=True)
    
    downloader = None
    try:
        # Inicializar downloader
        downloader = InvoiceDownloader()
        
        # Executar download
        result = downloader.download_invoice_xml(invoice_key, job_id, 'xml')
        
        logger.info(f"Resultado do download: {result}")
        
        if result.get('success'):
            logger.info("✅ DOWNLOAD REALIZADO COM SUCESSO!")
            if 'file_path' in result:
                file_path = result['file_path']
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    logger.info(f"📁 Arquivo salvo: {file_path}")
                    logger.info(f"📊 Tamanho: {file_size} bytes")
                    
                    # Verificar conteúdo
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        if len(content) > 100 and 'nfe' in content.lower():
                            logger.info("✅ XML válido confirmado")
                            return {
                                'success': True,
                                'file_path': file_path,
                                'file_size': file_size,
                                'xml_valid': True
                            }
                        else:
                            logger.error("❌ XML inválido ou vazio")
                            return {
                                'success': False,
                                'error': 'XML inválido'
                            }
                else:
                    logger.error(f"❌ Arquivo não encontrado: {file_path}")
                    return {
                        'success': False,
                        'error': 'Arquivo não encontrado'
                    }
            else:
                logger.error("❌ file_path não retornado")
                return {
                    'success': False,
                    'error': 'file_path não retornado'
                }
        else:
            logger.error(f"❌ DOWNLOAD FALHOU: {result.get('error', 'Erro desconhecido')}")
            return result
            
    except Exception as e:
        logger.error(f"❌ ERRO NO TESTE: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
    finally:
        if downloader:
            try:
                downloader.cleanup()
            except:
                pass

if __name__ == "__main__":
    result = test_real_download()
    print(f"\n🎯 RESULTADO FINAL: {result}")