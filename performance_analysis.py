"""
Análise de Performance: Desenvolvimento vs Deploy
Identifica diferenças específicas que afetam a velocidade de download
"""
import os
import time
import logging
import subprocess
from optimization_deploy import DeployOptimizer

logger = logging.getLogger(__name__)

class PerformanceAnalyzer:
    """Analisa diferenças de performance entre ambientes"""
    
    @staticmethod
    def analyze_environment():
        """Análise completa do ambiente atual"""
        is_deploy = DeployOptimizer.is_deploy_environment()
        
        analysis = {
            'environment': 'DEPLOY' if is_deploy else 'DESENVOLVIMENTO',
            'system_resources': PerformanceAnalyzer._get_system_resources(),
            'network_latency': PerformanceAnalyzer._measure_network_latency(),
            'chrome_config': PerformanceAnalyzer._get_chrome_config(),
            'timeouts': DeployOptimizer.get_optimized_timeouts(),
            'recommendations': []
        }
        
        # Análise específica para deploy
        if is_deploy:
            analysis['deploy_issues'] = PerformanceAnalyzer._analyze_deploy_issues()
            analysis['recommendations'].extend(PerformanceAnalyzer._get_deploy_recommendations())
        
        return analysis
    
    @staticmethod
    def _get_system_resources():
        """Obtém informações dos recursos do sistema usando comandos nativos"""
        try:
            resources = {}
            
            # CPU info via /proc/cpuinfo
            try:
                with open('/proc/cpuinfo', 'r') as f:
                    cpu_lines = f.readlines()
                resources['cpu_count'] = len([line for line in cpu_lines if line.startswith('processor')])
            except:
                resources['cpu_count'] = 'unknown'
            
            # Memory info via /proc/meminfo
            try:
                with open('/proc/meminfo', 'r') as f:
                    meminfo = f.read()
                    
                for line in meminfo.split('\n'):
                    if 'MemTotal:' in line:
                        total_kb = int(line.split()[1])
                        resources['memory_total_gb'] = round(total_kb / (1024**2), 2)
                    elif 'MemAvailable:' in line:
                        available_kb = int(line.split()[1])
                        resources['memory_available_gb'] = round(available_kb / (1024**2), 2)
                
                if 'memory_total_gb' in resources and 'memory_available_gb' in resources:
                    used_gb = resources['memory_total_gb'] - resources['memory_available_gb']
                    resources['memory_percent'] = round((used_gb / resources['memory_total_gb']) * 100, 1)
            except:
                resources['memory_info'] = 'unavailable'
            
            # Disk usage via df command
            try:
                result = subprocess.run(['df', '/'], capture_output=True, text=True)
                if result.returncode == 0:
                    lines = result.stdout.strip().split('\n')
                    if len(lines) > 1:
                        parts = lines[1].split()
                        if len(parts) >= 5:
                            resources['disk_usage_percent'] = int(parts[4].rstrip('%'))
            except:
                resources['disk_usage_percent'] = 'unknown'
            
            return resources
        except Exception as e:
            return {'error': str(e)}
    
    @staticmethod
    def _measure_network_latency():
        """Mede latência para o site de destino"""
        import subprocess
        try:
            # Ping para meudanfe.com.br
            result = subprocess.run(['ping', '-c', '3', 'meudanfe.com.br'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                # Extrai tempo médio do ping
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'avg' in line or 'rtt' in line:
                        # Procura padrão como "min/avg/max" 
                        parts = line.split('=')
                        if len(parts) > 1:
                            times = parts[1].strip().split('/')
                            if len(times) >= 2:
                                return {'avg_ms': float(times[1]), 'status': 'success'}
                
                return {'status': 'success', 'note': 'ping successful but could not parse time'}
            else:
                return {'status': 'failed', 'error': result.stderr}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    @staticmethod
    def _get_chrome_config():
        """Obtém configuração atual do Chrome"""
        chrome_options = DeployOptimizer.get_optimized_chrome_options()
        
        # Converte argumentos para lista legível
        args = []
        for i in range(len(chrome_options.arguments)):
            args.append(chrome_options.arguments[i])
        
        return {
            'total_arguments': len(args),
            'key_optimizations': [arg for arg in args if any(key in arg for key in 
                ['window-size', 'memory', 'single-process', 'headless', 'disable'])],
            'window_size': next((arg for arg in args if 'window-size' in arg), 'not set')
        }
    
    @staticmethod
    def _analyze_deploy_issues():
        """Analisa problemas específicos do ambiente deploy"""
        issues = []
        
        # Verifica se está em container/ambiente limitado
        if os.path.exists('/.dockerenv'):
            issues.append("Executando em container Docker")
        
        if 'runner' in os.getcwd():
            issues.append("Ambiente Replit com recursos compartilhados")
        
        # Verifica variáveis de ambiente que indicam limitações
        if os.environ.get('REPLIT_DEPLOYMENT'):
            issues.append("Ambiente deploy Replit com limitações de recursos")
        
        # Verifica tempo de resposta do sistema
        try:
            start_time = time.time()
            subprocess.run(['echo', 'test'], capture_output=True, timeout=5)
            response_time = time.time() - start_time
            if response_time > 0.1:
                issues.append(f"Sistema com resposta lenta: {response_time:.3f}s para comando simples")
        except:
            issues.append("Sistema com problemas de execução de comandos")
        
        return issues
    
    @staticmethod
    def _get_deploy_recommendations():
        """Recomendações específicas para otimizar deploy"""
        return [
            "Aumentar timeouts para compensar latência de rede",
            "Usar window-size menor para reduzir uso de memória",
            "Implementar retry mais agressivo para falhas de rede",
            "Considerar cache de sessões do Chrome",
            "Monitorar uso de memória durante downloads"
        ]
    
    @staticmethod
    def log_performance_analysis():
        """Executa análise completa e faz log dos resultados"""
        analysis = PerformanceAnalyzer.analyze_environment()
        
        logger.info("="*60)
        logger.info("ANÁLISE DE PERFORMANCE")
        logger.info("="*60)
        
        logger.info(f"🎯 Ambiente: {analysis['environment']}")
        
        # Log recursos do sistema
        resources = analysis['system_resources']
        if 'error' not in resources:
            logger.info(f"💾 Recursos: {resources['cpu_count']} CPUs, {resources['memory_available_gb']}GB RAM disponível ({resources['memory_percent']}% em uso)")
        
        # Log latência de rede
        latency = analysis['network_latency']
        if latency['status'] == 'success' and 'avg_ms' in latency:
            logger.info(f"🌐 Latência de rede: {latency['avg_ms']}ms para meudanfe.com.br")
        else:
            logger.info(f"🌐 Latência de rede: {latency}")
        
        # Log configuração Chrome
        chrome = analysis['chrome_config']
        logger.info(f"🔧 Chrome: {chrome['total_arguments']} argumentos, janela {chrome['window_size']}")
        
        # Log timeouts
        timeouts = analysis['timeouts']
        logger.info(f"⏱️  Timeouts: element_wait={timeouts['element_wait']}s, xml_button={timeouts['xml_button']}s, poll={timeouts['download_poll']}s")
        
        # Log problemas específicos do deploy
        if analysis['environment'] == 'DEPLOY' and 'deploy_issues' in analysis:
            if analysis['deploy_issues']:
                logger.info("⚠️  Problemas identificados:")
                for issue in analysis['deploy_issues']:
                    logger.info(f"   - {issue}")
            else:
                logger.info("✅ Nenhum problema crítico identificado")
        
        # Log recomendações
        if analysis['recommendations']:
            logger.info("💡 Recomendações:")
            for rec in analysis['recommendations']:
                logger.info(f"   - {rec}")
        
        logger.info("="*60)
        
        return analysis

# Função de conveniência para usar nos logs
def log_performance_analysis():
    """Wrapper para facilitar o uso"""
    return PerformanceAnalyzer.log_performance_analysis()