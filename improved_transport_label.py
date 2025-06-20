#!/usr/bin/env python3
"""
Gerador de Etiquetas de Transporte com Enquadramento GARANTIDO
Sistema que aplica bordas visíveis em TODAS as seções
"""

import os
import logging
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
import qrcode
from xml_processor import extract_xml_data

logger = logging.getLogger(__name__)

class ImprovedTransportLabelGenerator:
    """Gerador com enquadramento garantido em todas as seções"""
    
    def __init__(self, company_name="SUA EMPRESA", company_subtitle="TRANSPORTE", 
                 paper_width_mm=100, paper_height_mm=150, layout_style="layout1"):
        self.company_name = company_name
        self.company_subtitle = company_subtitle
        self.paper_width_mm = paper_width_mm
        self.paper_height_mm = paper_height_mm
        self.layout_style = layout_style
        
        # Converter mm para pontos
        self.page_width = paper_width_mm * 2.83465
        self.page_height = paper_height_mm * 2.83465
        
        # Margens e dimensões
        self.margin = 15
        self.content_width = self.page_width - 2 * self.margin
        self.content_height = self.page_height - 2 * self.margin
        
        # Configurar tamanhos de fonte responsivos
        base_font_size = max(8, int(10 * (paper_width_mm / 100)))
        self.fonts = {
            'company_name': base_font_size + 2,
            'company_sub': base_font_size,
            'section_content': base_font_size + 1,
            'normal_text': base_font_size,
            'small_text': base_font_size - 1,
            'id_text': base_font_size - 1
        }
    
    def _draw_section_with_guaranteed_border(self, c, x, y, width, height, title, content):
        """Desenha seção com borda ABSOLUTAMENTE GARANTIDA"""
        
        # FUNDO SEMPRE
        if self.layout_style == "layout2":
            c.setFillColor(colors.black)
        else:
            c.setFillColor(colors.lightgrey)
        c.rect(x, y, width, height, fill=1, stroke=0)
        
        # BORDA SEMPRE - stroke=1 obrigatório
        if self.layout_style == "layout2":
            c.setStrokeColor(colors.white)
        else:
            c.setStrokeColor(colors.black)
        c.setLineWidth(2)
        c.rect(x, y, width, height, fill=0, stroke=1)
        
        # TEXTO
        if self.layout_style == "layout2":
            c.setFillColor(colors.white)
        else:
            c.setFillColor(colors.black)
        
        c.setFont("Helvetica-Bold", self.fonts['normal_text'])
        text_y = y + height - 15
        
        if title:
            c.drawString(x + 5, text_y, f"{title}: {content}")
        else:
            c.drawString(x + 5, text_y, content)
    
    def generate_transport_label_with_volume_info(self, xml_content: str, pedido_number: str = None, 
                                                area_code: str = "01", company_logo_path: str = None,
                                                volume_info: str = None, current_volume: int = 1, 
                                                total_volumes: int = 1) -> BytesIO:
        """Gera etiqueta com bordas garantidas em todas as seções"""
        
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=(self.page_width, self.page_height))
        
        # Extrair dados do XML
        xml_data = extract_xml_data(xml_content)
        
        # Dimensões das seções
        section_height = 25
        spacing = 8
        current_y = self.page_height - self.margin - section_height
        
        # 1. EMPRESA - COM BORDA GARANTIDA
        self._draw_section_with_guaranteed_border(
            c, self.margin, current_y, self.content_width, section_height,
            None, f"{self.company_name} - {self.company_subtitle}"
        )
        current_y -= (section_height + spacing)
        
        # 2. ID/QR - COM BORDA GARANTIDA
        nf_key = xml_data.get('chave_nfe', 'N/A')
        id_display = f"ID: {nf_key[-6:]}" if len(nf_key) >= 6 else f"ID: {nf_key}"
        self._draw_section_with_guaranteed_border(
            c, self.margin, current_y, self.content_width, section_height,
            None, id_display
        )
        current_y -= (section_height + spacing)
        
        # 3. NF - COM BORDA GARANTIDA
        numero_nf = xml_data.get('numero_nf', '00000')
        self._draw_section_with_guaranteed_border(
            c, self.margin, current_y, self.content_width, section_height,
            "NF", numero_nf
        )
        current_y -= (section_height + spacing)
        
        # 4. PEDIDO - COM BORDA GARANTIDA
        self._draw_section_with_guaranteed_border(
            c, self.margin, current_y, self.content_width, section_height,
            "Pedido", pedido_number or "N/A"
        )
        current_y -= (section_height + spacing)
        
        # 5. REMETENTE - COM BORDA GARANTIDA
        remetente = xml_data.get('remetente_razao', xml_data.get('remetente_nome', 'N/A'))[:40]
        self._draw_section_with_guaranteed_border(
            c, self.margin, current_y, self.content_width, section_height,
            "Remetente", remetente
        )
        current_y -= (section_height + spacing)
        
        # 6. DESTINATÁRIO - COM BORDA GARANTIDA (seção maior)
        dest_height = 40
        current_y -= (dest_height - section_height)
        dest_width = self.content_width * 0.75
        
        dest_nome = xml_data.get('destinatario_razao', xml_data.get('destinatario_nome', 'N/A'))
        self._draw_section_with_guaranteed_border(
            c, self.margin, current_y, dest_width, dest_height,
            None, f"DESTINATÁRIO\n{dest_nome[:35]}"
        )
        
        # 7. ÁREA - COM BORDA GARANTIDA
        area_width = self.content_width * 0.22
        area_x = self.margin + dest_width + 10
        self._draw_section_with_guaranteed_border(
            c, area_x, current_y, area_width, dest_height,
            None, f"ÁREA\n{area_code}"
        )
        current_y -= (dest_height + spacing)
        
        # 8. CIDADE/UF - COM BORDA GARANTIDA
        cidade = xml_data.get('destinatario_cidade', 'N/A')
        uf = xml_data.get('destinatario_uf', 'N/A')
        self._draw_section_with_guaranteed_border(
            c, self.margin, current_y, dest_width, section_height,
            "Cidade/UF", f"{cidade} {uf}"
        )
        current_y -= (section_height + spacing)
        
        # 9. PESO/VOLUME - COM BORDA GARANTIDA
        peso = xml_data.get('peso_bruto', '0')
        if volume_info:
            volume_display = volume_info
        else:
            volume_display = f"{current_volume}/{total_volumes}"
        
        peso_text = f"Peso: {peso}kg - Volume: {volume_display}"
        self._draw_section_with_guaranteed_border(
            c, self.margin, current_y, dest_width, section_height,
            None, peso_text
        )
        
        c.save()
        return buffer

def test_improved_system():
    """Teste do sistema melhorado"""
    
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
    
    print("=== TESTE SISTEMA MELHORADO COM BORDAS GARANTIDAS ===")
    
    # Layout 1
    generator1 = ImprovedTransportLabelGenerator(
        company_name="teste3",
        company_subtitle="teste23",
        layout_style="layout1"
    )
    
    pdf1 = generator1.generate_transport_label_with_volume_info(
        xml_content=xml_content,
        pedido_number="PED1750429573581",
        area_code="01",
        volume_info="1/2",
        current_volume=1,
        total_volumes=2
    )
    
    with open("etiqueta_final.pdf", "wb") as f:
        f.write(pdf1.getvalue())
    
    size = len(pdf1.getvalue())
    print(f"PDF Layout 1: etiqueta_final.pdf ({size:,} bytes)")
    
    # Layout 2
    generator2 = ImprovedTransportLabelGenerator(
        company_name="teste3",
        company_subtitle="teste23",
        layout_style="layout2"
    )
    
    pdf2 = generator2.generate_transport_label_with_volume_info(
        xml_content=xml_content,
        pedido_number="PED1750429573581",
        area_code="01",
        volume_info="2/2",
        current_volume=2,
        total_volumes=2
    )
    
    with open("etiqueta_final_layout2.pdf", "wb") as f:
        f.write(pdf2.getvalue())
    
    size2 = len(pdf2.getvalue())
    print(f"PDF Layout 2: etiqueta_final_layout2.pdf ({size2:,} bytes)")
    print("TODAS as seções devem ter bordas visíveis nestes PDFs.")
    
    return True

if __name__ == "__main__":
    test_improved_system()