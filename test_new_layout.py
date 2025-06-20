#!/usr/bin/env python3
"""
Teste do novo layout de etiquetas enquadrado
"""

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
import os

def create_test_label():
    """Cria etiqueta de teste com novo layout enquadrado"""
    
    # Configurações da página
    width = 100 * mm
    height = 150 * mm
    margin = 5 * mm
    
    filename = "teste_etiqueta_enquadrada.pdf"
    c = canvas.Canvas(filename, pagesize=(width, height))
    
    # Posição inicial
    y_pos = height - margin
    section_height = 15 * mm
    
    # Função para desenhar seção enquadrada
    def draw_framed_section(title, content, y):
        section_y = y - section_height
        content_width = width - 2 * margin
        
        # Fundo cinza claro
        c.setFillColor(colors.lightgrey)
        c.rect(margin, section_y, content_width, section_height, fill=1)
        
        # Borda cinza
        c.setStrokeColor(colors.grey)
        c.setLineWidth(1)
        c.rect(margin, section_y, content_width, section_height, fill=0)
        
        # Texto preto
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        text_y = section_y + section_height * 0.3
        c.drawString(margin + 2*mm, text_y, f"{title}: {content}")
        
        return section_y
    
    # Cabeçalho da empresa
    c.setFont("Helvetica-Bold", 14)
    c.drawString(margin, y_pos - 8*mm, "TESTE LOGÍSTICA")
    c.setFont("Helvetica", 10)
    c.drawString(margin, y_pos - 12*mm, "TRANSPORTE")
    
    # QR Code simulado
    qr_size = 20*mm
    qr_x = width - margin - qr_size
    qr_y = y_pos - 20*mm
    c.setFillColor(colors.black)
    c.rect(qr_x, qr_y, qr_size, qr_size, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica", 8)
    c.drawCentredString(qr_x + qr_size/2, qr_y + qr_size/2, "QR")
    
    # ID
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 8)
    c.drawString(margin, y_pos - 25*mm, "ID: 503396")
    
    # Seções enquadradas
    y_pos = y_pos - 30*mm
    
    y_pos = draw_framed_section("NF", "417536", y_pos)
    y_pos = draw_framed_section("Pedido", "PED417536-1", y_pos - 2*mm)
    y_pos = draw_framed_section("Remetente", "CORSUL COMERCIO E REPRESENTACOES", y_pos - 2*mm)
    
    # Destinatário (seção expandida)
    section_y = y_pos - 25*mm - 2*mm
    content_width = width - 2 * margin
    
    c.setFillColor(colors.lightgrey)
    c.rect(margin, section_y, content_width, 25*mm, fill=1)
    c.setStrokeColor(colors.grey)
    c.setLineWidth(1)
    c.rect(margin, section_y, content_width, 25*mm, fill=0)
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin + 2*mm, section_y + 20*mm, "Destinatário: CONSORCIO ALUMAR")
    c.setFont("Helvetica", 8)
    c.drawString(margin + 2*mm, section_y + 15*mm, "Endereço: RODOVIA BR 135, SN, DISTRITO INDUSTRIAL")
    c.drawString(margin + 2*mm, section_y + 10*mm, "Endereço: SN, DISTRITO INDUSTRIAL, SAO LUIS")
    c.drawString(margin + 2*mm, section_y + 5*mm, "CEP: 65095050")
    
    y_pos = section_y
    
    # Cidade/UF
    y_pos = draw_framed_section("Cidade/UF", "SAO LUIS MA", y_pos - 2*mm)
    
    # Peso e Volume (dividido)
    section_y = y_pos - section_height - 2*mm
    half_width = (width - 2 * margin) / 2 - 1*mm
    
    # Peso (esquerda)
    c.setFillColor(colors.lightgrey)
    c.rect(margin, section_y, half_width, section_height, fill=1)
    c.setStrokeColor(colors.grey)
    c.setLineWidth(1)
    c.rect(margin, section_y, half_width, section_height, fill=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    text_y = section_y + section_height * 0.3
    c.drawString(margin + 2*mm, text_y, "Peso: 16,200")
    
    # Volume (direita)
    volume_x = margin + half_width + 2*mm
    c.setFillColor(colors.lightgrey)
    c.rect(volume_x, section_y, half_width, section_height, fill=1)
    c.setStrokeColor(colors.grey)
    c.setLineWidth(1)
    c.rect(volume_x, section_y, half_width, section_height, fill=0)
    c.setFillColor(colors.black)
    c.drawString(volume_x + 2*mm, text_y, "Volume: 1/2")
    
    # Área (canto inferior direito)
    area_width = 25*mm
    area_height = 20*mm
    area_x = width - margin - area_width
    area_y = margin
    
    c.setFillColor(colors.lightgrey)
    c.rect(area_x, area_y, area_width, area_height, fill=1)
    c.setStrokeColor(colors.grey)
    c.setLineWidth(2)
    c.rect(area_x, area_y, area_width, area_height, fill=0)
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(area_x + area_width/2, area_y + area_height * 0.7, "ÁREA")
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(area_x + area_width/2, area_y + area_height * 0.2, "A2")
    
    # Footer
    c.setFont("Helvetica", 6)
    c.setFillColor(colors.grey)
    c.drawString(margin, margin + 2*mm, "Sistema de Etiquetas")
    
    c.save()
    return filename

if __name__ == "__main__":
    filename = create_test_label()
    if os.path.exists(filename):
        size = os.path.getsize(filename)
        print(f"Etiqueta de teste criada: {filename} ({size} bytes)")
        print("Layout: fundo cinza claro, bordas enquadradas, menor contraste")
    else:
        print("Erro ao criar etiqueta de teste")