"""
Gerador de etiqueta que replica exatamente o layout Transul da imagem de referência
Layout específico baseado na análise visual da imagem fornecida
"""

import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
import qrcode
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from xml_processor import extract_xml_data
import logging

logger = logging.getLogger(__name__)

class TransulExactLayoutGenerator:
    """Gerador que replica o layout exato da etiqueta Transul da imagem de referência"""
    
    def __init__(self, paper_width_mm=100, paper_height_mm=150):
        """
        Inicializa gerador com dimensões específicas
        
        Args:
            paper_width_mm: Largura em milímetros
            paper_height_mm: Altura em milímetros
        """
        self.paper_width_mm = paper_width_mm
        self.paper_height_mm = paper_height_mm
        self.page_width = paper_width_mm * mm
        self.page_height = paper_height_mm * mm
        
        # Margens específicas do layout Transul
        self.margin = 3 * mm
        self.content_width = self.page_width - (2 * self.margin)
        self.content_height = self.page_height - (2 * self.margin)
        
    def generate_transul_exact_label(self, xml_content, pedido_number, area_code="01", 
                                   company_logo_path=None, volume_info="1/1"):
        """
        Gera etiqueta com layout exato da referência Transul
        
        Args:
            xml_content: Conteúdo XML da NFe
            pedido_number: Número do pedido
            area_code: Código da área
            company_logo_path: Caminho da logo da empresa
            volume_info: Informação do volume (ex: "1/2")
            
        Returns:
            BytesIO buffer com PDF gerado
        """
        try:
            # Extrair dados do XML
            xml_data = extract_xml_data(xml_content)
            
            # Criar buffer PDF
            buffer = io.BytesIO()
            
            # Criar canvas para controle preciso
            c = canvas.Canvas(buffer, pagesize=(self.page_width, self.page_height))
            
            # Desenhar layout exato baseado na imagem
            self._draw_transul_exact_layout(c, xml_data, pedido_number, area_code, 
                                          company_logo_path, volume_info)
            
            # Finalizar PDF
            c.save()
            buffer.seek(0)
            
            logger.info(f"Etiqueta Transul exata gerada: {len(buffer.getvalue())} bytes")
            return buffer
            
        except Exception as e:
            logger.error(f"Erro ao gerar etiqueta Transul exata: {e}")
            return None
    
    def _draw_transul_exact_layout(self, c, xml_data, pedido_number, area_code, 
                                 company_logo_path, volume_info):
        """Desenha o layout exato conforme a imagem de referência"""
        
        # Posições baseadas na análise da imagem
        y_start = self.page_height - self.margin
        current_y = y_start
        
        # 1. CABEÇALHO EMPRESA (Transul / TRANSPORTE)
        current_y = self._draw_company_header(c, current_y, company_logo_path)
        current_y -= 8 * mm
        
        # 2. ID da etiqueta (lado esquerdo) + QR Code (lado direito)
        current_y = self._draw_id_and_qr_section(c, current_y, xml_data, volume_info)
        current_y -= 6 * mm
        
        # 3. NF com fundo preto
        current_y = self._draw_nf_section(c, current_y, xml_data)
        current_y -= 2 * mm
        
        # 4. Pedido com fundo preto
        current_y = self._draw_pedido_section(c, current_y, pedido_number)
        current_y -= 2 * mm
        
        # 5. Remetente com fundo preto
        current_y = self._draw_remetente_section(c, current_y, xml_data)
        current_y -= 2 * mm
        
        # 6. Destinatário (fundo branco)
        current_y = self._draw_destinatario_section(c, current_y, xml_data)
        current_y -= 6 * mm
        
        # 7. Cidade/UF com fundo preto
        current_y = self._draw_cidade_uf_section(c, current_y, xml_data)
        current_y -= 6 * mm
        
        # 8. Peso e Volume (lado esquerdo)
        current_y = self._draw_peso_volume_section(c, current_y, xml_data, volume_info)
        
        # 9. ÁREA (canto inferior direito)
        self._draw_area_section(c, area_code)
        
        # 10. Rodapé CROSS WMS (canto inferior esquerdo)
        self._draw_footer(c)
    
    def _draw_company_header(self, c, y_pos, logo_path):
        """Desenha cabeçalho da empresa centralizado"""
        # Nome principal
        c.setFont("Helvetica-Bold", 18)
        company_name = "Transul"  # Baseado na imagem
        text_width = c.stringWidth(company_name, "Helvetica-Bold", 18)
        x_centered = (self.page_width - text_width) / 2
        c.drawString(x_centered, y_pos, company_name)
        y_pos -= 6 * mm
        
        # Subtítulo
        c.setFont("Helvetica", 10)
        subtitle = "TRANSPORTE"
        text_width = c.stringWidth(subtitle, "Helvetica", 10)
        x_centered = (self.page_width - text_width) / 2
        c.drawString(x_centered, y_pos, subtitle)
        
        return y_pos - 4 * mm
    
    def _draw_id_and_qr_section(self, c, y_pos, xml_data, volume_info):
        """Desenha ID da etiqueta e QR code"""
        # ID no lado esquerdo
        id_text = f"ID: {xml_data.get('numero_nf', 'N/A')}-{xml_data.get('serie', '001')}-{volume_info.replace('/', '-')}"
        c.setFont("Helvetica", 9)
        c.drawString(self.margin, y_pos, id_text)
        
        # QR Code no lado direito
        qr_data = f"{xml_data.get('numero_nf', '')}-{volume_info}"
        self._draw_qr_code(c, qr_data, self.page_width - self.margin - 15*mm, y_pos - 10*mm, 15*mm)
        
        return y_pos - 15 * mm
    
    def _draw_nf_section(self, c, y_pos, xml_data):
        """Desenha seção NF com fundo preto"""
        section_height = 8 * mm
        
        # Fundo preto
        c.setFillColor(colors.black)
        c.rect(self.margin, y_pos - section_height, self.content_width, section_height, fill=1)
        
        # Texto branco
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        nf_text = f"NF: {xml_data.get('numero_nf', 'N/A')}"
        c.drawString(self.margin + 3*mm, y_pos - 6*mm, nf_text)
        
        # Resetar cor
        c.setFillColor(colors.black)
        return y_pos - section_height
    
    def _draw_pedido_section(self, c, y_pos, pedido_number):
        """Desenha seção Pedido com fundo preto"""
        section_height = 8 * mm
        
        # Fundo preto
        c.setFillColor(colors.black)
        c.rect(self.margin, y_pos - section_height, self.content_width, section_height, fill=1)
        
        # Texto branco
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 12)
        pedido_text = f"Pedido: {pedido_number}"
        c.drawString(self.margin + 3*mm, y_pos - 6*mm, pedido_text)
        
        # Resetar cor
        c.setFillColor(colors.black)
        return y_pos - section_height
    
    def _draw_remetente_section(self, c, y_pos, xml_data):
        """Desenha seção Remetente com fundo preto"""
        section_height = 8 * mm
        
        # Fundo preto
        c.setFillColor(colors.black)
        c.rect(self.margin, y_pos - section_height, self.content_width, section_height, fill=1)
        
        # Texto branco
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        remetente_text = f"Remetente: {xml_data.get('emitente_nome', 'N/A')[:35]}"
        c.drawString(self.margin + 3*mm, y_pos - 6*mm, remetente_text)
        
        # Resetar cor
        c.setFillColor(colors.black)
        return y_pos - section_height
    
    def _draw_destinatario_section(self, c, y_pos, xml_data):
        """Desenha seção Destinatário com fundo branco"""
        section_height = 16 * mm
        
        # Fundo branco com borda
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.rect(self.margin, y_pos - section_height, self.content_width, section_height, fill=0)
        
        # Texto preto
        c.setFillColor(colors.black)
        c.setFont("Helvetica-Bold", 10)
        
        # Nome do destinatário
        dest_nome = xml_data.get('destinatario_nome', 'N/A')
        c.drawString(self.margin + 2*mm, y_pos - 5*mm, f"Destinatário: {dest_nome[:30]}")
        
        # Endereço
        endereco = xml_data.get('destinatario_endereco', 'N/A')
        cep = xml_data.get('destinatario_cep', 'N/A')
        c.setFont("Helvetica", 9)
        c.drawString(self.margin + 2*mm, y_pos - 10*mm, f"Endereço: {endereco[:35]}")
        c.drawString(self.margin + 2*mm, y_pos - 14*mm, f"CEP: {cep}")
        
        return y_pos - section_height
    
    def _draw_cidade_uf_section(self, c, y_pos, xml_data):
        """Desenha seção Cidade/UF com fundo preto"""
        section_height = 8 * mm
        
        # Fundo preto
        c.setFillColor(colors.black)
        c.rect(self.margin, y_pos - section_height, self.content_width, section_height, fill=1)
        
        # Texto branco
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 12)
        cidade = xml_data.get('destinatario_cidade', 'N/A')
        uf = xml_data.get('destinatario_uf', 'N/A')
        cidade_uf_text = f"Cidade/UF: {cidade} {uf}"
        c.drawString(self.margin + 3*mm, y_pos - 6*mm, cidade_uf_text)
        
        # Resetar cor
        c.setFillColor(colors.black)
        return y_pos - section_height
    
    def _draw_peso_volume_section(self, c, y_pos, xml_data, volume_info):
        """Desenha seção Peso e Volume no lado esquerdo"""
        # Peso com fundo preto
        peso_height = 8 * mm
        peso_width = 35 * mm
        
        c.setFillColor(colors.black)
        c.rect(self.margin, y_pos - peso_height, peso_width, peso_height, fill=1)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        peso = xml_data.get('peso_bruto', '0')
        peso_text = f"Peso: {peso}"
        c.drawString(self.margin + 2*mm, y_pos - 6*mm, peso_text)
        
        # Transportadora (abaixo do peso)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 8)
        transportadora = xml_data.get('transportadora_nome', 'TRANSUL TRANSPORTE')
        c.drawString(self.margin, y_pos - peso_height - 4*mm, f"Transportadora: {transportadora}")
        
        # Volume com fundo preto (abaixo da transportadora)
        volume_y = y_pos - peso_height - 8*mm
        volume_height = 8 * mm
        
        c.setFillColor(colors.black)
        c.rect(self.margin, volume_y - volume_height, peso_width, volume_height, fill=1)
        
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        volume_text = f"Volume: {volume_info}"
        c.drawString(self.margin + 2*mm, volume_y - 6*mm, volume_text)
        
        # Resetar cor
        c.setFillColor(colors.black)
        return volume_y - volume_height
    
    def _draw_area_section(self, c, area_code):
        """Desenha seção ÁREA no canto inferior direito"""
        area_width = 20 * mm
        area_height = 20 * mm
        x_pos = self.page_width - self.margin - area_width
        y_pos = self.margin
        
        # Fundo preto
        c.setFillColor(colors.black)
        c.rect(x_pos, y_pos, area_width, area_height, fill=1)
        
        # Texto branco centralizado
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 8)
        
        # "ÁREA"
        area_text = "ÁREA"
        text_width = c.stringWidth(area_text, "Helvetica-Bold", 8)
        x_centered = x_pos + (area_width - text_width) / 2
        c.drawString(x_centered, y_pos + 14*mm, area_text)
        
        # Código da área
        c.setFont("Helvetica-Bold", 16)
        code_text = area_code
        text_width = c.stringWidth(code_text, "Helvetica-Bold", 16)
        x_centered = x_pos + (area_width - text_width) / 2
        c.drawString(x_centered, y_pos + 6*mm, code_text)
        
        # Resetar cor
        c.setFillColor(colors.black)
    
    def _draw_footer(self, c):
        """Desenha rodapé CROSS WMS no canto inferior esquerdo"""
        c.setFont("Helvetica", 7)
        c.setFillColor(colors.gray)
        c.drawString(self.margin, self.margin + 2*mm, "CROSS WMS")
        c.setFillColor(colors.black)
    
    def _draw_qr_code(self, c, data, x, y, size):
        """Desenha QR code na posição especificada"""
        try:
            qr = qrcode.QRCode(version=1, box_size=1, border=1)
            qr.add_data(data)
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Converter para formato que o ReportLab aceita
            from reportlab.lib.utils import ImageReader
            qr_buffer = io.BytesIO()
            qr_img.save(qr_buffer, format='PNG')
            qr_buffer.seek(0)
            
            c.drawImage(ImageReader(qr_buffer), x, y, width=size, height=size)
            
        except Exception as e:
            logger.warning(f"Erro ao gerar QR code: {e}")
            # Desenhar retângulo simples como fallback
            c.setStrokeColor(colors.black)
            c.rect(x, y, size, size, fill=0)


def generate_transul_exact_label_from_xml(xml_content, pedido_number, area_code="01", 
                                        company_logo_path=None, volume_info="1/1",
                                        paper_width_mm=100, paper_height_mm=150):
    """
    Função principal para gerar etiqueta com layout exato Transul
    
    Args:
        xml_content: Conteúdo XML da NFe
        pedido_number: Número do pedido
        area_code: Código da área
        company_logo_path: Caminho da logo (não usado neste layout específico)
        volume_info: Informação do volume
        paper_width_mm: Largura do papel
        paper_height_mm: Altura do papel
        
    Returns:
        BytesIO buffer com PDF gerado
    """
    generator = TransulExactLayoutGenerator(paper_width_mm, paper_height_mm)
    return generator.generate_transul_exact_label(
        xml_content, pedido_number, area_code, company_logo_path, volume_info
    )