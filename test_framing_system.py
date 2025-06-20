#!/usr/bin/env python3
"""
Teste diagnóstico do sistema de enquadramento visual
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from responsive_label_generator import ResponsiveTransportLabelGenerator

def test_framing_diagnosis():
    """Testa diagnóstico do sistema de enquadramento"""
    
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
        <NFe>
            <infNFe>
                <ide>
                    <nNF>417549</nNF>
                    <serie>2</serie>
                </ide>
                <emit>
                    <xNome>TESTE EMPRESA</xNome>
                </emit>
                <dest>
                    <xNome>CLIENTE DESTINATARIO</xNome>
                    <enderDest>
                        <xMun>SAO PAULO</xMun>
                        <UF>SP</UF>
                    </enderDest>
                </dest>
                <total>
                    <ICMSTot>
                        <vNF>1000.00</vNF>
                    </ICMSTot>
                </total>
                <transp>
                    <vol>
                        <qVol>1</qVol>
                        <pesoB>5000</pesoB>
                    </vol>
                </transp>
            </infNFe>
        </NFe>
    </nfeProc>"""
    
    print("=== DIAGNÓSTICO DO SISTEMA DE ENQUADRAMENTO ===")
    
    # Testar Layout 1 (Moderno)
    print("\n--- Testando Layout 1 (Moderno) ---")
    generator1 = ResponsiveTransportLabelGenerator(
        company_name="TESTE EMPRESA",
        company_subtitle="TRANSPORTE",
        paper_width_mm=100,
        paper_height_mm=150,
        layout_style="layout1"
    )
    
    pdf1 = generator1.generate_transport_label(
        xml_content=xml_content,
        pedido_number="PED123456",
        area_code="01"
    )
    
    if pdf1:
        with open("teste_enquadramento_layout1.pdf", "wb") as f:
            f.write(pdf1.getvalue())
        size1 = len(pdf1.getvalue())
        print(f"✅ Layout 1 gerado: teste_enquadramento_layout1.pdf ({size1:,} bytes)")
        print("   - Deve ter: fundos cinza claro + bordas cinza")
        print("   - Seções: Empresa, NF, Pedido, Remetente, Destinatário, Cidade, Peso/Volume, Área")
    else:
        print("❌ Falha na geração Layout 1")
    
    # Testar Layout 2 (Alto Contraste)
    print("\n--- Testando Layout 2 (Alto Contraste) ---")
    generator2 = ResponsiveTransportLabelGenerator(
        company_name="TESTE EMPRESA",
        company_subtitle="TRANSPORTE",
        paper_width_mm=100,
        paper_height_mm=150,
        layout_style="layout2"
    )
    
    pdf2 = generator2.generate_transport_label(
        xml_content=xml_content,
        pedido_number="PED123456",
        area_code="01"
    )
    
    if pdf2:
        with open("teste_enquadramento_layout2.pdf", "wb") as f:
            f.write(pdf2.getvalue())
        size2 = len(pdf2.getvalue())
        print(f"✅ Layout 2 gerado: teste_enquadramento_layout2.pdf ({size2:,} bytes)")
        print("   - Deve ter: fundos pretos + texto branco")
        print("   - Seções: Empresa, NF, Pedido, Remetente, Destinatário, Cidade, Peso/Volume, Área")
    else:
        print("❌ Falha na geração Layout 2")
    
    print("\n=== ANÁLISE DO PROBLEMA ===")
    print("🔍 O enquadramento visual deve aparecer como:")
    print("   Layout 1: Retângulos cinza claro com bordas cinza")
    print("   Layout 2: Retângulos pretos com texto branco")
    print("🔍 Se não aparecer, problema na função _apply_section_frame")
    
    return True

if __name__ == "__main__":
    test_framing_diagnosis()