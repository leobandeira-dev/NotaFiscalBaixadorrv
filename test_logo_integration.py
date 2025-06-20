#!/usr/bin/env python3
"""
Teste de integração do sistema de logo nas etiquetas
Verifica se a logo é corretamente carregada e integrada
"""

import os
import logging
from io import BytesIO
from improved_transport_label import ImprovedTransportLabelGenerator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_logo_integration():
    """Testa a integração da logo no sistema de etiquetas"""
    
    print("=== TESTE DE INTEGRAÇÃO DA LOGO ===")
    
    # Simular dados XML para teste
    xml_data = {
        'numero_nf': '417536',
        'serie': '2',
        'emitente_nome': 'CORSUL COMERCIO',
        'emitente_cidade': 'JOINVILLE',
        'emitente_uf': 'SC',
        'destinatario_nome': 'CONSORCIO ALUMAR',
        'destinatario_cidade': 'SAO LUIS',
        'destinatario_uf': 'MA',
        'peso_bruto': '16.2',
        'valor_total': '9150.00'
    }
    
    # Configurações da empresa
    company_name = "TESTE TRANSPORTES LTDA"
    company_subtitle = "LOGÍSTICA INTEGRADA"
    area_code = "01"
    
    # Teste 1: Etiqueta sem logo (placeholder)
    print("\n1. Testando etiqueta sem logo (placeholder)...")
    generator = ImprovedTransportLabelGenerator(
        company_name=company_name,
        company_subtitle=company_subtitle,
        paper_width_mm=100,
        paper_height_mm=150,
        layout_style="layout1",
        company_logo_path=None
    )
    
    try:
        pdf_buffer = generator.generate_transport_label_with_volume_info(
            xml_content=xml_data,
            pedido_number="PED001",
            area_code=area_code,
            company_logo_path=None,
            volume_info="1/1",
            current_volume=1,
            total_volumes=1
        )
        
        if pdf_buffer:
            size = len(pdf_buffer.getvalue())
            print(f"✓ Etiqueta sem logo gerada: {size} bytes")
            
            # Salvar para verificação visual
            with open("teste_etiqueta_sem_logo.pdf", "wb") as f:
                f.write(pdf_buffer.getvalue())
            print("✓ Arquivo salvo: teste_etiqueta_sem_logo.pdf")
        else:
            print("✗ Erro: Buffer vazio")
            
    except Exception as e:
        print(f"✗ Erro ao gerar etiqueta sem logo: {e}")
    
    # Teste 2: Etiqueta com logo (se existir arquivo de teste)
    print("\n2. Testando etiqueta com logo...")
    
    # Verificar se existe alguma logo de teste
    test_logo_paths = [
        "static/uploads/logos/1_test_logo.png",
        "test_logo.png",
        "logo_test.jpg"
    ]
    
    logo_found = None
    for logo_path in test_logo_paths:
        if os.path.exists(logo_path):
            logo_found = logo_path
            break
    
    if logo_found:
        print(f"Logo encontrada: {logo_found}")
        
        generator_with_logo = ImprovedTransportLabelGenerator(
            company_name=company_name,
            company_subtitle=company_subtitle,
            paper_width_mm=100,
            paper_height_mm=150,
            layout_style="layout1",
            company_logo_path=logo_found
        )
        
        try:
            pdf_buffer_logo = generator_with_logo.generate_transport_label_with_volume_info(
                xml_content=xml_data,
                pedido_number="PED002",
                area_code=area_code,
                company_logo_path=logo_found,
                volume_info="1/1",
                current_volume=1,
                total_volumes=1
            )
            
            if pdf_buffer_logo:
                size = len(pdf_buffer_logo.getvalue())
                print(f"✓ Etiqueta com logo gerada: {size} bytes")
                
                # Salvar para verificação visual
                with open("teste_etiqueta_com_logo.pdf", "wb") as f:
                    f.write(pdf_buffer_logo.getvalue())
                print("✓ Arquivo salvo: teste_etiqueta_com_logo.pdf")
            else:
                print("✗ Erro: Buffer vazio")
                
        except Exception as e:
            print(f"✗ Erro ao gerar etiqueta com logo: {e}")
    else:
        print("ℹ Nenhuma logo de teste encontrada")
        print("  Para testar com logo, adicione um arquivo em:")
        for path in test_logo_paths:
            print(f"  - {path}")
    
    # Teste 3: Verificar diferentes layouts
    print("\n3. Testando diferentes layouts...")
    
    for layout_style in ["layout1", "layout2"]:
        print(f"\n  Testando {layout_style}...")
        
        generator_layout = ImprovedTransportLabelGenerator(
            company_name=company_name,
            company_subtitle=company_subtitle,
            paper_width_mm=100,
            paper_height_mm=150,
            layout_style=layout_style,
            company_logo_path=logo_found
        )
        
        try:
            pdf_buffer_layout = generator_layout.generate_transport_label_with_volume_info(
                xml_content=xml_data,
                pedido_number=f"PED{layout_style[-1]}",
                area_code=area_code,
                company_logo_path=logo_found,
                volume_info="1/2",
                current_volume=1,
                total_volumes=2
            )
            
            if pdf_buffer_layout:
                size = len(pdf_buffer_layout.getvalue())
                print(f"  ✓ {layout_style}: {size} bytes")
                
                with open(f"teste_etiqueta_{layout_style}.pdf", "wb") as f:
                    f.write(pdf_buffer_layout.getvalue())
                print(f"  ✓ Arquivo salvo: teste_etiqueta_{layout_style}.pdf")
            else:
                print(f"  ✗ {layout_style}: Buffer vazio")
                
        except Exception as e:
            print(f"  ✗ {layout_style}: {e}")
    
    print("\n=== TESTE CONCLUÍDO ===")
    print("Arquivos gerados podem ser verificados visualmente para confirmar:")
    print("- Presença de espaço reservado para logo")
    print("- Integração correta da logo quando disponível")
    print("- Funcionamento em diferentes layouts")

if __name__ == "__main__":
    test_logo_integration()