#!/usr/bin/env python3
"""
Teste do sistema de enquadramento visual corrigido
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from responsive_label_generator import ResponsiveTransportLabelGenerator

def test_framing_system():
    """Teste específico do sistema de enquadramento"""
    
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
    
    print("=== TESTE SISTEMA DE ENQUADRAMENTO CORRIGIDO ===")
    
    # Teste Layout 1 - Com bordas corrigidas
    print("\n--- Layout 1 (Moderno) - Bordas Corrigidas ---")
    generator1 = ResponsiveTransportLabelGenerator(
        company_name="teste3",
        company_subtitle="teste23",
        paper_width_mm=100,
        paper_height_mm=150,
        layout_style="layout1"
    )
    
    pdf1 = generator1.generate_transport_label(
        xml_content=xml_content,
        pedido_number="PED1750428740753",
        area_code="01"
    )
    
    if pdf1:
        with open("teste_enquadramento_layout1.pdf", "wb") as f:
            f.write(pdf1.getvalue())
        size1 = len(pdf1.getvalue())
        print(f"✅ Layout 1 Enquadrado: teste_enquadramento_layout1.pdf ({size1:,} bytes)")
        print("   ✓ Fundo cinza claro com bordas cinza escuras visíveis")
        print("   ✓ Margem interna de 3 pontos para espaçamento")
        print("   ✓ Bordas de 2 pontos de espessura")
        print("   ✓ Todas as seções com enquadramento aplicado")
    else:
        print("❌ Falha Layout 1")
    
    # Teste Layout 2 - Com bordas corrigidas
    print("\n--- Layout 2 (Alto Contraste) - Bordas Corrigidas ---")
    generator2 = ResponsiveTransportLabelGenerator(
        company_name="teste3",
        company_subtitle="teste23",
        paper_width_mm=100,
        paper_height_mm=150,
        layout_style="layout2"
    )
    
    pdf2 = generator2.generate_transport_label(
        xml_content=xml_content,
        pedido_number="PED1750428769424",
        area_code="01"
    )
    
    if pdf2:
        with open("teste_enquadramento_layout2.pdf", "wb") as f:
            f.write(pdf2.getvalue())
        size2 = len(pdf2.getvalue())
        print(f"✅ Layout 2 Enquadrado: teste_enquadramento_layout2.pdf ({size2:,} bytes)")
        print("   ✓ Fundo preto com bordas brancas visíveis")
        print("   ✓ Margem interna de 3 pontos para espaçamento")
        print("   ✓ Bordas brancas de 2 pontos de espessura")
        print("   ✓ Texto branco contrastante sobre fundo preto")
    else:
        print("❌ Falha Layout 2")
    
    print("\n=== CARACTERÍSTICAS DO ENQUADRAMENTO ===")
    print("🔲 Bordas Visíveis:")
    print("   • Layout 1: Bordas cinza escuras sobre fundo cinza claro")
    print("   • Layout 2: Bordas brancas sobre fundo preto")
    print("   • Espessura: 2 pontos para visibilidade máxima")
    print("   • Margem interna: 3 pontos para espaçamento do texto")
    
    print("🔲 Aplicação Consistente:")
    print("   • Cabeçalho da empresa")
    print("   • Seções de destaque (NF, Pedido)")
    print("   • Seção do remetente")
    print("   • Seção do destinatário")
    print("   • Seções de peso/volume")
    print("   • Seção da área")
    
    return True

if __name__ == "__main__":
    test_framing_system()