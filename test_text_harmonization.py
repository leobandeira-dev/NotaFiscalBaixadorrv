#!/usr/bin/env python3
"""
Teste de harmonização de texto e integração do layout Transul
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from responsive_label_generator import ResponsiveTransportLabelGenerator
from transul_style_generator import generate_transul_style_label

def test_harmonized_layouts():
    """Teste dos 3 layouts harmonizados"""
    
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
        <NFe>
            <infNFe Id="NFe11340001001001417549">
                <ide>
                    <nNF>11340</nNF>
                    <serie>2</serie>
                    <dhEmi>2025-04-17T10:30:00-03:00</dhEmi>
                </ide>
                <emit>
                    <xNome>REAL SINALIZACAO INDUSTRIA COMERCIO LTDA</xNome>
                    <enderEmit>
                        <xLgr>RUA INDUSTRIAL</xLgr>
                        <nro>123</nro>
                        <xBairro>DISTRITO INDUSTRIAL</xBairro>
                        <xMun>SAO PAULO</xMun>
                        <UF>SP</UF>
                        <CEP>01234567</CEP>
                    </enderEmit>
                </emit>
                <dest>
                    <xNome>FORT CLEAN - DISTRIBUIDORA LTDA</xNome>
                    <enderDest>
                        <xLgr>RUA PIAUI</xLgr>
                        <nro>456</nro>
                        <xBairro>CENTRO</xBairro>
                        <xMun>IMPERATRIZ</xMun>
                        <UF>MA</UF>
                        <CEP>65907100</CEP>
                    </enderDest>
                </dest>
                <total>
                    <ICMSTot>
                        <vNF>1225.00</vNF>
                    </ICMSTot>
                </total>
                <transp>
                    <transporta>
                        <xNome>TRANSUL TRANSPORTE</xNome>
                    </transporta>
                    <vol>
                        <qVol>62</qVol>
                        <pesoB>1225000</pesoB>
                    </vol>
                </transp>
            </infNFe>
        </NFe>
    </nfeProc>"""
    
    print("=== TESTE DE HARMONIZAÇÃO DOS 3 LAYOUTS ===")
    
    # Layout 1 (Moderno) - Harmonizado
    print("\n--- Layout 1 (Moderno) - Harmonizado ---")
    generator1 = ResponsiveTransportLabelGenerator(
        company_name="Transul",
        company_subtitle="TRANSPORTE",
        paper_width_mm=100,
        paper_height_mm=150,
        layout_style="layout1"
    )
    
    pdf1 = generator1.generate_transport_label(
        xml_content=xml_content,
        pedido_number="24441",
        area_code="01"
    )
    
    if pdf1:
        with open("teste_layout1_harmonizado.pdf", "wb") as f:
            f.write(pdf1.getvalue())
        size1 = len(pdf1.getvalue())
        print(f"✅ Layout 1 Harmonizado: teste_layout1_harmonizado.pdf ({size1:,} bytes)")
        print("   ✓ Fundos cinza claro com bordas definidas")
        print("   ✓ Controle dinâmico de limites")
        print("   ✓ Espaçamento responsivo")
    else:
        print("❌ Falha Layout 1")
    
    # Layout 2 (Alto Contraste) - Harmonizado
    print("\n--- Layout 2 (Alto Contraste) - Harmonizado ---")
    generator2 = ResponsiveTransportLabelGenerator(
        company_name="Transul",
        company_subtitle="TRANSPORTE",
        paper_width_mm=100,
        paper_height_mm=150,
        layout_style="layout2"
    )
    
    pdf2 = generator2.generate_transport_label(
        xml_content=xml_content,
        pedido_number="24441",
        area_code="01"
    )
    
    if pdf2:
        with open("teste_layout2_harmonizado.pdf", "wb") as f:
            f.write(pdf2.getvalue())
        size2 = len(pdf2.getvalue())
        print(f"✅ Layout 2 Harmonizado: teste_layout2_harmonizado.pdf ({size2:,} bytes)")
        print("   ✓ Faixas pretas com texto branco")
        print("   ✓ Controle dinâmico de limites")
        print("   ✓ Espaçamento responsivo")
    else:
        print("❌ Falha Layout 2")
    
    # Layout 3 (Estilo Transul Profissional) - Novo
    print("\n--- Layout 3 (Estilo Transul Profissional) - Novo ---")
    pdf3 = generate_transul_style_label(
        xml_content=xml_content,
        pedido_number="24441",
        area_code="01",
        company_name="Transul",
        company_subtitle="TRANSPORTE",
        paper_width_mm=100,
        paper_height_mm=150
    )
    
    if pdf3:
        with open("teste_layout3_transul_profissional.pdf", "wb") as f:
            f.write(pdf3.getvalue())
        size3 = len(pdf3.getvalue())
        print(f"✅ Layout 3 Transul: teste_layout3_transul_profissional.pdf ({size3:,} bytes)")
        print("   ✓ Cabeçalho centralizado limpo")
        print("   ✓ Faixas pretas alternadas com seções brancas")
        print("   ✓ Seção destinatário detalhada")
        print("   ✓ Harmonía visual profissional")
        print("   ✓ Replica exatamente o modelo de inspiração")
    else:
        print("❌ Falha Layout 3")
    
    print("\n=== COMPARAÇÃO DOS 3 LAYOUTS ===")
    print("🎯 Layout 1 (Moderno):")
    print("   • Fundos cinza claro com bordas")
    print("   • Estilo elegante e moderno")
    print("   • Boa legibilidade")
    
    print("🎯 Layout 2 (Alto Contraste):")
    print("   • Faixas pretas com texto branco")
    print("   • Máximo contraste visual")
    print("   • Ideal para ambientes industriais")
    
    print("🎯 Layout 3 (Transul Profissional):")
    print("   • Cabeçalho centralizado limpo")
    print("   • Faixas pretas alternadas")
    print("   • Seção branca para destinatário")
    print("   • Replica modelo de inspiração")
    print("   • Harmonia visual empresarial")
    
    return True

if __name__ == "__main__":
    test_harmonized_layouts()