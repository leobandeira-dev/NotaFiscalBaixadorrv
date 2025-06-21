"""
Debug script para identificar por que os jobs estão falhando
"""

import requests
import json
import time
from datetime import datetime

def debug_job_failures():
    """Investiga falhas nos jobs de download"""
    
    print("🔍 INVESTIGANDO FALHAS NOS JOBS DE DOWNLOAD")
    print("=" * 60)
    
    session = requests.Session()
    
    # Login
    login_data = {'email': 'joao@crossxml.com.br', 'password': 'soeusei'}
    login_response = session.post('https://crossxml.com.br/login', data=login_data)
    
    if login_response.status_code != 200:
        print("❌ Falha no login")
        return
    
    print("✅ Login realizado com sucesso")
    
    # 1. Testar com uma única chave válida conhecida
    print("\n1. Testando com chave válida única...")
    single_key = '35250513516247000107550010000113401146202508'
    
    submit_data = {'invoice_keys': single_key}
    submit_response = session.post('https://crossxml.com.br/submit_keys', data=submit_data)
    
    if 'download' in submit_response.url:
        job_id = submit_response.url.split('/')[-1]
        print(f"Job criado: {job_id}")
        
        # Monitorar este job
        for i in range(30):
            status_response = session.get(f'https://crossxml.com.br/job_status/{job_id}')
            if status_response.status_code == 200:
                try:
                    status_data = status_response.json()
                    status = status_data.get('status')
                    processed = status_data.get('processed', 0)
                    total = status_data.get('total_keys', 0)
                    successful = status_data.get('successful', 0)
                    failed = status_data.get('failed', 0)
                    
                    print(f"  Ciclo {i+1}: {status} - {processed}/{total} (✅{successful} ❌{failed})")
                    
                    # Mostrar erros se existirem
                    if status_data.get('errors'):
                        print(f"  ERROS: {status_data['errors']}")
                    
                    if status in ['completed', 'failed']:
                        print(f"\n📊 RESULTADO FINAL - Job {job_id}:")
                        print(f"   Status: {status}")
                        print(f"   Processados: {processed}/{total}")
                        print(f"   Sucessos: {successful}")
                        print(f"   Falhas: {failed}")
                        
                        if status_data.get('errors'):
                            print("   Erros encontrados:")
                            for error in status_data['errors']:
                                print(f"     - {error}")
                        
                        if status_data.get('files'):
                            print(f"   Arquivos: {status_data['files']}")
                        
                        break
                except json.JSONDecodeError:
                    print(f"  Ciclo {i+1}: Resposta não é JSON válida")
            else:
                print(f"  Ciclo {i+1}: HTTP {status_response.status_code}")
            
            time.sleep(2)
    
    # 2. Testar conectividade do sistema de automação
    print("\n2. Testando conectividade do sistema...")
    test_response = session.get('https://crossxml.com.br/test_automation')
    
    if test_response.status_code == 200:
        try:
            test_data = test_response.json()
            print(f"   Teste de conectividade: {test_data.get('status')}")
            print(f"   Detalhes: {test_data.get('message')}")
        except:
            print("   Resposta não é JSON")
    else:
        print(f"   Erro no teste: HTTP {test_response.status_code}")
    
    # 3. Verificar health da aplicação
    print("\n3. Verificando saúde da aplicação...")
    health_response = session.get('https://crossxml.com.br/health')
    
    if health_response.status_code == 200:
        health_data = health_response.json()
        print(f"   Status: {health_data.get('status')}")
        print(f"   Versão: {health_data.get('version')}")
        print(f"   Timestamp: {health_data.get('timestamp')}")
    else:
        print(f"   Erro no health check: HTTP {health_response.status_code}")
    
    # 4. Verificar se há jobs recentes com falhas
    print("\n4. Verificando jobs recentes...")
    try:
        # Tentar acessar lista de jobs via API
        jobs_response = session.get('https://crossxml.com.br/api/v1/jobs?limit=10')
        if jobs_response.status_code == 200:
            jobs_data = jobs_response.json()
            recent_jobs = jobs_data.get('jobs', [])
            
            print(f"   Encontrados {len(recent_jobs)} jobs recentes")
            
            for job in recent_jobs[:5]:  # Mostrar apenas os 5 mais recentes
                job_status = job.get('status', 'unknown')
                job_id = job.get('job_id', 'unknown')
                total = job.get('total_keys', 0)
                successful = job.get('successful', 0)
                failed = job.get('failed', 0)
                
                print(f"   Job {job_id[:8]}...: {job_status} ({successful}✅ {failed}❌ de {total})")
        else:
            print(f"   Não foi possível acessar lista de jobs: HTTP {jobs_response.status_code}")
    except Exception as e:
        print(f"   Erro ao verificar jobs: {e}")

if __name__ == "__main__":
    debug_job_failures()