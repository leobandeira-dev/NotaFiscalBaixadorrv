"""
Teste específico para verificar funcionamento do robô no ambiente de deploy
"""

import logging
import time
import os
from deploy_robot_fix import DeployRobotFix
from automation_fixed import InvoiceDownloader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_deploy_robot():
    """Teste completo do robô no ambiente de deploy"""
    logger.info("🧪 Iniciando teste do robô de deploy...")
    
    # Verificar ambiente
    is_deploy = DeployRobotFix.is_deploy_environment()
    logger.info(f"🔍 Ambiente de deploy detectado: {is_deploy}")
    
    # Testar conexão básica
    logger.info("🔗 Testando conexão básica...")
    connection_ok = DeployRobotFix.test_deploy_connection()
    logger.info(f"🔗 Conexão básica: {'✅ OK' if connection_ok else '❌ FALHOU'}")
    
    # Testar download completo
    logger.info("📥 Testando download completo...")
    try:
        downloader = InvoiceDownloader()
        
        # Usar chave de teste
        test_key = "35250513516247000107550010000113401146202508"
        result = downloader.download_invoice_xml(test_key, "test-job", user_id=2)
        
        success = result.get('success', False)
        logger.info(f"📥 Download completo: {'✅ OK' if success else '❌ FALHOU'}")
        
        if success:
            logger.info(f"✅ XML baixado com sucesso: {result.get('filename')}")
        else:
            logger.error(f"❌ Erro no download: {result.get('error')}")
            
        downloader.cleanup()
        return success
        
    except Exception as e:
        logger.error(f"❌ Erro no teste: {e}")
        return False

def diagnose_deploy_issues():
    """Diagnóstico de problemas no deploy"""
    logger.info("🔧 Executando diagnóstico de deploy...")
    
    issues = []
    
    # Verificar variáveis de ambiente
    env_vars = ['REPLIT_DOMAINS', 'PORT', 'REPLIT_DEPLOYMENT']
    for var in env_vars:
        value = os.environ.get(var)
        if value:
            logger.info(f"✅ {var}: {value}")
        else:
            logger.warning(f"⚠️ {var}: Não definido")
            issues.append(f"Variável {var} não definida")
    
    # Verificar chromedriver
    chromedriver_paths = [
        '/nix/store/3qnxr5x6gw3k9a9i7d0akz0m6bksbwff-chromedriver-125.0.6422.141/bin/chromedriver',
        '/usr/bin/chromedriver',
        '/usr/local/bin/chromedriver'
    ]
    
    chromedriver_found = False
    for path in chromedriver_paths:
        if os.path.exists(path):
            logger.info(f"✅ ChromeDriver encontrado: {path}")
            chromedriver_found = True
            break
    
    if not chromedriver_found:
        logger.warning("⚠️ ChromeDriver não encontrado nos caminhos padrão")
        issues.append("ChromeDriver não encontrado")
    
    # Verificar conectividade
    try:
        import requests
        response = requests.get("https://meudanfe.com.br/", timeout=10)
        if response.status_code == 200:
            logger.info("✅ Conectividade com meudanfe.com.br: OK")
        else:
            logger.warning(f"⚠️ Conectividade com meudanfe.com.br: {response.status_code}")
            issues.append(f"Resposta HTTP {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Erro de conectividade: {e}")
        issues.append(f"Erro de conectividade: {e}")
    
    if issues:
        logger.error("❌ Problemas encontrados:")
        for issue in issues:
            logger.error(f"  - {issue}")
    else:
        logger.info("✅ Diagnóstico OK - Nenhum problema encontrado")
    
    return len(issues) == 0

if __name__ == "__main__":
    print("=" * 60)
    print("TESTE DO ROBÔ DE DEPLOY")
    print("=" * 60)
    
    # Executar diagnóstico
    diagnosis_ok = diagnose_deploy_issues()
    
    print("\n" + "=" * 60)
    print("TESTE DE FUNCIONALIDADE")
    print("=" * 60)
    
    # Executar teste
    test_ok = test_deploy_robot()
    
    print("\n" + "=" * 60)
    print("RESULTADO FINAL")
    print("=" * 60)
    
    if diagnosis_ok and test_ok:
        print("✅ ROBÔ FUNCIONANDO CORRETAMENTE NO DEPLOY")
    else:
        print("❌ ROBÔ COM PROBLEMAS NO DEPLOY")
        print("Verifique os logs acima para detalhes")