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
                 paper_width_mm=100, paper_height_mm=150, layout_style="layout1", 
                 company_logo_path=None):
        self.company_name = company_name
        self.company_subtitle = company_subtitle
        self.paper_width_mm = paper_width_mm
        self.paper_height_mm = paper_height_mm
        self.layout_style = layout_style
        self.company_logo_path = company_logo_path
        
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
        
        # Dimensões das seções com espaçamento de 2mm entre grupos
        spacing_mm = 2  # 2mm conforme solicitado
        spacing_pts = spacing_mm * 2.83465  # converter mm para pontos
        section_height = max(20, int(self.page_height * 0.08))  # altura responsiva
        current_y = self.page_height - self.margin - section_height
        
        # 1. CABEÇALHO COM EMPRESA E LOGO - COM BORDA GARANTIDA
        header_height = int(section_height * 1.8)  # Maior para acomodar logo
        self._draw_company_header_with_logo_space(
            c, self.margin, current_y, self.content_width, header_height,
            company_logo_path
        )
        current_y -= (header_height + spacing_pts)
        
        # 2. ID/QR - COM DESTAQUE VISUAL
        nf_key = xml_data.get('chave_nfe', 'N/A')
        id_display = f"ID: {nf_key[-6:]}" if len(nf_key) >= 6 else f"ID: {nf_key}"
        self._draw_highlighted_section(
            c, self.margin, current_y, self.content_width, section_height,
            None, id_display, highlight_type='id'
        )
        current_y -= (section_height + spacing_pts)
        
        # 3. NF - SEÇÃO IMPORTANTE COM DESTAQUE
        numero_nf = xml_data.get('numero_nf', '00000')
        self._draw_highlighted_section(
            c, self.margin, current_y, self.content_width, section_height,
            "NF", numero_nf, highlight_type='important'
        )
        current_y -= (section_height + spacing_pts)
        
        # 4. PEDIDO - SEÇÃO IMPORTANTE COM DESTAQUE
        self._draw_highlighted_section(
            c, self.margin, current_y, self.content_width, section_height,
            "Pedido", pedido_number or "N/A", highlight_type='important'
        )
        current_y -= (section_height + spacing_pts)
        
        # 5. REMETENTE - COM BORDA GARANTIDA
        remetente = xml_data.get('remetente_razao', xml_data.get('remetente_nome', 'N/A'))[:40]
        self._draw_section_with_guaranteed_border(
            c, self.margin, current_y, self.content_width, section_height,
            "Remetente", remetente
        )
        current_y -= (section_height + spacing_pts)
        
        # 6. DESTINATÁRIO - COM BORDA GARANTIDA (seção maior)
        dest_height = int(section_height * 1.6)  # 60% maior que seção padrão
        current_y -= (dest_height - section_height)
        dest_width = self.content_width * 0.75
        
        dest_nome = xml_data.get('destinatario_razao', xml_data.get('destinatario_nome', 'N/A'))
        self._draw_section_with_guaranteed_border(
            c, self.margin, current_y, dest_width, dest_height,
            None, f"DESTINATÁRIO\n{dest_nome[:35]}"
        )
        
        # 7. ÁREA - COM BORDA GARANTIDA
        area_width = self.content_width * 0.22
        area_x = self.margin + dest_width + spacing_pts
        self._draw_section_with_guaranteed_border(
            c, area_x, current_y, area_width, dest_height,
            None, f"ÁREA\n{area_code}"
        )
        current_y -= (dest_height + spacing_pts)
        
        # 8. CIDADE/UF - COM BORDA GARANTIDA
        cidade = xml_data.get('destinatario_cidade', 'N/A')
        uf = xml_data.get('destinatario_uf', 'N/A')
        self._draw_section_with_guaranteed_border(
            c, self.margin, current_y, dest_width, section_height,
            "Cidade/UF", f"{cidade} {uf}"
        )
        current_y -= (section_height + spacing_pts)
        
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

    def _draw_company_header_with_logo_space(self, c, x, y, width, height, logo_path):
        """Desenha cabeçalho da empresa com espaço dedicado para logo"""
        
        # Desenhar borda do cabeçalho
        if self.layout_style == 'layout1':
            # Layout 1: fundo cinza claro com borda preta
            c.setFillColor(colors.lightgrey)
            c.rect(x, y, width, height, fill=1, stroke=0)
            c.setStrokeColor(colors.black)
            c.setLineWidth(2)
            c.rect(x, y, width, height, fill=0, stroke=1)
        else:
            # Layout 2: fundo preto com borda branca
            c.setFillColor(colors.black)
            c.rect(x, y, width, height, fill=1, stroke=0)
            c.setStrokeColor(colors.white)
            c.setLineWidth(2)
            c.rect(x, y, width, height, fill=0, stroke=1)
        
        # Definir área para logo (30% da largura)
        logo_width = width * 0.3
        text_width = width * 0.7
        logo_area_x = x + 8
        text_area_x = x + logo_width + 16
        
        # Desenhar logo ou demonstração do espaço reservado
        logo_max_height = height - 16  # 8pt margin top/bottom
        logo_max_width = logo_width - 16  # 8pt margin left/right
        
        if logo_path and os.path.exists(logo_path):
            try:
                from reportlab.lib.utils import ImageReader
                img = ImageReader(logo_path)
                img_width, img_height = img.getSize()
                
                # Calcular escala mantendo proporção
                scale_w = logo_max_width / img_width
                scale_h = logo_max_height / img_height
                scale = min(scale_w, scale_h)
                
                final_width = img_width * scale
                final_height = img_height * scale
                
                # Centralizar logo na área reservada
                logo_x = logo_area_x + (logo_max_width - final_width) / 2
                logo_y = y + (height - final_height) / 2
                
                c.drawImage(logo_path, logo_x, logo_y, final_width, final_height)
                
            except Exception as e:
                print(f"Erro ao carregar logo: {e}")
                self._draw_logo_placeholder(c, logo_area_x, y, logo_max_width, logo_max_height)
        else:
            # Demonstrar espaço reservado para logo
            self._draw_logo_placeholder(c, logo_area_x, y, logo_max_width, logo_max_height)
        
        # Desenhar texto da empresa
        if self.layout_style == 'layout1':
            c.setFillColor(colors.black)
        else:
            c.setFillColor(colors.white)
        
        # Nome da empresa (linha superior)
        c.setFont("Helvetica-Bold", 14)
        company_y = y + height * 0.65
        c.drawString(text_area_x, company_y, self.company_name)
        
        # Subtítulo da empresa (linha inferior)
        c.setFont("Helvetica", 10)
        subtitle_y = y + height * 0.35
        c.drawString(text_area_x, subtitle_y, self.company_subtitle)

    def _draw_logo_placeholder(self, c, x, y, width, height):
        """Desenha placeholder visual para demonstrar espaço da logo"""
        
        # Definir cores baseadas no layout
        if self.layout_style == 'layout1':
            placeholder_color = colors.Color(0.9, 0.9, 0.9)  # Cinza claro
            border_color = colors.Color(0.6, 0.6, 0.6)  # Cinza médio
            text_color = colors.Color(0.5, 0.5, 0.5)  # Cinza escuro
        else:
            placeholder_color = colors.Color(0.3, 0.3, 0.3)  # Cinza escuro
            border_color = colors.Color(0.7, 0.7, 0.7)  # Cinza claro
            text_color = colors.Color(0.8, 0.8, 0.8)  # Branco acinzentado
        
        # Desenhar fundo do placeholder
        c.setFillColor(placeholder_color)
        c.rect(x, y, width, height, fill=1, stroke=0)
        
        # Desenhar borda pontilhada para indicar área reservada
        c.setStrokeColor(border_color)
        c.setLineWidth(1)
        c.setDash([3, 2])  # Linha pontilhada
        c.rect(x, y, width, height, fill=0, stroke=1)
        c.setDash([])  # Resetar para linha sólida
        
        # Desenhar moldura principal da logo
        frame_width = width * 0.8
        frame_height = height * 0.6
        frame_x = x + (width - frame_width) / 2
        frame_y = y + (height - frame_height) / 2
        
        c.setStrokeColor(text_color)
        c.setLineWidth(1.5)
        c.rect(frame_x, frame_y, frame_width, frame_height, fill=0, stroke=1)
        
        # Desenhar cruz de centralização (guias)
        center_x = frame_x + frame_width / 2
        center_y = frame_y + frame_height / 2
        
        c.setLineWidth(0.5)
        c.setDash([2, 2])
        # Linha horizontal
        c.line(frame_x + 5, center_y, frame_x + frame_width - 5, center_y)
        # Linha vertical
        c.line(center_x, frame_y + 5, center_x, frame_y + frame_height - 5)
        c.setDash([])
        
        # Texto "LOGO" centralizado
        c.setFillColor(text_color)
        c.setFont("Helvetica-Bold", 10)
        logo_text = "LOGO"
        logo_width = c.stringWidth(logo_text, "Helvetica-Bold", 10)
        logo_x = center_x - logo_width / 2
        logo_y = center_y - 3
        c.drawString(logo_x, logo_y, logo_text)
        
        # Dimensões da área
        c.setFont("Helvetica", 5)
        dim_text = f"{int(frame_width)}x{int(frame_height)}pt"
        dim_width = c.stringWidth(dim_text, "Helvetica", 5)
        dim_x = frame_x + frame_width - dim_width - 2
        dim_y = frame_y + 2
        c.drawString(dim_x, dim_y, dim_text)
        
        # Texto explicativo
        c.setFont("Helvetica", 7)
        explain_text = "Área Reservada para Logo da Empresa"
        explain_width = c.stringWidth(explain_text, "Helvetica", 7)
        explain_x = x + (width - explain_width) / 2
        explain_y = y + height * 0.05
        c.drawString(explain_x, explain_y, explain_text)

    def _draw_highlighted_section(self, c, x, y, width, height, label, content, highlight_type='normal'):
        """Desenha seção com estilização visual melhorada"""
        
        # Cores baseadas no tipo de destaque
        if highlight_type == 'id':
            # Seção ID com destaque especial
            if self.layout_style == 'layout1':
                bg_color = colors.Color(0.9, 0.95, 1.0)  # Azul muito claro
                border_color = colors.Color(0.2, 0.4, 0.8)  # Azul escuro
                text_color = colors.Color(0.1, 0.1, 0.1)
            else:
                bg_color = colors.Color(0.1, 0.2, 0.4)  # Azul escuro
                border_color = colors.Color(0.7, 0.8, 1.0)  # Azul claro
                text_color = colors.white
        elif highlight_type == 'important':
            # Seções importantes (NF, Pedido)
            if self.layout_style == 'layout1':
                bg_color = colors.Color(0.95, 0.95, 0.7)  # Amarelo claro
                border_color = colors.Color(0.8, 0.6, 0.0)  # Dourado
                text_color = colors.black
            else:
                bg_color = colors.Color(0.4, 0.3, 0.0)  # Dourado escuro
                border_color = colors.Color(1.0, 0.9, 0.3)  # Amarelo
                text_color = colors.white
        else:
            # Seções normais
            if self.layout_style == 'layout1':
                bg_color = colors.lightgrey
                border_color = colors.black
                text_color = colors.black
            else:
                bg_color = colors.black
                border_color = colors.white
                text_color = colors.white
        
        # Desenhar fundo
        c.setFillColor(bg_color)
        c.rect(x, y, width, height, fill=1, stroke=0)
        
        # Desenhar borda com estilo melhorado
        c.setStrokeColor(border_color)
        c.setLineWidth(2)
        c.rect(x, y, width, height, fill=0, stroke=1)
        
        # Margens internas
        margin = 8
        text_x = x + margin
        text_y = y + height / 2
        
        # Desenhar texto com estilo melhorado
        c.setFillColor(text_color)
        
        if label:
            # Seção com label (ex: "NF: 417549")
            c.setFont("Helvetica-Bold", 10)
            label_width = c.stringWidth(label + ": ", "Helvetica-Bold", 10)
            c.drawString(text_x, text_y + 2, label + ":")
            
            c.setFont("Helvetica-Bold", 12)
            c.drawString(text_x + label_width, text_y + 2, str(content))
        else:
            # Seção sem label (ex: só "ID: 417549")
            c.setFont("Helvetica-Bold", 11)
            c.drawString(text_x, text_y + 2, str(content))

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