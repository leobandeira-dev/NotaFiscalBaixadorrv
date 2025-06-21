"""
Debug específico para identificar por que downloads falham no crossxml.com.br
"""

import requests
import json
import time

def test_authentication_required():
    """Testa se a autenticação é obrigatória"""
    print("🔍 Testando necessidade de autenticação...")
    
    # Tentar acessar página de download sem autenticação
    response = requests.get("https://crossxml.com.br/download")
    
    print(f"Status Code: {response.status_code}")
    print(f"URL Final: {response.url}")
    
    if 'login' in response.url.lower() or response.status_code == 401:
        return True, "Redirecionado para login - autenticação obrigatória"
    
    return False, "Página acessível sem autenticação"

def test_submit_without_auth():
    """Testa submit de formulário sem autenticação"""
    print("\n🔍 Testando submit sem autenticação...")
    
    session = requests.Session()
    
    # Primeiro, obter a página
    get_response = session.get("https://crossxml.com.br/download")
    print(f"GET /download: {get_response.status_code}")
    
    # Tentar fazer POST
    post_data = {
        'invoice_keys': '35250513516247000107550010000113401146202508'
    }
    
    post_response = session.post("https://crossxml.com.br/submit_keys", data=post_data)
    print(f"POST /submit_keys: {post_response.status_code}")
    print(f"URL após POST: {post_response.url}")
    
    if 'login' in post_response.url.lower():
        return False, "Redirecionado para login ao tentar submit"
    elif 'status' in post_response.url.lower() or 'download' in post_response.url.lower():
        return True, f"Submit bem-sucedido - redirecionado para: {post_response.url}"
    else:
        return False, f"Submit não redirecionou corretamente: {post_response.url}"

def test_api_health():
    """Testa se a API está funcionando"""
    print("\n🔍 Testando saúde da API...")
    
    try:
        response = requests.get("https://crossxml.com.br/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print(f"API Health: OK")
            print(f"Versão: {data.get('version', 'N/A')}")
            print(f"Status: {data.get('status', 'N/A')}")
            return True, "API funcionando"
        else:
            return False, f"API retornou status {response.status_code}"
    except Exception as e:
        return False, f"Erro na API: {e}"

def test_comparison_with_replit_domain():
    """Compara comportamento entre domínios"""
    print("\n🔍 Comparando com domínio Replit...")
    
    replit_domain = "https://9a7d14e3-7ec8-40b5-8b00-8733fff0b3f4-00-10dm2qhcjzz2k.spock.replit.dev"
    
    # Testar acesso ao domínio Replit
    try:
        replit_response = requests.get(f"{replit_domain}/download", timeout=10)
        print(f"Replit domain /download: {replit_response.status_code}")
        print(f"Replit URL: {replit_response.url}")
        
        # Testar health no Replit
        replit_health = requests.get(f"{replit_domain}/health", timeout=10)
        if replit_health.status_code == 200:
            replit_data = replit_health.json()
            print(f"Replit Health: {replit_data.get('status', 'N/A')}")
            print(f"Replit Version: {replit_data.get('version', 'N/A')}")
        
        return True, "Domínio Replit acessível"
        
    except Exception as e:
        return False, f"Erro ao acessar Replit: {e}"

def main():
    print("=" * 60)
    print("🚨 DEBUG CROSSXML.COM.BR - PROBLEMA DE DOWNLOAD")
    print("=" * 60)
    
    # Teste 1: Autenticação
    auth_required, auth_msg = test_authentication_required()
    print(f"Autenticação obrigatória: {'SIM' if auth_required else 'NÃO'}")
    print(f"Detalhes: {auth_msg}")
    
    # Teste 2: Submit sem auth
    submit_ok, submit_msg = test_submit_without_auth()
    print(f"\nSubmit sem auth funciona: {'SIM' if submit_ok else 'NÃO'}")
    print(f"Detalhes: {submit_msg}")
    
    # Teste 3: API Health
    api_ok, api_msg = test_api_health()
    print(f"\nAPI funcionando: {'SIM' if api_ok else 'NÃO'}")
    print(f"Detalhes: {api_msg}")
    
    # Teste 4: Comparação
    replit_ok, replit_msg = test_comparison_with_replit_domain()
    print(f"\nDomínio Replit acessível: {'SIM' if replit_ok else 'NÃO'}")
    print(f"Detalhes: {replit_msg}")
    
    print("\n" + "=" * 60)
    print("💡 DIAGNÓSTICO FINAL")
    print("=" * 60)
    
    if auth_required:
        print("❌ PROBLEMA IDENTIFICADO: Sistema exige autenticação")
        print("   - O domínio crossxml.com.br está redirecionando para login")
        print("   - Usuários precisam estar logados para fazer downloads")
        print("   - Isso pode ser diferente do domínio Replit")
        print("\n🔧 SOLUÇÃO NECESSÁRIA:")
        print("   - Verificar configuração de autenticação entre domínios")
        print("   - Confirmar se middleware de segurança está ativo")
        print("   - Testar com usuário autenticado")
    elif not submit_ok:
        print("❌ PROBLEMA IDENTIFICADO: Submit não funciona")
        print("   - Formulário não processa corretamente")
        print("   - Pode ser problema de CSRF ou sessão")
        print("\n🔧 SOLUÇÃO NECESSÁRIA:")
        print("   - Verificar tokens CSRF")
        print("   - Confirmar configuração de sessões")
    elif not api_ok:
        print("❌ PROBLEMA IDENTIFICADO: API não responde")
        print("   - Sistema pode estar com problemas")
        print("\n🔧 SOLUÇÃO NECESSÁRIA:")
        print("   - Verificar logs do servidor")
        print("   - Reiniciar aplicação se necessário")
    else:
        print("✅ SISTEMA APARENTEMENTE FUNCIONANDO")
        print("   - Todos os testes básicos passaram")
        print("   - Problema pode ser específico do robô ou timing")

if __name__ == "__main__":
    main()