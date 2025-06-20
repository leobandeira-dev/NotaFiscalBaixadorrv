#!/usr/bin/env python3
"""
Teste completo do sistema de layout com diagnóstico visual
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm

def test_basic_framing():
    """Testa enquadramento básico do ReportLab"""
    
    print("=== TESTE BÁSICO DE ENQUADRAMENTO REPORTLAB ===")
    
    # Criar PDF de teste
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(100*mm, 150*mm))
    
    # Teste Layout 1 - Fundo cinza com borda
    print("\n--- Testando Layout 1 (Cinza + Borda) ---")
    
    # Retângulo com fundo cinza claro
    c.setFillColor(colors.lightgrey)
    c.rect(10, 100, 80, 20, fill=1, stroke=0)
    
    # Borda cinza escura
    c.setStrokeColor(colors.grey)
    c.setLineWidth(1.5)
    c.rect(10, 100, 80, 20, fill=0, stroke=1)
    
    # Texto preto
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(15, 107, "TESTE LAYOUT 1 - CINZA + BORDA")
    
    # Teste Layout 2 - Fundo preto
    print("--- Testando Layout 2 (Preto + Texto Branco) ---")
    
    # Retângulo preto
    c.setFillColor(colors.black)
    c.rect(10, 70, 80, 20, fill=1, stroke=0)
    
    # Texto branco
    c.setFillColor(colors.white)
    c.drawString(15, 77, "TESTE LAYOUT 2 - PRETO + BRANCO")
    
    # Teste simples de borda
    print("--- Testando Borda Simples ---")
    c.setStrokeColor(colors.red)
    c.setLineWidth(2)
    c.rect(10, 40, 80, 20, fill=0, stroke=1)
    c.setFillColor(colors.black)
    c.drawString(15, 47, "TESTE BORDA VERMELHA")
    
    c.save()
    
    # Salvar arquivo
    with open("teste_basico_enquadramento.pdf", "wb") as f:
        f.write(buffer.getvalue())
    
    size = len(buffer.getvalue())
    print(f"✅ PDF básico gerado: teste_basico_enquadramento.pdf ({size:,} bytes)")
    print("   - Deve mostrar 3 retângulos com estilos diferentes")
    print("   - Layout 1: Fundo cinza claro + borda cinza")
    print("   - Layout 2: Fundo preto + texto branco")
    print("   - Teste: Borda vermelha simples")
    
    return True

def test_responsive_generator_fixed():
    """Testa gerador responsivo com correções"""
    from responsive_label_generator import ResponsiveTransportLabelGenerator
    
    print("\n=== TESTE GERADOR RESPONSIVO CORRIGIDO ===")
    
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
        <NFe>
            <infNFe>
                <ide>
                    <nNF>417549</nNF>
                    <serie>2</serie>
                </ide>
                <emit>
                    <xNome>TESTE EMPRESA LTDA</xNome>
                </emit>
                <dest>
                    <xNome>CLIENTE DESTINATARIO TESTE</xNome>
                    <enderDest>
                        <xMun>SAO PAULO</xMun>
                        <UF>SP</UF>
                    </enderDest>
                </dest>
                <total>
                    <ICMSTot>
                        <vNF>2500.00</vNF>
                    </ICMSTot>
                </total>
                <transp>
                    <vol>
                        <qVol>3</qVol>
                        <pesoB>12000</pesoB>
                    </vol>
                </transp>
            </infNFe>
        </NFe>
    </nfeProc>"""
    
    # Layout 1 corrigido
    print("\n--- Layout 1 Corrigido ---")
    generator1 = ResponsiveTransportLabelGenerator(
        company_name="TESTE EMPRESA LTDA",
        company_subtitle="TRANSPORTE E LOGÍSTICA",
        paper_width_mm=100,
        paper_height_mm=150,
        layout_style="layout1"
    )
    
    pdf1 = generator1.generate_transport_label(
        xml_content=xml_content,
        pedido_number="PED1750427456789",
        area_code="01"
    )
    
    if pdf1:
        with open("teste_layout1_corrigido.pdf", "wb") as f:
            f.write(pdf1.getvalue())
        size1 = len(pdf1.getvalue())
        print(f"✅ Layout 1 corrigido: teste_layout1_corrigido.pdf ({size1:,} bytes)")
    else:
        print("❌ Falha Layout 1")
    
    # Layout 2 corrigido
    print("--- Layout 2 Corrigido ---")
    generator2 = ResponsiveTransportLabelGenerator(
        company_name="TESTE EMPRESA LTDA",
        company_subtitle="TRANSPORTE E LOGÍSTICA",
        paper_width_mm=100,
        paper_height_mm=150,
        layout_style="layout2"
    )
    
    pdf2 = generator2.generate_transport_label(
        xml_content=xml_content,
        pedido_number="PED1750427456789",
        area_code="01"
    )
    
    if pdf2:
        with open("teste_layout2_corrigido.pdf", "wb") as f:
            f.write(pdf2.getvalue())
        size2 = len(pdf2.getvalue())
        print(f"✅ Layout 2 corrigido: teste_layout2_corrigido.pdf ({size2:,} bytes)")
    else:
        print("❌ Falha Layout 2")
    
    return True

if __name__ == "__main__":
    test_basic_framing()
    test_responsive_generator_fixed()