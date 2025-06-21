"""
Teste de Velocidade Ultra-Rápida
Compara performance antes e depois das otimizações
"""

import time
import logging
from automation_fixed import InvoiceDownloader
from ultra_speed_optimizer import UltraSpeedOptimizer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_ultra_speed_performance():
    """Testa a performance do sistema ultra-rápido"""
    
    # Chave de teste real
    test_invoice_key = "42250485179240000239550020004175301719974747"
    job_id = "test-ultra-speed"
    
    logger.info("🚀 INICIANDO TESTE DE VELOCIDADE ULTRA-RÁPIDA")
    logger.info("=" * 60)
    
    try:
        # Instanciar downloader com otimizações
        downloader = InvoiceDownloader()
        
        # Medir tempo total de execução
        start_time = time.time()
        
        logger.info(f"⚡ Testando chave: {test_invoice_key}")
        logger.info(f"⚡ Job ID: {job_id}")
        logger.info(f"⚡ Configurações Ultra-Speed aplicadas")
        
        # Executar download com otimizações
        result = downloader.download_invoice_xml(
            invoice_key=test_invoice_key,
            job_id=job_id,
            user_id=7  # Usuário de teste
        )
        
        # Calcular tempo total
        total_time = time.time() - start_time
        
        logger.info("=" * 60)
        logger.info("📊 RESULTADOS DO TESTE ULTRA-RÁPIDO:")
        logger.info(f"⏱️  Tempo total: {total_time:.2f} segundos")
        logger.info(f"✅ Sucesso: {result.get('success', False)}")
        
        if result.get('success'):
            logger.info(f"📁 Arquivo: {result.get('file_path', 'N/A')}")
            
            # Análise de performance
            if total_time < 3:
                logger.info("🚀 PERFORMANCE ULTRA-RÁPIDA! (< 3s)")
            elif total_time < 5:
                logger.info("⚡ PERFORMANCE RÁPIDA (3-5s)")
            elif total_time < 8:
                logger.info("🏃 Performance Aceitável (5-8s)")
            else:
                logger.info("🐌 Performance Lenta (> 8s)")
                
        else:
            logger.error(f"❌ Erro: {result.get('error', 'Unknown error')}")
        
        # Comparação com benchmarks anteriores
        logger.info("=" * 60)
        logger.info("📈 COMPARAÇÃO COM VERSÕES ANTERIORES:")
        logger.info("⚖️  Versão anterior: ~5.5s (baseline)")
        logger.info(f"🚀 Versão ultra-rápida: {total_time:.2f}s")
        
        if total_time < 5.5:
            improvement = ((5.5 - total_time) / 5.5) * 100
            logger.info(f"🎯 Melhoria: {improvement:.1f}% mais rápido!")
        else:
            regression = ((total_time - 5.5) / 5.5) * 100
            logger.info(f"⚠️  Regressão: {regression:.1f}% mais lento")
            
        return {
            'success': result.get('success', False),
            'total_time': total_time,
            'performance_category': 'ultra' if total_time < 3 else 'fast' if total_time < 5 else 'acceptable' if total_time < 8 else 'slow'
        }
        
    except Exception as e:
        logger.error(f"❌ Erro durante teste: {e}")
        return {
            'success': False,
            'error': str(e),
            'total_time': 0
        }
    
    finally:
        # Cleanup
        try:
            downloader.cleanup()
        except:
            pass

def test_timeout_configurations():
    """Testa as configurações de timeout ultra-rápidas"""
    
    logger.info("🔧 TESTANDO CONFIGURAÇÕES ULTRA-RÁPIDAS:")
    
    # Timeouts ultra-rápidos
    ultra_timeouts = UltraSpeedOptimizer.get_ultra_timeouts()
    
    logger.info("⚡ Timeouts Ultra-Rápidos:")
    for key, value in ultra_timeouts.items():
        logger.info(f"   {key}: {value}s")
    
    # Verificar se são significativamente menores
    baseline_timeouts = {
        'page_load': 8,
        'element_wait': 3,
        'xml_button': 2,
        'download_poll': 0.5,
        'max_attempts': 20
    }
    
    logger.info("📊 Comparação de Timeouts:")
    total_improvement = 0
    
    for key in ultra_timeouts:
        if key in baseline_timeouts:
            baseline = baseline_timeouts[key]
            ultra = ultra_timeouts[key]
            if baseline > 0:
                improvement = ((baseline - ultra) / baseline) * 100
                total_improvement += improvement
                logger.info(f"   {key}: {improvement:.1f}% mais rápido")
    
    avg_improvement = total_improvement / len([k for k in ultra_timeouts if k in baseline_timeouts])
    logger.info(f"🎯 Melhoria média de timeouts: {avg_improvement:.1f}%")
    
    return ultra_timeouts

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 TESTE DE PERFORMANCE ULTRA-RÁPIDA")
    print("="*60)
    
    # Testar configurações
    timeouts = test_timeout_configurations()
    
    print("\n" + "-"*60)
    
    # Testar performance real
    results = test_ultra_speed_performance()
    
    print("\n" + "="*60)
    print("🏁 TESTE CONCLUÍDO")
    print("="*60)