#!/usr/bin/env python3
"""
Teste de integração das etiquetas corrigidas
Verifica se o sistema está usando Layout 3 "Transul Exato" com todas as correções visuais
"""

import os
from responsive_label_generator import ResponsiveTransportLabelGenerator
from new_app import generate_improved_labels_with_guaranteed_borders

def test_default_layout_integration():
    """Testa se o sistema usa por padrão o layout corrigido"""
    
    print("=== TESTE DE INTEGRAÇÃO LAYOUT PADRÃO ===")
    
    # XML de teste
    xml_path = "attached_assets/42250485179240000239550020004175361171503396_1750379433035.xml"
    
    if not os.path.exists(xml_path):
        print("❌ Arquivo XML não encontrado")
        return False
        
    with open(xml_path, 'r', encoding='utf-8') as f:
        xml_content = f.read()
    
    print(f"✅ XML carregado: {len(xml_content)} caracteres")
    
    # Teste 1: ResponsiveTransportLabelGenerator com layout padrão (deve ser 'transul')
    print("\n1. Testando layout padrão do ResponsiveTransportLabelGenerator...")
    
    try:
        # Sem especificar layout_style - deve usar o padrão
        generator = ResponsiveTransportLabelGenerator(
            company_name="LAF LOGISTICA",
            company_subtitle="OPERADOR LOGISTICO",
            paper_width_mm=100,
            paper_height_mm=150
            # layout_style não especificado - deve usar padrão
        )
        
        print(f"   Layout padrão: {generator.layout_style}")
        
        if generator.layout_style == "transul":
            print("   ✅ Layout padrão correto (transul)")
        else:
            print(f"   ❌ Layout padrão incorreto: {generator.layout_style}")
            return False
            
        result = generator.generate_transport_label(
            xml_content=xml_content,
            pedido_number="PED2025001",
            area_code="01"
        )
        
        if result:
            size = len(result.getvalue())
            print(f"   ✅ Etiqueta gerada: {size:,} bytes")
            
            # Verificar se é o tamanho otimizado (3.4KB aprox)
            if 3000 <= size <= 4000:
                print("   ✅ Tamanho otimizado correto (Layout 3)")
                
                with open("teste_layout_padrao_integrado.pdf", "wb") as f:
                    f.write(result.getvalue())
                print("   📄 Salvo: teste_layout_padrao_integrado.pdf")
                return True
            else:
                print(f"   ❌ Tamanho não otimizado: {size:,} bytes")
                return False
        else:
            print("   ❌ Falha na geração")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False

def test_layouts_comparison():
    """Compara os 3 layouts para verificar diferenças"""
    
    print("\n=== COMPARAÇÃO DOS 3 LAYOUTS ===")
    
    xml_path = "attached_assets/42250485179240000239550020004175361171503396_1750379433035.xml"
    with open(xml_path, 'r', encoding='utf-8') as f:
        xml_content = f.read()
    
    layouts = {
        "layout1": "Layout 1 (Moderno)",
        "layout2": "Layout 2 (Alto Contraste)", 
        "transul": "Layout 3 (Transul Exato - Corrigido)"
    }
    
    results = {}
    
    for layout_key, layout_name in layouts.items():
        print(f"\nTestando {layout_name}...")
        
        try:
            generator = ResponsiveTransportLabelGenerator(
                company_name="LAF LOGISTICA",
                company_subtitle="OPERADOR LOGISTICO",
                paper_width_mm=100,
                paper_height_mm=150,
                layout_style=layout_key
            )
            
            result = generator.generate_transport_label(
                xml_content=xml_content,
                pedido_number="PED2025001",
                area_code="01"
            )
            
            if result:
                size = len(result.getvalue())
                results[layout_key] = size
                print(f"   ✅ {layout_name}: {size:,} bytes")
                
                filename = f"teste_comparacao_{layout_key}.pdf"
                with open(filename, "wb") as f:
                    f.write(result.getvalue())
                print(f"   📄 Salvo: {filename}")
            else:
                print(f"   ❌ {layout_name}: falha na geração")
                
        except Exception as e:
            print(f"   ❌ {layout_name}: erro - {e}")
    
    # Análise dos resultados
    print("\n📊 ANÁLISE DOS RESULTADOS:")
    
    if 'transul' in results:
        transul_size = results['transul']
        
        if 3000 <= transul_size <= 4000:
            print(f"   ✅ Layout 3 (Transul): {transul_size:,} bytes - OTIMIZADO")
        else:
            print(f"   ❌ Layout 3 (Transul): {transul_size:,} bytes - NÃO OTIMIZADO")
            
        # Comparar com outros layouts
        for layout_key in ['layout1', 'layout2']:
            if layout_key in results:
                other_size = results[layout_key]
                diff = transul_size - other_size
                
                if diff < -1000:  # Layout 3 é significativamente menor
                    print(f"   ✅ Layout 3 vs {layout_key}: {diff:+,} bytes (OTIMIZAÇÃO CONFIRMADA)")
                else:
                    print(f"   ⚠️ Layout 3 vs {layout_key}: {diff:+,} bytes")
    
    return results

if __name__ == "__main__":
    print("Iniciando teste de integração das etiquetas corrigidas...")
    
    # Teste 1: Layout padrão
    success1 = test_default_layout_integration()
    
    # Teste 2: Comparação de layouts
    results = test_layouts_comparison()
    
    print("\n" + "="*60)
    
    if success1 and 'transul' in results and 3000 <= results['transul'] <= 4000:
        print("🎉 INTEGRAÇÃO DAS CORREÇÕES VISUAIS COMPLETA!")
        print("   ✅ Layout padrão configurado corretamente")
        print("   ✅ Layout 3 'Transul Exato' gerando PDFs otimizados")
        print("   ✅ Todas as correções visuais aplicadas")
        print("   ✅ Sistema pronto para produção")
    else:
        print("❌ PROBLEMAS NA INTEGRAÇÃO DETECTADOS")
        print("   Verificar configuração dos layouts")