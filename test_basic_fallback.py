#!/usr/bin/env python3
"""
Teste básico do sistema de fallback
Verifica importações e configuração básica
"""

import sys
import os

def test_basic_imports():
    """Testa se as importações básicas funcionam"""
    try:
        from fallback_automation import FallbackDownloader
        print("✓ FallbackDownloader importado com sucesso")
        
        # Testa criação da instância
        downloader = FallbackDownloader()
        print("✓ FallbackDownloader instanciado com sucesso")
        
        # Testa método de teste de conectividade
        result = downloader.test_fallback_connection()
        print(f"✓ Teste de conectividade: {result}")
        
        return True
        
    except ImportError as e:
        print(f"✗ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"✗ Erro geral: {e}")
        return False

def test_basic_integration():
    """Testa se a integração com automation_fixed funciona"""
    try:
        from automation_fixed import InvoiceDownloader
        print("✓ InvoiceDownloader importado com sucesso")
        
        downloader = InvoiceDownloader()
        print("✓ InvoiceDownloader instanciado com sucesso")
        
        # Verifica se o método de fallback existe
        if hasattr(downloader, 'try_fallback_download'):
            print("✓ Método try_fallback_download encontrado")
            return True
        else:
            print("✗ Método try_fallback_download não encontrado")
            return False
            
    except ImportError as e:
        print(f"✗ Erro de importação: {e}")
        return False
    except Exception as e:
        print(f"✗ Erro geral: {e}")
        return False

if __name__ == "__main__":
    print("=== TESTE BÁSICO DO SISTEMA DE FALLBACK ===\n")
    
    print("1. Testando importações básicas:")
    basic_ok = test_basic_imports()
    
    print("\n2. Testando integração:")
    integration_ok = test_basic_integration()
    
    print("\n=== RESULTADO FINAL ===")
    if basic_ok and integration_ok:
        print("✓ Todos os testes básicos passaram")
        sys.exit(0)
    else:
        print("✗ Alguns testes falharam")
        sys.exit(1)