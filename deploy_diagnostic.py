"""
Diagnóstico específico para problemas de performance em deploy
Identifica causas raiz das diferenças de velocidade
"""
import os
import time
import logging
import subprocess
from datetime import datetime

logger = logging.getLogger(__name__)

class DeployDiagnostic:
    """Diagnóstica problemas específicos do ambiente deploy"""
    
    @staticmethod
    def run_comprehensive_diagnostic():
        """Executa diagnóstico completo do ambiente"""
        logger.info("="*60)
        logger.info("DIAGNÓSTICO DEPLOY - PROBLEMAS DE PERFORMANCE")
        logger.info("="*60)
        
        # 1. Identificação do ambiente
        env_info = DeployDiagnostic._identify_environment()
        logger.info(f"🎯 Ambiente: {env_info['type']}")
        logger.info(f"📍 Localização: {env_info['location']}")
        
        # 2. Teste de conectividade de rede
        network_perf = DeployDiagnostic._test_network_performance()
        logger.info(f"🌐 Conectividade para meudanfe.com.br:")
        logger.info(f"   - Status: {network_perf['status']}")
        if 'latency_ms' in network_perf:
            logger.info(f"   - Latência: {network_perf['latency_ms']}ms")
            if network_perf['latency_ms'] > 150:
                logger.info("   ⚠️  PROBLEMA: Latência alta (>150ms)")
        
        # 3. Recursos do sistema
        resources = DeployDiagnostic._check_system_resources()
        logger.info(f"💾 Recursos do sistema:")
        for key, value in resources.items():
            logger.info(f"   - {key}: {value}")
        
        # 4. Performance do Chrome
        chrome_perf = DeployDiagnostic._test_chrome_performance()
        logger.info(f"🔧 Performance do Chrome:")
        logger.info(f"   - Tempo de inicialização: {chrome_perf['startup_time']:.3f}s")
        if chrome_perf['startup_time'] > 3.0:
            logger.info("   ⚠️  PROBLEMA: Chrome lento para inicializar (>3s)")
        
        # 5. Diferenças específicas deploy vs dev
        deploy_issues = DeployDiagnostic._identify_deploy_specific_issues()
        if deploy_issues:
            logger.info("⚠️  PROBLEMAS IDENTIFICADOS NO DEPLOY:")
            for issue in deploy_issues:
                logger.info(f"   - {issue}")
        
        # 6. Recomendações específicas
        recommendations = DeployDiagnostic._generate_specific_recommendations(
            network_perf, resources, chrome_perf, deploy_issues
        )
        logger.info("💡 RECOMENDAÇÕES ESPECÍFICAS:")
        for rec in recommendations:
            logger.info(f"   - {rec}")
        
        logger.info("="*60)
        
        return {
            'environment': env_info,
            'network': network_perf,
            'resources': resources,
            'chrome_performance': chrome_perf,
            'deploy_issues': deploy_issues,
            'recommendations': recommendations
        }
    
    @staticmethod
    def _identify_environment():
        """Identifica tipo e características do ambiente"""
        env_info = {
            'type': 'UNKNOWN',
            'location': os.getcwd(),
            'replit_deployment': os.environ.get('REPLIT_DEPLOYMENT', 'false'),
            'repl_id': os.environ.get('REPL_ID', 'none'),
            'hostname': os.environ.get('HOSTNAME', 'unknown')
        }
        
        if env_info['replit_deployment'] != 'false':
            env_info['type'] = 'REPLIT_DEPLOY'
        elif env_info['repl_id'] != 'none':
            env_info['type'] = 'REPLIT_DEV'
        elif 'runner' in env_info['location']:
            env_info['type'] = 'REPLIT_RUNNER'
        else:
            env_info['type'] = 'LOCAL'
        
        return env_info
    
    @staticmethod
    def _test_network_performance():
        """Testa performance específica da rede"""
        try:
            # Teste 1: Conectividade básica
            start_time = time.time()
            result = subprocess.run(
                ['curl', '-s', '-o', '/dev/null', '-w', '%{time_total}', 'https://meudanfe.com.br/'],
                capture_output=True, text=True, timeout=15
            )
            total_time = time.time() - start_time
            
            if result.returncode == 0:
                curl_time = float(result.stdout.strip())
                return {
                    'status': 'SUCCESS',
                    'latency_ms': round(curl_time * 1000, 1),
                    'total_time': round(total_time, 3)
                }
            else:
                return {
                    'status': 'FAILED',
                    'error': result.stderr,
                    'total_time': round(total_time, 3)
                }
        except Exception as e:
            return {'status': 'ERROR', 'error': str(e)}
    
    @staticmethod
    def _check_system_resources():
        """Verifica recursos específicos que afetam performance"""
        resources = {}
        
        # Espaço em disco
        try:
            result = subprocess.run(['df', '-h', '/'], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    resources['disk_space'] = f"{parts[3]} disponível de {parts[1]}"
        except:
            resources['disk_space'] = 'unknown'
        
        # Memória disponível
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if 'MemAvailable:' in line:
                        kb = int(line.split()[1])
                        mb = round(kb / 1024, 0)
                        resources['memory_available'] = f"{mb}MB"
                        break
        except:
            resources['memory_available'] = 'unknown'
        
        # Load average
        try:
            with open('/proc/loadavg', 'r') as f:
                load = f.read().strip().split()[0]
                resources['load_average'] = load
        except:
            resources['load_average'] = 'unknown'
        
        return resources
    
    @staticmethod
    def _test_chrome_performance():
        """Testa performance específica do Chrome"""
        try:
            start_time = time.time()
            
            # Simula inicialização do Chrome (sem abrir)
            result = subprocess.run([
                'which', 'google-chrome'
            ], capture_output=True, text=True, timeout=5)
            
            startup_time = time.time() - start_time
            
            return {
                'startup_time': startup_time,
                'chrome_available': result.returncode == 0
            }
        except Exception as e:
            return {
                'startup_time': 999,
                'chrome_available': False,
                'error': str(e)
            }
    
    @staticmethod
    def _identify_deploy_specific_issues():
        """Identifica problemas específicos do ambiente deploy"""
        issues = []
        
        # Verifica se está em ambiente Replit Deploy
        if os.environ.get('REPLIT_DEPLOYMENT'):
            issues.append("Ambiente Replit Deploy com recursos limitados")
        
        # Verifica limitações de memória
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if 'MemAvailable:' in line:
                        kb = int(line.split()[1])
                        mb = kb / 1024
                        if mb < 512:
                            issues.append(f"Pouca memória disponível: {mb:.0f}MB")
        except:
            pass
        
        # Verifica se há limitações de CPU
        try:
            with open('/proc/loadavg', 'r') as f:
                load = float(f.read().strip().split()[0])
                if load > 2.0:
                    issues.append(f"Sistema com alta carga: {load}")
        except:
            pass
        
        # Verifica se está em container
        if os.path.exists('/.dockerenv'):
            issues.append("Executando em container com limitações")
        
        return issues
    
    @staticmethod
    def _generate_specific_recommendations(network_perf, resources, chrome_perf, deploy_issues):
        """Gera recomendações específicas baseadas nos problemas encontrados"""
        recommendations = []
        
        # Recomendações de rede
        if 'latency_ms' in network_perf and network_perf['latency_ms'] > 150:
            recommendations.append(f"Aumentar timeouts para compensar latência de {network_perf['latency_ms']}ms")
            recommendations.append("Implementar retry mais agressivo para conexões lentas")
        
        # Recomendações de Chrome
        if chrome_perf['startup_time'] > 3.0:
            recommendations.append("Usar instância Chrome persistente em vez de criar nova a cada download")
            recommendations.append("Implementar pool de conexões Chrome")
        
        # Recomendações específicas para deploy
        if "Ambiente Replit Deploy" in str(deploy_issues):
            recommendations.append("Reduzir window-size para 400x300 no deploy")
            recommendations.append("Usar timeouts 2x maiores que desenvolvimento")
            recommendations.append("Implementar cache de elementos da página")
        
        # Recomendações de memória
        if any("memória" in issue.lower() for issue in deploy_issues):
            recommendations.append("Usar --memory-pressure-off e --max_old_space_size=1024")
            recommendations.append("Fechar Chrome imediatamente após cada download")
        
        return recommendations

# Função de conveniência
def run_deploy_diagnostic():
    """Executa diagnóstico completo"""
    return DeployDiagnostic.run_comprehensive_diagnostic()