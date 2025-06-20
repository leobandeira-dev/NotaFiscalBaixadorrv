#!/usr/bin/env python3
"""
Gerador de Etiquetas Melhorado - Estilo Grandes Transportadoras
Foco no endereço do destinatário com visual profissional
"""

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib import colors
import os

def create_professional_transport_label():
    """
    Cria etiqueta profissional inspirada nas grandes transportadoras
    Foco no endereço do destinatário
    """
    
    # Configurações da página
    width = 100 * mm
    height = 150 * mm
    margin = 4 * mm
    
    filename = "etiqueta_transportadora_profissional.pdf"
    c = canvas.Canvas(filename, pagesize=(width, height))
    
    # ===== HEADER CORPORATIVO =====
    y_pos = height - margin
    
    # Logo e nome da empresa (compacto)
    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(colors.black)
    c.drawString(margin, y_pos - 8*mm, "TESTE LOGÍSTICA")
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.grey)
    c.drawString(margin, y_pos - 12*mm, "TRANSPORTE E DISTRIBUIÇÃO")
    
    # QR Code (menor e discreto)
    qr_size = 15*mm
    qr_x = width - margin - qr_size
    qr_y = y_pos - 18*mm
    c.setFillColor(colors.lightgrey)
    c.rect(qr_x, qr_y, qr_size, qr_size, fill=1)
    c.setStrokeColor(colors.grey)
    c.rect(qr_x, qr_y, qr_size, qr_size, fill=0)
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 6)
    c.drawCentredString(qr_x + qr_size/2, qr_y + qr_size/2, "QR CODE")
    
    # ID discreto
    c.setFont("Helvetica", 7)
    c.setFillColor(colors.grey)
    c.drawString(margin, y_pos - 20*mm, "ID: 503396")
    
    # Linha separadora
    y_pos = y_pos - 25*mm
    c.setStrokeColor(colors.lightgrey)
    c.setLineWidth(0.5)
    c.line(margin, y_pos, width - margin, y_pos)
    
    # ===== SEÇÕES COMPACTAS =====
    section_height = 8*mm
    
    def draw_compact_section(title, content, y):
        section_y = y - section_height
        content_width = width - 2 * margin
        
        # Fundo muito sutil
        c.setFillColor(colors.Color(0.98, 0.98, 0.98))
        c.rect(margin, section_y, content_width, section_height, fill=1)
        c.setStrokeColor(colors.Color(0.9, 0.9, 0.9))
        c.setLineWidth(0.5)
        c.rect(margin, section_y, content_width, section_height, fill=0)
        
        # Texto
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 8)
        text_y = section_y + section_height * 0.4
        c.drawString(margin + 2*mm, text_y, f"{title}: {content}")
        
        return section_y
    
    # NF e Pedido (compactos)
    y_pos = draw_compact_section("NF", "417536", y_pos - 2*mm)
    y_pos = draw_compact_section("Pedido", "PED417536-1", y_pos - 1*mm)
    y_pos = draw_compact_section("Origem", "CORSUL COMERCIO - JOINVILLE/SC", y_pos - 1*mm)
    
    # ===== DESTINATÁRIO - SEÇÃO PRINCIPAL =====
    y_pos = y_pos - 3*mm
    dest_height = 35*mm  # 30% do espaço - FOCO NO DESTINATÁRIO
    section_y = y_pos - dest_height
    content_width = width - 2 * margin
    
    # Fundo destaque para destinatário
    c.setFillColor(colors.Color(0.95, 0.97, 1.0))  # Azul muito claro
    c.rect(margin, section_y, content_width, dest_height, fill=1)
    c.setStrokeColor(colors.Color(0.7, 0.8, 0.9))
    c.setLineWidth(1)
    c.rect(margin, section_y, content_width, dest_height, fill=0)
    
    # DESTINATÁRIO - Título destacado
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(margin + 2*mm, section_y + dest_height - 6*mm, "DESTINATÁRIO")
    
    # Nome da empresa destinatária
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin + 2*mm, section_y + dest_height - 12*mm, "CONSORCIO DE ALUMINIO DO MARANHAO")
    c.drawString(margin + 2*mm, section_y + dest_height - 17*mm, "CONSORCIO ALUMAR")
    
    # ENDEREÇO - Seção principal
    c.setFont("Helvetica", 8)
    c.setFillColor(colors.Color(0.3, 0.3, 0.3))
    c.drawString(margin + 2*mm, section_y + dest_height - 22*mm, "Endereço:")
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(colors.black)
    c.drawString(margin + 2*mm, section_y + dest_height - 26*mm, "RODOVIA BR 135, SN")
    c.drawString(margin + 2*mm, section_y + dest_height - 30*mm, "DISTRITO INDUSTRIAL")
    
    # Cidade e CEP
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin + 2*mm, section_y + dest_height - 35*mm, "SAO LUIS - MA")
    c.setFont("Helvetica", 8)
    c.drawString(margin + 35*mm, section_y + dest_height - 35*mm, "CEP: 65095-050")
    
    y_pos = section_y
    
    # ===== INFORMAÇÕES DE TRANSPORTE =====
    y_pos = y_pos - 2*mm
    transport_height = 12*mm
    section_y = y_pos - transport_height
    
    # Dividir em peso e volume
    half_width = (width - 2 * margin - 2*mm) / 2
    
    # PESO (esquerda)
    c.setFillColor(colors.Color(0.96, 0.96, 0.96))
    c.rect(margin, section_y, half_width, transport_height, fill=1)
    c.setStrokeColor(colors.grey)
    c.setLineWidth(0.5)
    c.rect(margin, section_y, half_width, transport_height, fill=0)
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(margin + 2*mm, section_y + transport_height - 6*mm, "PESO")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(margin + 2*mm, section_y + transport_height - 11*mm, "16,200 kg")
    
    # VOLUME (direita)
    volume_x = margin + half_width + 2*mm
    c.setFillColor(colors.Color(0.96, 0.96, 0.96))
    c.rect(volume_x, section_y, half_width, transport_height, fill=1)
    c.setStrokeColor(colors.grey)
    c.setLineWidth(0.5)
    c.rect(volume_x, section_y, half_width, transport_height, fill=0)
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(volume_x + 2*mm, section_y + transport_height - 6*mm, "VOLUME")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(volume_x + 2*mm, section_y + transport_height - 11*mm, "1/2")
    
    # ===== ÁREA (canto inferior direito) =====
    area_width = 20*mm
    area_height = 15*mm
    area_x = width - margin - area_width
    area_y = margin + 2*mm
    
    c.setFillColor(colors.Color(0.93, 0.93, 0.93))
    c.rect(area_x, area_y, area_width, area_height, fill=1)
    c.setStrokeColor(colors.grey)
    c.setLineWidth(1)
    c.rect(area_x, area_y, area_width, area_height, fill=0)
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(area_x + area_width/2, area_y + area_height - 5*mm, "ÁREA")
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(area_x + area_width/2, area_y + 3*mm, "A2")
    
    # ===== FOOTER DISCRETO =====
    c.setFont("Helvetica", 6)
    c.setFillColor(colors.lightgrey)
    c.drawString(margin, margin, "Sistema de Etiquetas - Rastreamento Integrado")
    
    c.save()
    return filename

if __name__ == "__main__":
    filename = create_professional_transport_label()
    if os.path.exists(filename):
        size = os.path.getsize(filename)
        print(f"Etiqueta profissional criada: {filename} ({size} bytes)")
        print("Visual inspirado em grandes transportadoras - Foco no destinatário")
    else:
        print("Erro ao criar etiqueta profissional")