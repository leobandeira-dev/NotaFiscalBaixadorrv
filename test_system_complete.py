#!/usr/bin/env python3
"""
Teste do sistema completo com enquadramento forçado
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from reportlab.pdfgen import canvas
from reportlab.lib import colors
from io import BytesIO
import xml.etree.ElementTree as ET
from xml_processor import extract_xml_data

def create_label_with_forced_borders(xml_content, paper_width_mm=100, paper_height_mm=150):
    """Cria etiqueta com bordas absolutamente forçadas"""
    
    # Converter mm para pontos
    width_pts = paper_width_mm * 2.83465
    height_pts = paper_height_mm * 2.83465
    
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=(width_pts, height_pts))
    
    # Extrair dados do XML
    xml_data = extract_xml_data(xml_content)
    
    def draw_framed_section(x, y, width, height, title, content, bg_color=colors.lightgrey):
        """Desenha seção com borda SEMPRE visível"""
        # Fundo
        c.setFillColor(bg_color)
        c.rect(x, y, width, height, fill=1, stroke=0)
        
        # Borda PRETA GROSSA - SEMPRE
        c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.rect(x, y, width, height, fill=0, stroke=1)
        
        # Texto
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 9)
        if title:
            c.drawString(x + 5, y + height - 15, f"{title}: {content}")
        else:
            c.drawString(x + 5, y + height - 15, content)
    
    # Dimensões
    margin = 15
    content_width = width_pts - 2 * margin
    section_height = 25
    spacing = 8
    
    # Posições Y
    current_y = height_pts - margin - section_height
    
    # 1. EMPRESA (com borda)
    draw_framed_section(margin, current_y, content_width, section_height, 
                       None, "teste3 - teste23")
    current_y -= (section_height + spacing)
    
    # 2. ID/QR (com borda)
    nf_key = xml_data.get('chave_nfe', 'N/A')
    id_display = f"ID: {nf_key[-6:]}" if len(nf_key) >= 6 else f"ID: {nf_key}"
    draw_framed_section(margin, current_y, content_width, section_height, 
                       None, id_display)
    current_y -= (section_height + spacing)
    
    # 3. NF (com borda)
    numero_nf = xml_data.get('numero_nf', '00000')
    draw_framed_section(margin, current_y, content_width, section_height, 
                       "NF", numero_nf)
    current_y -= (section_height + spacing)
    
    # 4. PEDIDO (com borda)
    draw_framed_section(margin, current_y, content_width, section_height, 
                       "Pedido", "PED1750429573581")
    current_y -= (section_height + spacing)
    
    # 5. REMETENTE (com borda)
    remetente = xml_data.get('remetente_razao', xml_data.get('remetente_nome', 'N/A'))[:35]
    draw_framed_section(margin, current_y, content_width, section_height, 
                       "Remetente", remetente)
    current_y -= (section_height + spacing)
    
    # 6. DESTINATÁRIO (com borda) - seção maior
    dest_height = 40
    current_y -= (dest_height - section_height)
    
    # Área disponível (75% da largura)
    dest_width = content_width * 0.75
    draw_framed_section(margin, current_y, dest_width, dest_height, None, "DESTINATÁRIO")
    
    # ÁREA (25% da largura) 
    area_width = content_width * 0.22
    area_x = margin + dest_width + 10
    draw_framed_section(area_x, current_y, area_width, dest_height, None, "ÁREA\n01")
    
    current_y -= (dest_height + spacing)
    
    # 7. CIDADE/UF (com borda)
    cidade = xml_data.get('destinatario_cidade', 'N/A')
    uf = xml_data.get('destinatario_uf', 'N/A')
    draw_framed_section(margin, current_y, content_width * 0.75, section_height, 
                       "Cidade/UF", f"{cidade} {uf}")
    current_y -= (section_height + spacing)
    
    # 8. PESO/VOLUME (com borda)
    peso = xml_data.get('peso_bruto', '0')
    volumes = xml_data.get('volumes', '1')
    draw_framed_section(margin, current_y, content_width * 0.75, section_height, 
                       "Peso/Volume", f"{peso}kg - Vol: 1/{volumes}")
    
    c.save()
    return buffer

def test_complete_system():
    """Teste do sistema completo"""
    
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
    
    print("=== TESTE SISTEMA COMPLETO COM BORDAS FORÇADAS ===")
    
    pdf = create_label_with_forced_borders(xml_content)
    
    with open("teste_sistema_completo.pdf", "wb") as f:
        f.write(pdf.getvalue())
    
    size = len(pdf.getvalue())
    print(f"PDF gerado: teste_sistema_completo.pdf ({size:,} bytes)")
    print("Este PDF deve ter TODAS as seções com bordas pretas visíveis.")
    return True

if __name__ == "__main__":
    test_complete_system()