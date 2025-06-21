"""
Teste isolado para identificar por que as threads não executam process_download_job
"""

import threading
import time
import sys
import os

# Adicionar diretório atual ao path
sys.path.insert(0, os.getcwd())

def test_basic_thread():
    """Teste básico de thread"""
    print("1. Testando execução básica de thread...")
    
    def simple_function():
        print("   ✅ Thread básica executada com sucesso")
    
    thread = threading.Thread(target=simple_function)
    thread.start()
    thread.join()

def test_thread_with_app_context():
    """Teste de thread com contexto Flask"""
    print("2. Testando thread com contexto Flask...")
    
    try:
        from new_app import app
        
        def function_with_context():
            print("   📱 Entrando no contexto da aplicação...")
            with app.app_context():
                print("   ✅ Thread com contexto Flask executada com sucesso")
        
        thread = threading.Thread(target=function_with_context)
        thread.start()
        thread.join()
        
    except Exception as e:
        print(f"   ❌ Erro ao testar thread com contexto: {e}")

def test_process_download_job_import():
    """Teste de importação da função process_download_job"""
    print("3. Testando importação da função process_download_job...")
    
    try:
        from new_app import process_download_job
        print("   ✅ Função process_download_job importada com sucesso")
        print(f"   📝 Tipo da função: {type(process_download_job)}")
        print(f"   📝 Localização: {process_download_job.__module__}")
        
    except Exception as e:
        print(f"   ❌ Erro ao importar process_download_job: {e}")

def test_direct_function_call():
    """Teste de chamada direta da função"""
    print("4. Testando chamada direta da função...")
    
    try:
        from new_app import process_download_job, app
        
        # Criar um contexto de aplicação e chamar a função diretamente
        with app.app_context():
            print("   📱 Chamando process_download_job diretamente...")
            # Chamar com parâmetros de teste
            process_download_job("test-job-id", 2)
            
    except Exception as e:
        print(f"   ❌ Erro ao chamar process_download_job diretamente: {e}")
        import traceback
        print(f"   📝 Traceback: {traceback.format_exc()}")

def test_thread_with_function_call():
    """Teste de thread chamando process_download_job"""
    print("5. Testando thread chamando process_download_job...")
    
    try:
        from new_app import process_download_job
        
        def thread_function():
            print("   🧵 Thread iniciada, chamando process_download_job...")
            try:
                process_download_job("test-thread-job-id", 2)
                print("   ✅ process_download_job executada na thread com sucesso")
            except Exception as e:
                print(f"   ❌ Erro na thread: {e}")
                import traceback
                print(f"   📝 Traceback: {traceback.format_exc()}")
        
        thread = threading.Thread(target=thread_function)
        thread.start()
        thread.join(timeout=10)  # Timeout de 10 segundos
        
        if thread.is_alive():
            print("   ⚠️  Thread ainda está rodando após 10 segundos")
        else:
            print("   ✅ Thread finalizou dentro do tempo esperado")
            
    except Exception as e:
        print(f"   ❌ Erro no teste de thread: {e}")

if __name__ == "__main__":
    print("🔧 TESTE DE EXECUÇÃO DE THREADS")
    print("=" * 50)
    
    test_basic_thread()
    test_thread_with_app_context()
    test_process_download_job_import()
    test_direct_function_call()
    test_thread_with_function_call()
    
    print("\n📊 TESTE CONCLUÍDO")