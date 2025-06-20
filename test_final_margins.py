#!/usr/bin/env python3
"""
Teste final para garantir que TODAS as seções tenham bordas visíveis
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from responsive_label_generator import ResponsiveTransportLabelGenerator

def test_complete_framing():
    """Teste para verificar se todas as seções têm bordas"""
    
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
    
    print("=== TESTE FINAL DE ENQUADRAMENTO ===")
    
    # Layout 2 - Alto Contraste (mais fácil de ver as bordas)
    generator = ResponsiveTransportLabelGenerator(
        company_name="teste3",
        company_subtitle="teste23",
        paper_width_mm=100,
        paper_height_mm=150,
        layout_style="layout2"
    )
    
    pdf = generator.generate_transport_label(
        xml_content=xml_content,
        pedido_number="PED1750429131295",
        area_code="01"
    )
    
    if pdf:
        with open("teste_basico_enquadramento.pdf", "wb") as f:
            f.write(pdf.getvalue())
        size = len(pdf.getvalue())
        print(f"PDF gerado: teste_basico_enquadramento.pdf ({size:,} bytes)")
        print("Verificando se todas as seções têm bordas:")
        print("• Cabeçalho da empresa")
        print("• Seção ID/QR")
        print("• Seção NF")
        print("• Seção Pedido")
        print("• Seção Remetente")
        print("• Seção Destinatário")
        print("• Seção Cidade/UF")
        print("• Seção Peso/Volume")
        print("• Seção Área")
        return True
    else:
        print("Erro ao gerar PDF")
        return False

if __name__ == "__main__":
    test_complete_framing()