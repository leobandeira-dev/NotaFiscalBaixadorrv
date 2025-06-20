#!/usr/bin/env python3
"""
Debug do roteamento para Layout 3 "Transul Exato"
Verifica se o sistema está corretamente direcionando para TransulExactLayoutGenerator
"""

import os
from responsive_label_generator import ResponsiveTransportLabelGenerator

def test_routing_debug():
    """Testa o roteamento específico para layout 'transul'"""
    
    print("=== DEBUG DO ROTEAMENTO LAYOUT TRANSUL ===")
    
    # XML de teste
    xml_path = "attached_assets/42250485179240000239550020004175361171503396_1750379433035.xml"
    
    if not os.path.exists(xml_path):
        print("Arquivo XML não encontrado")
        return False
        
    with open(xml_path, 'r', encoding='utf-8') as f:
        xml_content = f.read()
    
    print(f"XML carregado: {len(xml_content)} caracteres")
    
    # Teste direto do TransulExactLayoutGenerator
    print("\n1. Testando TransulExactLayoutGenerator diretamente...")
    try:
        from transul_exact_layout_generator import generate_transul_exact_label_from_xml
        
        result_direct = generate_transul_exact_label_from_xml(
            xml_content=xml_content,
            pedido_number="PED2025001",
            area_code="01",
            company_logo_path=None,
            volume_info="1/1",
            paper_width_mm=100,
            paper_height_mm=150
        )
        
        if result_direct:
            size_direct = len(result_direct.getvalue())
            print(f"   ✅ TransulExactLayoutGenerator: {size_direct:,} bytes")
            
            with open("teste_direto_transul.pdf", "wb") as f:
                f.write(result_direct.getvalue())
        else:
            print("   ❌ TransulExactLayoutGenerator falhou")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro ao importar TransulExactLayoutGenerator: {e}")
        return False
    
    # Teste através do ResponsiveTransportLabelGenerator com layout "transul"
    print("\n2. Testando ResponsiveTransportLabelGenerator com layout='transul'...")
    try:
        generator = ResponsiveTransportLabelGenerator(
            company_name="LAF LOGISTICA",
            company_subtitle="OPERADOR LOGISTICO",
            paper_width_mm=100,
            paper_height_mm=150,
            layout_style="transul"
        )
        
        print(f"   Layout style configurado: {generator.layout_style}")
        
        result_responsive = generator.generate_transport_label(
            xml_content=xml_content,
            pedido_number="PED2025001",
            area_code="01"
        )
        
        if result_responsive:
            size_responsive = len(result_responsive.getvalue())
            print(f"   ✅ ResponsiveTransportLabelGenerator: {size_responsive:,} bytes")
            
            with open("teste_responsive_transul.pdf", "wb") as f:
                f.write(result_responsive.getvalue())
                
            # Comparar tamanhos
            if abs(size_direct - size_responsive) < 100:
                print(f"   ✅ Roteamento correto! Diferença: {abs(size_direct - size_responsive)} bytes")
                return True
            else:
                print(f"   ❌ Roteamento incorreto! Diferença: {abs(size_direct - size_responsive)} bytes")
                print(f"       Direto: {size_direct}, Responsive: {size_responsive}")
                return False
        else:
            print("   ❌ ResponsiveTransportLabelGenerator falhou")
            return False
            
    except Exception as e:
        print(f"   ❌ Erro no ResponsiveTransportLabelGenerator: {e}")
        return False

def test_all_layouts_routing():
    """Testa o roteamento de todos os layouts"""
    
    print("\n=== TESTE DE ROTEAMENTO TODOS OS LAYOUTS ===")
    
    xml_path = "attached_assets/42250485179240000239550020004175361171503396_1750379433035.xml"
    with open(xml_path, 'r', encoding='utf-8') as f:
        xml_content = f.read()
    
    layouts = ["layout1", "layout2", "transul"]
    
    for layout in layouts:
        print(f"\nTestando layout: {layout}")
        
        try:
            generator = ResponsiveTransportLabelGenerator(
                company_name="LAF LOGISTICA",
                company_subtitle="OPERADOR LOGISTICO", 
                paper_width_mm=100,
                paper_height_mm=150,
                layout_style=layout
            )
            
            # Verificar se o layout está correto
            print(f"   Layout configurado: {generator.layout_style}")
            
            result = generator.generate_transport_label(
                xml_content=xml_content,
                pedido_number="PED2025001",
                area_code="01"
            )
            
            if result:
                size = len(result.getvalue())
                print(f"   ✅ Gerado: {size:,} bytes")
                
                filename = f"teste_routing_{layout}.pdf"
                with open(filename, "wb") as f:
                    f.write(result.getvalue())
                print(f"   📄 Salvo: {filename}")
            else:
                print(f"   ❌ Falha na geração")
                
        except Exception as e:
            print(f"   ❌ Erro: {e}")

if __name__ == "__main__":
    print("Iniciando debug do roteamento...")
    
    # Teste de roteamento específico
    success = test_routing_debug()
    
    # Teste de todos os layouts
    test_all_layouts_routing()
    
    print("\n" + "="*50)
    if success:
        print("✅ ROTEAMENTO FUNCIONANDO CORRETAMENTE")
        print("   Layout 'transul' direcionado para TransulExactLayoutGenerator")
    else:
        print("❌ PROBLEMA NO ROTEAMENTO DETECTADO")
        print("   Verificar configuração do layout 'transul'")