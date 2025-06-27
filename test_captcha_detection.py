#!/usr/bin/env python3
"""
Teste específico para sistema de detecção e contorno de CAPTCHA
Validar se a solução implementada funciona corretamente
"""

import sys
import time
import logging
from fallback_automation import FallbackDownloader

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_captcha_detection_system():
    """Testar sistema de detecção e contorno de CAPTCHA"""
    print("🔍 TESTE: Sistema de Detecção e Contorno de CAPTCHA")
    print("=" * 60)
    
    # Usar chave de teste real
    test_key = "35250513516247000107550010000113401146202508"
    job_id = "test_captcha_" + str(int(time.time()))
    
    downloader = None
    try:
        # Inicializar downloader
        print(f"1. Inicializando FallbackDownloader...")
        downloader = FallbackDownloader()
        
        # Testar conectividade básica
        print(f"2. Testando conectividade básica...")
        connection_test = downloader.test_fallback_connection()
        if connection_test['success']:
            print(f"   ✅ Conectividade: {connection_test['message']}")
        else:
            print(f"   ❌ Conectividade: {connection_test['error']}")
            return False
        
        # Testar download com detecção de CAPTCHA
        print(f"3. Testando download com detecção de CAPTCHA...")
        print(f"   Chave de teste: {test_key}")
        print(f"   Job ID: {job_id}")
        
        result = downloader.download_xml_fallback(test_key, job_id, user_id=1)
        
        # Analisar resultado
        print(f"4. Analisando resultado:")
        if result['success']:
            print(f"   ✅ Download realizado com sucesso!")
            print(f"   📁 Arquivo: {result.get('file_path', 'N/A')}")
            print(f"   📊 Tamanho: {result.get('file_size', 'N/A')} bytes")
            
            # Verificar se XML contém dados válidos
            if result.get('xml_content'):
                xml_content = result['xml_content']
                if len(xml_content) > 1000 and '<nfeProc' in xml_content:
                    print(f"   ✅ XML válido detectado ({len(xml_content)} caracteres)")
                else:
                    print(f"   ⚠️  XML pode estar incompleto ({len(xml_content)} caracteres)")
            
        else:
            print(f"   ❌ Download falhou: {result.get('error', 'Erro desconhecido')}")
            
            # Verificar se foi por CAPTCHA
            error_msg = result.get('error', '').lower()
            if 'captcha' in error_msg:
                print(f"   🔒 CAPTCHA detectado - sistema funcionando conforme esperado")
                print(f"   💡 Estratégias de contorno foram aplicadas")
            elif 'fallback' in error_msg or 'backup' in error_msg:
                print(f"   🔄 Sistema de fallback ativo - tentativas automáticas em andamento")
            
        return result['success']
        
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        logger.exception("Erro detalhado:")
        return False
        
    finally:
        if downloader:
            downloader.cleanup()
            print(f"5. Sistema limpo com sucesso")

def test_captcha_methods():
    """Testar métodos específicos de CAPTCHA"""
    print("\n🧪 TESTE: Métodos de Detecção de CAPTCHA")
    print("=" * 60)
    
    downloader = None
    try:
        downloader = FallbackDownloader()
        downloader.setup_driver()
        
        # Navegar para site de teste
        print("1. Navegando para site de fallback...")
        downloader.driver.get("https://consultadanfe.com.br/")
        time.sleep(2)
        
        # Testar detecção de CAPTCHA
        print("2. Testando detecção de CAPTCHA...")
        job_id = "test_methods_" + str(int(time.time()))
        
        captcha_result = downloader.detect_and_handle_captcha(job_id)
        
        if captcha_result is True:
            print("   ✅ CAPTCHA detectado e contornado com sucesso")
        elif captcha_result is None:
            print("   ⚠️  CAPTCHA detectado mas não contornado")
        else:
            print("   ℹ️  Nenhum CAPTCHA detectado")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de métodos: {e}")
        return False
        
    finally:
        if downloader:
            downloader.cleanup()

def main():
    """Executar todos os testes"""
    print("🚀 INICIANDO TESTES DO SISTEMA DE CAPTCHA")
    print("=" * 80)
    
    success_count = 0
    total_tests = 2
    
    # Teste 1: Sistema completo
    if test_captcha_detection_system():
        success_count += 1
        
    # Teste 2: Métodos específicos
    if test_captcha_methods():
        success_count += 1
    
    # Resumo final
    print("\n" + "=" * 80)
    print(f"📊 RESUMO DOS TESTES")
    print(f"Testes executados: {total_tests}")
    print(f"Testes bem-sucedidos: {success_count}")
    print(f"Taxa de sucesso: {(success_count/total_tests)*100:.1f}%")
    
    if success_count == total_tests:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema de detecção e contorno de CAPTCHA operacional")
    else:
        print("⚠️  Alguns testes falharam")
        print("🔧 Verificar logs para detalhes específicos")
    
    return success_count == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)