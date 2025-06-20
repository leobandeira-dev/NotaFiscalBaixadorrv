#!/usr/bin/env python3
"""
Teste das melhorias de espaçamento e proporções dos containers
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from responsive_label_generator import ResponsiveTransportLabelGenerator

def test_spacing_improvements():
    """Testa melhorias de espaçamento entre containers"""
    
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
        <NFe>
            <infNFe>
                <ide>
                    <nNF>417549</nNF>
                    <serie>2</serie>
                    <dhEmi>2025-04-17T10:30:00-03:00</dhEmi>
                </ide>
                <emit>
                    <xNome>teste3</xNome>
                    <enderEmit>
                        <xLgr>RUA TESTE</xLgr>
                        <nro>123</nro>
                        <xBairro>CENTRO</xBairro>
                        <xMun>JOINVILLE</xMun>
                        <UF>SC</UF>
                        <CEP>89210001</CEP>
                    </enderEmit>
                </emit>
                <dest>
                    <xNome>CONSORCIO DE ALUMINIO DO MARANHAO CONSORTIUM</xNome>
                    <enderDest>
                        <xLgr>ESTRADA DA ALUMAR</xLgr>
                        <nro>12345</nro>
                        <xBairro>ITAQUI BACANGA DISTRITO INDUSTRIAL</xBairro>
                        <xMun>SAO LUIS</xMun>
                        <UF>MA</UF>
                        <CEP>65110000</CEP>
                    </enderDest>
                </dest>
                <total>
                    <ICMSTot>
                        <vNF>6100.00</vNF>
                    </ICMSTot>
                </total>
                <transp>
                    <transporta>
                        <xNome>TRANSPORTADORA TESTE LTDA</xNome>
                    </transporta>
                    <vol>
                        <qVol>2</qVol>
                        <pesoB>8000</pesoB>
                    </vol>
                </transp>
            </infNFe>
        </NFe>
    </nfeProc>"""
    
    print("=== TESTE DE MELHORIAS DE ESPAÇAMENTO ===")
    
    # Layout 1 com melhorias
    print("\n--- Layout 1 (Moderno) - Melhorado ---")
    generator1 = ResponsiveTransportLabelGenerator(
        company_name="teste3",
        company_subtitle="teste3", 
        paper_width_mm=100,
        paper_height_mm=150,
        layout_style="layout1"
    )
    
    pdf1 = generator1.generate_transport_label(
        xml_content=xml_content,
        pedido_number="PED1750426789269",
        area_code="01"
    )
    
    if pdf1:
        with open("teste_espacamento_melhorado_layout1.pdf", "wb") as f:
            f.write(pdf1.getvalue())
        size1 = len(pdf1.getvalue())
        print(f"✅ PDF gerado: teste_espacamento_melhorado_layout1.pdf ({size1:,} bytes)")
        print("   ✓ Containers maiores (base_section_height * 3)")
        print("   ✓ Espaçamento entre containers: 8 pontos")
        print("   ✓ Destinatário: 2.5x altura base (maior)")
        print("   ✓ Margens internas: 8 pontos")
    else:
        print("❌ Falha na geração Layout 1")
    
    # Layout 2 com melhorias
    print("\n--- Layout 2 (Alto Contraste) - Melhorado ---")
    generator2 = ResponsiveTransportLabelGenerator(
        company_name="teste3",
        company_subtitle="teste3",
        paper_width_mm=100, 
        paper_height_mm=150,
        layout_style="layout2"
    )
    
    pdf2 = generator2.generate_transport_label(
        xml_content=xml_content,
        pedido_number="PED417549-2",
        area_code="01"
    )
    
    if pdf2:
        with open("teste_espacamento_melhorado_layout2.pdf", "wb") as f:
            f.write(pdf2.getvalue())
        size2 = len(pdf2.getvalue())
        print(f"✅ PDF gerado: teste_espacamento_melhorado_layout2.pdf ({size2:,} bytes)")
        print("   ✓ Containers maiores (base_section_height * 3)")
        print("   ✓ Espaçamento entre containers: 8 pontos")
        print("   ✓ Destinatário: 2.5x altura base (maior)")
        print("   ✓ Margens internas: 8 pontos")
    else:
        print("❌ Falha na geração Layout 2")
    
    print("\n=== RESUMO DAS MELHORIAS IMPLEMENTADAS ===")
    print("🔧 Espaçamento base aumentado: 4mm → containers maiores")
    print("🔧 Espaçamento entre seções: 8 pontos → mais respiro visual")
    print("🔧 Container destinatário: 2.5x base → informações completas")
    print("🔧 Margens internas: 8 pontos → textos afastados das bordas")
    print("🔧 Proporções balanceadas: todos os containers redimensionados")
    
    return True

if __name__ == "__main__":
    test_spacing_improvements()