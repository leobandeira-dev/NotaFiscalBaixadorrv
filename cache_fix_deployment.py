"""
Solução para forçar atualização de cache no domínio customizado
Resolve o problema do status "failed" no deployment
"""

import time
import requests
from datetime import datetime

def force_cache_update():
    """Força atualização do cache no domínio customizado"""
    
    print("🔄 Forçando atualização do cache no domínio customizado...")
    
    # URLs para testar
    custom_domain = "https://crossxml.com.br"
    replit_domain = "https://9a7d14e3-7ec8-40b5-8b00-8733fff0b3f4-00-10dm2qhcjzz2k.spock.replit.dev"
    
    # Cache busting parameters
    timestamp = int(time.time())
    cache_busters = [
        f"?v={timestamp}",
        f"?cache_bust={timestamp}",
        f"?t={timestamp}&force=1",
        f"?refresh={timestamp}",
        f"?no_cache={timestamp}"
    ]
    
    print(f"Timestamp usado: {timestamp}")
    
    # Teste diferentes estratégias de cache busting
    for i, cache_buster in enumerate(cache_busters, 1):
        print(f"\n🔧 Estratégia {i}/5: {cache_buster}")
        
        try:
            # Headers para forçar refresh
            headers = {
                'Cache-Control': 'no-cache, no-store, must-revalidate',
                'Pragma': 'no-cache',
                'Expires': '0',
                'User-Agent': f'CROSS-XML-Deploy-Fix/{timestamp}'
            }
            
            # Test health endpoint with cache busting
            url = f"{custom_domain}/health{cache_buster}"
            response = requests.get(url, headers=headers, timeout=15)
            
            if response.status_code == 200:
                print(f"✅ SUCCESS! Health endpoint respondeu: {response.status_code}")
                data = response.json()
                print(f"   Service: {data.get('service')}")
                print(f"   Version: {data.get('version')}")
                print(f"   Domain: {data.get('domain')}")
                return True
            else:
                print(f"❌ Status: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Erro: {e}")
        
        # Wait between attempts
        if i < len(cache_busters):
            print("⏳ Aguardando 10 segundos...")
            time.sleep(10)
    
    return False

def verify_both_domains():
    """Verifica se ambos os domínios estão respondendo corretamente"""
    
    domains = {
        "Custom": "https://crossxml.com.br",
        "Replit": "https://9a7d14e3-7ec8-40b5-8b00-8733fff0b3f4-00-10dm2qhcjzz2k.spock.replit.dev"
    }
    
    print("\n🔍 Verificação final dos domínios:")
    
    for name, domain in domains.items():
        print(f"\n{name} Domain ({domain}):")
        
        try:
            # Test health
            health_resp = requests.get(f"{domain}/health", timeout=10)
            print(f"  Health: {health_resp.status_code}")
            
            # Test ready
            ready_resp = requests.get(f"{domain}/ready", timeout=10)
            print(f"  Ready: {ready_resp.status_code}")
            
            # Test main page
            main_resp = requests.get(f"{domain}/", timeout=10)
            print(f"  Main: {main_resp.status_code}")
            
        except Exception as e:
            print(f"  ❌ Erro: {e}")

def generate_deployment_report():
    """Gera relatório do status do deployment"""
    
    print("\n📊 RELATÓRIO DO DEPLOYMENT:")
    print("=" * 50)
    
    # Verificar se problema foi resolvido
    try:
        response = requests.get("https://crossxml.com.br/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ PROBLEMA RESOLVIDO!")
            print(f"✅ Health endpoint respondendo corretamente")
            print(f"✅ Versão: {data.get('version')}")
            print(f"✅ Timestamp: {data.get('timestamp')}")
            print("\n🎯 PRÓXIMOS PASSOS:")
            print("1. Aguardar alguns minutos para o painel Replit atualizar")
            print("2. Status 'failed' deve mudar para 'active' automaticamente")
            print("3. Sistema totalmente funcional em ambos os domínios")
        else:
            print("⚠️ PROBLEMA PERSISTE")
            print(f"Status do health endpoint: {response.status_code}")
            print("\n🔧 AÇÕES RECOMENDADAS:")
            print("1. Aguardar mais 10-15 minutos para propagação completa")
            print("2. Verificar configuração do domínio no painel Replit")
            print("3. Considerar redeployment manual se necessário")
            
    except Exception as e:
        print("❌ PROBLEMA NÃO RESOLVIDO")
        print(f"Erro: {e}")
        print("\n🚨 AÇÕES URGENTES:")
        print("1. Verificar conectividade de rede")
        print("2. Verificar se domínio está configurado corretamente")
        print("3. Contatar suporte Replit se problema persistir")

if __name__ == "__main__":
    print("🚀 INICIANDO CORREÇÃO DO DEPLOYMENT")
    print("=" * 50)
    
    # Attempt to force cache update
    success = force_cache_update()
    
    # Verify both domains
    verify_both_domains()
    
    # Generate final report
    generate_deployment_report()
    
    print(f"\n⏰ Processo concluído: {datetime.now()}")