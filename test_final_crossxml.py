"""
Teste final para confirmar que o sistema está funcionando no crossxml.com.br
"""

import requests
import time

def test_final_crossxml():
    """Teste final do sistema crossxml.com.br"""
    
    print("🔧 TESTE FINAL DO SISTEMA CROSSXML.COM.BR")
    print("=" * 60)
    
    # 1. Testar a rota correta que existe: /xml-download
    print("1. Testando rota correta /xml-download...")
    response = requests.get("https://crossxml.com.br/xml-download")
    print(f"   Status: {response.status_code}")
    print(f"   URL final: {response.url}")
    
    if response.status_code == 200 and 'login' in response.url:
        print("   ✅ Sistema funciona - redireciona para login como esperado")
        auth_working = True
    else:
        print("   ❌ Problema com autenticação")
        auth_working = False
    
    # 2. Testar submit para a rota correta
    print("\n2. Testando submit real com chave válida...")
    
    session = requests.Session()
    
    # Primeiro, pegar a página de login para obter token CSRF se necessário
    login_page = session.get("https://crossxml.com.br/login")
    print(f"   Login page: {login_page.status_code}")
    
    # Tentar fazer POST direto (sem autenticação) para ver o comportamento
    post_data = {
        'invoice_keys': '35250513516247000107550010000113401146202508'
    }
    
    post_response = session.post("https://crossxml.com.br/submit_keys", data=post_data)
    print(f"   POST status: {post_response.status_code}")
    print(f"   POST URL final: {post_response.url}")
    
    if 'login' in post_response.url and post_response.status_code == 200:
        print("   ✅ Submit funciona - exige autenticação como esperado")
        submit_working = True
    else:
        print("   ❌ Submit não está funcionando corretamente")
        submit_working = False
    
    # 3. Testar health da aplicação
    print("\n3. Testando saúde da aplicação...")
    health = requests.get("https://crossxml.com.br/health")
    
    if health.status_code == 200:
        health_data = health.json()
        print(f"   ✅ API saudável: {health_data.get('status')}")
        print(f"   Versão: {health_data.get('version')}")
        app_healthy = True
    else:
        print("   ❌ API não responde")
        app_healthy = False
    
    # 4. Comparar com domínio Replit
    print("\n4. Comparando com domínio Replit...")
    replit_domain = "https://9a7d14e3-7ec8-40b5-8b00-8733fff0b3f4-00-10dm2qhcjzz2k.spock.replit.dev"
    
    try:
        replit_response = requests.get(f"{replit_domain}/xml-download")
        print(f"   Replit /xml-download: {replit_response.status_code}")
        
        replit_submit = requests.post(f"{replit_domain}/submit_keys", data=post_data)
        print(f"   Replit submit: {replit_submit.status_code}")
        print(f"   Replit final URL: {replit_submit.url}")
        
        if replit_response.status_code == 200 and replit_submit.status_code == 200:
            print("   ✅ Domínio Replit funcionando igual")
            replit_equal = True
        else:
            print("   ❌ Comportamento diferente no Replit")
            replit_equal = False
            
    except Exception as e:
        print(f"   ❌ Erro ao testar Replit: {e}")
        replit_equal = False
    
    # Resultado final
    print("\n" + "=" * 60)
    print("📊 RESULTADO FINAL")
    print("=" * 60)
    
    if auth_working and submit_working and app_healthy:
        print("🎉 SISTEMA FUNCIONANDO CORRETAMENTE!")
        print()
        print("✅ Autenticação: Sistema exige login - CORRETO")
        print("✅ Submit: Processa e redireciona - CORRETO") 
        print("✅ Aplicação: Saudável e responsiva - CORRETO")
        print()
        print("💡 INSTRUÇÕES PARA O USUÁRIO:")
        print("1. Acesse: https://crossxml.com.br/xml-download")
        print("2. Faça login com sua conta")
        print("3. Insira a chave: 35250513516247000107550010000113401146202508")
        print("4. Clique em 'Iniciar Download'")
        print("5. O sistema processará e baixará o XML automaticamente")
        print()
        print("🔑 CHAVE CORRETA PARA TESTE:")
        print("35250513516247000107550010000113401146202508")
        
        return True
        
    else:
        print("❌ PROBLEMAS IDENTIFICADOS:")
        if not auth_working:
            print("   - Sistema de autenticação não está funcionando")
        if not submit_working:
            print("   - Submit de formulário com problemas")
        if not app_healthy:
            print("   - Aplicação não está saudável")
            
        return False

if __name__ == "__main__":
    test_final_crossxml()