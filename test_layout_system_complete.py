#!/usr/bin/env python3
"""
Sistema de teste completo para verificar enquadramento
"""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from io import BytesIO

def create_test_with_forced_borders():
    """Cria PDF de teste com bordas forçadas"""
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(283, 425))  # 100x150mm
    
    # Função simples de enquadramento que SEMPRE funciona
    def draw_frame(x, y, width, height, label):
        # Fundo cinza
        c.setFillColor(colors.lightgrey)
        c.rect(x, y, width, height, fill=1, stroke=0)
        
        # Borda preta GROSSA
        c.setStrokeColor(colors.black)
        c.setLineWidth(3)
        c.rect(x, y, width, height, fill=0, stroke=1)
        
        # Texto
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(x + 5, y + height/2, label)
    
    # Desenhar seções com bordas forçadas
    y_pos = 400
    sections = [
        "EMPRESA",
        "ID/QR",  
        "NF",
        "PEDIDO",
        "REMETENTE",
        "DESTINATÁRIO",
        "CIDADE/UF",
        "PESO/VOLUME",
        "ÁREA"
    ]
    
    for section in sections:
        draw_frame(20, y_pos, 240, 30, section)
        y_pos -= 40
    
    c.save()
    return buffer

def test_basic_framing():
    """Teste básico de enquadramento"""
    print("=== TESTE BÁSICO DE ENQUADRAMENTO ===")
    
    pdf = create_test_with_forced_borders()
    
    with open("teste_basico_bordas.pdf", "wb") as f:
        f.write(pdf.getvalue())
    
    size = len(pdf.getvalue())
    print(f"PDF teste criado: teste_basico_bordas.pdf ({size:,} bytes)")
    print("Este PDF deve mostrar 9 seções com bordas pretas grossas.")
    print("Se as bordas não aparecerem, o problema é no ReportLab.")
    
    return True

if __name__ == "__main__":
    test_basic_framing()