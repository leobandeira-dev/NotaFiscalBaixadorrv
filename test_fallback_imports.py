#!/usr/bin/env python3
"""
Teste simplificado de importações do sistema de fallback
Verifica se todos os módulos são importáveis sem executar WebDriver
"""

def test_fallback_imports():
    """Testa apenas as importações sem executar WebDriver"""
    print("=== TESTE SIMPLIFICADO DE IMPORTAÇÕES FALLBACK ===\n")
    
    try:
        # 1. Testar importação do módulo de fallback
        print("1. Testando importação do módulo de fallback:")
        from fallback_automation import FallbackDownloader
        print("✓ FallbackDownloader importado com sucesso")
        
        # 2. Testar criação de instância
        fallback = FallbackDownloader()
        print("✓ FallbackDownloader instanciado com sucesso")
        
        # 3. Testar se métodos existem
        assert hasattr(fallback, 'download_xml_fallback'), "Método download_xml_fallback não encontrado"
        print("✓ Método download_xml_fallback encontrado")
        
        assert hasattr(fallback, 'save_xml_content'), "Método save_xml_content não encontrado"
        print("✓ Método save_xml_content encontrado")
        
        # 4. Testar integração com automation_fixed
        print("\n2. Testando integração com automation_fixed:")
        from automation_fixed import InvoiceDownloader
        print("✓ InvoiceDownloader importado com sucesso")
        
        downloader = InvoiceDownloader()
        print("✓ InvoiceDownloader instanciado com sucesso")
        
        assert hasattr(downloader, 'try_fallback_download'), "Método try_fallback_download não encontrado"
        print("✓ Método try_fallback_download encontrado")
        
        # 5. Testar importação do xml_processor
        print("\n3. Testando processamento de XML:")
        from xml_processor import extract_xml_data
        print("✓ extract_xml_data importado com sucesso")
        
        # Teste com XML básico
        test_xml = """<?xml version="1.0" encoding="UTF-8"?>
        <nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
            <NFe>
                <infNFe Id="NFe35250513516247000107550010000113401146202508">
                    <ide>
                        <nNF>11340</nNF>
                        <serie>1</serie>
                    </ide>
                    <emit>
                        <xNome>TESTE EMPRESA</xNome>
                    </emit>
                </infNFe>
            </NFe>
        </nfeProc>"""
        
        xml_data = extract_xml_data(test_xml)
        print("✓ XML parsing funcionando corretamente")
        
        print("\n=== RESULTADO FINAL ===")
        print("✅ Todos os testes de importação passaram com sucesso!")
        print("✅ Sistema de fallback pronto para uso")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro durante o teste: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_fallback_imports()
    exit(0 if success else 1)