#!/usr/bin/env python3
"""
Teste visual extremo para verificar enquadramento
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from responsive_label_generator import ResponsiveTransportLabelGenerator

def test_visual_framing():
    """Teste com bordas extremamente contrastadas"""
    
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
        <NFe>
            <infNFe Id="NFe11340001001001417549">
                <ide>
                    <nNF>417549</nNF>
                    <serie>2</serie>
                    <dhEmi>2025-04-17T10:30:00-03:00</dhEmi>
                </ide>
                <emit>
                    <xNome>CORSUL COMERCIO E REPRESENTACOES DO SUL LTDA</xNome>
                    <enderEmit>
                        <xLgr>RUA GUARUJA</xLgr>
                        <nro>434</nro>
                        <xBairro>ITAUM</xBairro>
                        <xMun>JOINVILLE</xMun>
                        <UF>SC</UF>
                        <CEP>89210001</CEP>
                    </enderEmit>
                </emit>
                <dest>
                    <xNome>CONSORCIO DE ALUMINIO DO MARANHAO</xNome>
                    <enderDest>
                        <xLgr>RODOVIA BR 135</xLgr>
                        <nro>SN</nro>
                        <xBairro>DISTRITO INDUSTRIAL</xBairro>
                        <xMun>SAO LUIS</xMun>
                        <UF>MA</UF>
                        <CEP>65110000</CEP>
                    </enderDest>
                </dest>
                <total>
                    <ICMSTot>
                        <vNF>9150.00</vNF>
                    </ICMSTot>
                </total>
                <transp>
                    <transporta>
                        <xNome>SCHREIBER LOGISTICA LTDA</xNome>
                    </transporta>
                    <vol>
                        <qVol>2</qVol>
                        <pesoB>16200</pesoB>
                    </vol>
                </transp>
            </infNFe>
        </NFe>
    </nfeProc>"""
    
    print("=== TESTE VISUAL DE ENQUADRAMENTO ===")
    
    # Layout 1 - Bordas pretas grossas
    print("Testando Layout 1 (bordas pretas grossas)...")
    generator1 = ResponsiveTransportLabelGenerator(
        company_name="TESTE BORDAS",
        company_subtitle="LAYOUT 1",
        paper_width_mm=100,
        paper_height_mm=150,
        layout_style="layout1"
    )
    
    pdf1 = generator1.generate_transport_label(
        xml_content=xml_content,
        pedido_number="TESTE123",
        area_code="01"
    )
    
    if pdf1:
        with open("teste_enquadramento_layout1.pdf", "wb") as f:
            f.write(pdf1.getvalue())
        print(f"✓ Layout 1: teste_enquadramento_layout1.pdf ({len(pdf1.getvalue()):,} bytes)")
    
    # Layout 2 - Bordas brancas grossas
    print("Testando Layout 2 (bordas brancas grossas)...")
    generator2 = ResponsiveTransportLabelGenerator(
        company_name="TESTE BORDAS",
        company_subtitle="LAYOUT 2", 
        paper_width_mm=100,
        paper_height_mm=150,
        layout_style="layout2"
    )
    
    pdf2 = generator2.generate_transport_label(
        xml_content=xml_content,
        pedido_number="TESTE123",
        area_code="01"
    )
    
    if pdf2:
        with open("teste_enquadramento_layout2.pdf", "wb") as f:
            f.write(pdf2.getvalue())
        print(f"✓ Layout 2: teste_enquadramento_layout2.pdf ({len(pdf2.getvalue()):,} bytes)")
    
    print("\nSe as bordas não estiverem visíveis nestes PDFs, há um problema fundamental na função de enquadramento.")
    return True

if __name__ == "__main__":
    test_visual_framing()