"""
Teste de Performance Real do Sistema CROSS XML
Executa download real para verificar otimizações deploy vs desenvolvimento
"""
import time
import logging
from datetime import datetime
from automation_fixed import InvoiceDownloader
from performance_solution import PerformanceSolution, DeployPerformanceMonitor
from optimization_deploy import DeployOptimizer

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_real_performance():
    """Executa teste de performance real com chave autêntica"""
    
    # Chave de nota fiscal real para teste
    test_invoice_key = "35250162954987000130550020001854371034511150"
    job_id = f"perf_test_{int(time.time())}"
    
    logger.info("="*60)
    logger.info("TESTE DE PERFORMANCE REAL - CROSS XML")
    logger.info("="*60)
    
    # 1. Detectar ambiente
    is_deploy = DeployOptimizer.is_deploy_environment()
    env_name = "DEPLOY (crossxml.com.br)" if is_deploy else "DESENVOLVIMENTO"
    logger.info(f"🎯 Ambiente detectado: {env_name}")
    
    # 2. Aplicar otimizações
    performance_result = PerformanceSolution.apply_deploy_performance_fixes()
    logger.info(f"⚡ Otimizações aplicadas: {len(performance_result['optimizations_applied'])}")
    
    # 3. Executar download com monitoramento
    start_time = time.time()
    
    try:
        downloader = InvoiceDownloader()
        logger.info(f"🚀 Iniciando download XML: {test_invoice_key}")
        
        # Download com monitoramento de performance
        result = downloader.download_invoice_xml(
            invoice_key=test_invoice_key,
            job_id=job_id,
            download_type='xml'
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Resultados do teste
        logger.info("="*60)
        logger.info("RESULTADOS DO TESTE DE PERFORMANCE")
        logger.info("="*60)
        logger.info(f"⌚ Tempo total: {duration:.2f} segundos")
        logger.info(f"✅ Status: {result.get('status', 'UNKNOWN')}")
        logger.info(f"📁 Arquivo: {result.get('filename', 'N/A')}")
        
        if result.get('status') == 'success':
            file_size = result.get('file_size', 0)
            logger.info(f"📊 Tamanho do arquivo: {file_size} bytes")
            
            # Análise de performance por ambiente
            if is_deploy:
                if duration < 15:
                    logger.info("🎉 EXCELENTE: Performance deploy otimizada funcionando!")
                elif duration < 25:
                    logger.info("✅ BOM: Performance deploy dentro do esperado")
                else:
                    logger.warning("⚠️  Performance deploy pode ser melhorada")
            else:
                if duration < 10:
                    logger.info("⚡ RÁPIDO: Performance desenvolvimento ótima")
                else:
                    logger.info("📈 Performance desenvolvimento normal")
        
        downloader.cleanup()
        
        return {
            'success': True,
            'duration': duration,
            'environment': env_name,
            'result': result,
            'optimizations': performance_result['optimizations_applied']
        }
        
    except Exception as e:
        end_time = time.time()
        duration = end_time - start_time
        
        logger.error(f"❌ Erro no teste: {str(e)}")
        logger.info(f"⌚ Tempo até erro: {duration:.2f} segundos")
        
        return {
            'success': False,
            'duration': duration,
            'environment': env_name,
            'error': str(e),
            'optimizations': performance_result['optimizations_applied']
        }

if __name__ == "__main__":
    result = test_real_performance()
    
    print("\n" + "="*60)
    print("RESUMO FINAL DO TESTE")
    print("="*60)
    print(f"Sucesso: {'SIM' if result['success'] else 'NÃO'}")
    print(f"Duração: {result['duration']:.2f}s")
    print(f"Ambiente: {result['environment']}")
    print(f"Otimizações: {len(result.get('optimizations', []))}")
    print("="*60)