"""
Teste da otimização de velocidade
Compara tempo de execução entre versão original e otimizada
"""

import time
import logging
from automation_speed_optimized import SpeedOptimizedInvoiceDownloader
from automation_fixed import InvoiceDownloader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_speed_comparison():
    """Compara velocidade entre versões"""
    
    test_key = "35250513516247000107550010000113401146202508"
    job_id = "speed_test_001"
    
    print("="*60)
    print("TESTE DE OTIMIZAÇÃO DE VELOCIDADE")
    print("="*60)
    
    # Teste 1: Versão Speed-Optimized
    print("\n1. TESTANDO VERSÃO SPEED-OPTIMIZED...")
    start_time = time.time()
    
    try:
        speed_downloader = SpeedOptimizedInvoiceDownloader()
        result_speed = speed_downloader.download_invoice_xml(test_key, job_id + "_speed")
        speed_time = time.time() - start_time
        
        print(f"✓ Tempo Speed-Optimized: {speed_time:.1f} segundos")
        print(f"✓ Resultado: {result_speed.get('success', False)}")
        
        speed_downloader.cleanup()
        
    except Exception as e:
        speed_time = time.time() - start_time
        print(f"✗ Erro Speed-Optimized: {e}")
        print(f"✗ Tempo até erro: {speed_time:.1f} segundos")
    
    # Aguardar entre testes
    time.sleep(3)
    
    # Teste 2: Versão Original (para comparação)
    print("\n2. TESTANDO VERSÃO ORIGINAL...")
    start_time = time.time()
    
    try:
        original_downloader = InvoiceDownloader()
        result_original = original_downloader.download_invoice_xml(test_key, job_id + "_original")
        original_time = time.time() - start_time
        
        print(f"✓ Tempo Original: {original_time:.1f} segundos")
        print(f"✓ Resultado: {result_original.get('success', False)}")
        
        original_downloader.cleanup()
        
    except Exception as e:
        original_time = time.time() - start_time
        print(f"✗ Erro Original: {e}")
        print(f"✗ Tempo até erro: {original_time:.1f} segundos")
    
    # Comparação
    print("\n" + "="*60)
    print("COMPARAÇÃO DE RESULTADOS")
    print("="*60)
    
    if 'speed_time' in locals() and 'original_time' in locals():
        improvement = original_time - speed_time
        percentage = (improvement / original_time) * 100
        
        print(f"Speed-Optimized: {speed_time:.1f}s")
        print(f"Original:       {original_time:.1f}s")
        print(f"Melhoria:       {improvement:.1f}s ({percentage:.1f}%)")
        
        if improvement > 0:
            print("✓ OTIMIZAÇÃO FUNCIONOU!")
        else:
            print("✗ Otimização não trouxe benefício")
    else:
        print("⚠ Não foi possível comparar devido a erros")

if __name__ == "__main__":
    test_speed_comparison()