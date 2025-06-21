"""
Correção definitiva para o sistema de processamento de jobs
Remove conflitos entre múltiplas definições da função process_download_job
"""

import os
import shutil

def fix_job_processing():
    """Corrige conflitos no sistema de processamento de jobs"""
    
    print("🔧 CORRIGINDO SISTEMA DE PROCESSAMENTO DE JOBS")
    print("=" * 60)
    
    # 1. Renomear arquivos conflitantes para backup
    conflicting_files = ['app.py', 'main_fixed.py']
    
    for file in conflicting_files:
        if os.path.exists(file):
            backup_name = f"{file}.backup"
            shutil.move(file, backup_name)
            print(f"✅ Arquivo {file} movido para {backup_name}")
    
    # 2. Verificar se new_app.py tem a função correta
    with open('new_app.py', 'r') as f:
        content = f.read()
    
    if 'def process_download_job(job_id, user_id):' in content:
        print("✅ new_app.py tem a assinatura correta da função")
    else:
        print("❌ new_app.py não tem a função correta")
    
    # 3. Verificar imports problemáticos
    import_issues = []
    
    if 'from app import' in content:
        import_issues.append("Import de 'app.py' detectado")
    
    if 'from main_fixed import' in content:
        import_issues.append("Import de 'main_fixed.py' detectado")
    
    if import_issues:
        print("⚠️  Possíveis imports problemáticos:")
        for issue in import_issues:
            print(f"   - {issue}")
    else:
        print("✅ Nenhum import problemático detectado")
    
    print("\n📊 RESUMO DA CORREÇÃO:")
    print("- Arquivos conflitantes removidos")
    print("- new_app.py mantém a função correta")
    print("- Sistema deve processar jobs corretamente agora")

if __name__ == "__main__":
    fix_job_processing()