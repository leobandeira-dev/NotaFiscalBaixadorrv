"""
Gerador de Etiquetas de Transporte - Modelo Transul
Replica exatamente o layout da etiqueta da Transul Transporte
"""
import logging
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
import qrcode
from PIL import Image as PILImage
from xml_processor import extract_xml_data
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class TransulLabelGenerator:
    """Gerador de etiquetas no modelo Transul Transporte"""
    
    def __init__(self):
        self.page_width = 210 * mm  # A4 width
        self.page_height = 297 * mm  # A4 height
        self.margin = 20 * mm
        self.content_width = self.page_width - (2 * self.margin)
    
    def generate_transport_label(self, xml_content: str, pedido_number: str = None, area_code: str = "01") -> BytesIO:
        """
        Gera etiqueta de transporte no modelo Transul
        
        Args:
            xml_content: Conteúdo XML da NFe
            pedido_number: Número do pedido (opcional)
            area_code: Código da área (padrão: "01")
            
        Returns:
            BytesIO contendo o PDF da etiqueta
        """
        try:
            # Extrair dados do XML
            xml_data = extract_xml_data(xml_content)
            
            # Criar buffer para o PDF
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            
            # Desenhar a etiqueta
            self._draw_transul_label(c, xml_data, pedido_number, area_code)
            
            c.showPage()
            c.save()
            buffer.seek(0)
            
            logger.info("Etiqueta Transul gerada com sucesso")
            return buffer
            
        except Exception as e:
            logger.error(f"Erro ao gerar etiqueta Transul: {str(e)}")
            raise
    
    def _draw_transul_label(self, c, xml_data, pedido_number, area_code):
        """Desenha a etiqueta completa no modelo Transul"""
        
        # Posição inicial Y (começa do topo)
        y_pos = self.page_height - 40 * mm
        
        # 1. Header da Transportadora - Transul
        self._draw_header(c, y_pos)
        y_pos -= 25 * mm
        
        # 2. ID e QR Code
        y_pos = self._draw_id_section(c, xml_data, y_pos)
        y_pos -= 15 * mm
        
        # 3. NF Section (fundo preto)
        y_pos = self._draw_nf_section(c, xml_data, y_pos)
        y_pos -= 15 * mm
        
        # 4. Pedido Section (fundo preto)
        y_pos = self._draw_pedido_section(c, pedido_number or xml_data.get('numero_nf', '24441'), y_pos)
        y_pos -= 15 * mm
        
        # 5. Remetente Section (fundo preto)
        y_pos = self._draw_remetente_section(c, xml_data, y_pos)
        y_pos -= 25 * mm
        
        # 6. Destinatário e Endereço
        y_pos = self._draw_destinatario_section(c, xml_data, y_pos)
        y_pos -= 25 * mm
        
        # 7. Cidade/UF Section (fundo preto)
        y_pos = self._draw_cidade_section(c, xml_data, y_pos)
        y_pos -= 15 * mm
        
        # 8. Peso Section (fundo preto)
        y_pos = self._draw_peso_section(c, xml_data, y_pos)
        y_pos -= 15 * mm
        
        # 9. Volume Section (fundo preto)
        y_pos = self._draw_volume_section(c, xml_data, y_pos)
        y_pos -= 50 * mm
        
        # 10. Área (canto inferior direito)
        self._draw_area_section(c, area_code)
        
        # 11. Footer
        self._draw_footer(c)
    
    def _draw_header(self, c, y_pos):
        """Desenha o cabeçalho Transul Transporte"""
        # Logo/Nome da empresa
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredText(self.page_width / 2, y_pos, "Transul")
        
        c.setFont("Helvetica", 12)
        c.drawCentredText(self.page_width / 2, y_pos - 15, "TRANSPORTE")
    
    def _draw_id_section(self, c, xml_data, y_pos):
        """Desenha seção do ID e QR Code"""
        # ID text
        c.setFont("Helvetica", 12)
        invoice_key = xml_data.get('chave_acesso', '11340-001-001-001')
        formatted_id = f"ID: {invoice_key[:5]}-{invoice_key[5:8]}-{invoice_key[8:11]}-{invoice_key[11:14]}"
        c.drawString(self.margin, y_pos, formatted_id)
        
        # QR Code
        qr_data = xml_data.get('chave_acesso', '11340001001001')
        self._draw_qr_code(c, qr_data, self.page_width - 60 * mm, y_pos - 20, 40 * mm)
        
        return y_pos
    
    def _draw_nf_section(self, c, xml_data, y_pos):
        """Desenha seção NF com fundo preto"""
        # Fundo preto
        c.setFillColor(colors.black)
        c.rect(self.margin, y_pos - 12, self.content_width, 12 * mm, fill=1)
        
        # Texto branco
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        nf_number = xml_data.get('numero_nf', '11340')
        c.drawString(self.margin + 5, y_pos - 8, f"NF: {nf_number}")
        
        # Voltar cor para preto
        c.setFillColor(colors.black)
        return y_pos
    
    def _draw_pedido_section(self, c, pedido_number, y_pos):
        """Desenha seção Pedido com fundo preto"""
        # Fundo preto
        c.setFillColor(colors.black)
        c.rect(self.margin, y_pos - 12, self.content_width, 12 * mm, fill=1)
        
        # Texto branco
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(self.margin + 5, y_pos - 8, f"Pedido: {pedido_number}")
        
        # Voltar cor para preto
        c.setFillColor(colors.black)
        return y_pos
    
    def _draw_remetente_section(self, c, xml_data, y_pos):
        """Desenha seção Remetente com fundo preto"""
        # Fundo preto
        c.setFillColor(colors.black)
        c.rect(self.margin, y_pos - 12, self.content_width, 12 * mm, fill=1)
        
        # Texto branco
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        remetente = xml_data.get('nome_emitente', 'REAL SINALIZACAO INDUSTRIA COMERCIO')
        # Truncar se muito longo
        if len(remetente) > 40:
            remetente = remetente[:37] + "..."
        c.drawString(self.margin + 5, y_pos - 8, f"Remetente: {remetente}")
        
        # Voltar cor para preto
        c.setFillColor(colors.black)
        return y_pos
    
    def _draw_destinatario_section(self, c, xml_data, y_pos):
        """Desenha informações do destinatário"""
        c.setFont("Helvetica", 12)
        
        # Destinatário
        destinatario = xml_data.get('destinatario_razao', 'FORT CLEAN - DISTRIBUIDORA LTDA')
        c.drawString(self.margin, y_pos, f"Destinatário: {destinatario}")
        
        # Endereço
        endereco_parts = []
        if xml_data.get('destinatario_logradouro'):
            endereco_parts.append(xml_data.get('destinatario_logradouro'))
        if xml_data.get('destinatario_cidade'):
            endereco_parts.append(xml_data.get('destinatario_cidade'))
        if xml_data.get('destinatario_uf'):
            endereco_parts.append(xml_data.get('destinatario_uf'))
        if xml_data.get('destinatario_cep'):
            endereco_parts.append(f"CEP: {xml_data.get('destinatario_cep')}")
        
        endereco = ", ".join(endereco_parts) or "RUA PIAUI, IMPERATRIZ - MA, CEP: 65907100"
        c.drawString(self.margin, y_pos - 15, f"Endereço: {endereco}")
        
        return y_pos
    
    def _draw_cidade_section(self, c, xml_data, y_pos):
        """Desenha seção Cidade/UF com fundo preto"""
        # Fundo preto
        c.setFillColor(colors.black)
        c.rect(self.margin, y_pos - 12, self.content_width, 12 * mm, fill=1)
        
        # Texto branco
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        cidade = xml_data.get('destinatario_cidade', 'IMPERATRIZ')
        uf = xml_data.get('destinatario_uf', 'MA')
        c.drawString(self.margin + 5, y_pos - 8, f"Cidade/UF: {cidade} {uf}")
        
        # Voltar cor para preto
        c.setFillColor(colors.black)
        return y_pos
    
    def _draw_peso_section(self, c, xml_data, y_pos):
        """Desenha seção Peso com fundo preto"""
        # Fundo preto para peso
        peso_width = 60 * mm
        c.setFillColor(colors.black)
        c.rect(self.margin, y_pos - 12, peso_width, 12 * mm, fill=1)
        
        # Texto branco peso
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        peso = xml_data.get('peso_bruto', '1225.000')
        c.drawString(self.margin + 5, y_pos - 8, f"Peso: {peso}")
        
        # Transportadora (texto normal)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 12)
        c.drawString(self.margin + peso_width + 10, y_pos - 8, "Transportadora: TRANSUL TRANSPORTE")
        
        return y_pos
    
    def _draw_volume_section(self, c, xml_data, y_pos):
        """Desenha seção Volume com fundo preto"""
        # Fundo preto
        volume_width = 60 * mm
        c.setFillColor(colors.black)
        c.rect(self.margin, y_pos - 12, volume_width, 12 * mm, fill=1)
        
        # Texto branco
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 14)
        volumes = xml_data.get('quantidade_volumes', '62')
        c.drawString(self.margin + 5, y_pos - 8, f"Volume: 1/{volumes}")
        
        # Voltar cor para preto
        c.setFillColor(colors.black)
        return y_pos
    
    def _draw_area_section(self, c, area_code):
        """Desenha seção ÁREA no canto inferior direito"""
        # Posição no canto inferior direito
        area_x = self.page_width - 60 * mm
        area_y = 60 * mm
        area_width = 40 * mm
        area_height = 30 * mm
        
        # Fundo preto
        c.setFillColor(colors.black)
        c.rect(area_x, area_y, area_width, area_height, fill=1)
        
        # Texto branco
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 12)
        c.drawCentredText(area_x + area_width/2, area_y + area_height - 10, "ÁREA")
        
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredText(area_x + area_width/2, area_y + 8, area_code)
        
        # Voltar cor para preto
        c.setFillColor(colors.black)
    
    def _draw_footer(self, c):
        """Desenha rodapé com marca CROSS WMS"""
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.grey)
        c.drawString(self.margin, 30 * mm, "CROSS WMS")
    
    def _draw_qr_code(self, c, data, x, y, size):
        """Desenha QR code na posição especificada"""
        try:
            # Criar QR code
            qr_code = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=3,
                border=1,
            )
            qr_code.add_data(data)
            qr_code.make(fit=True)
            
            # Converter para imagem
            img = qr_code.make_image(fill_color="black", back_color="white")
            
            # Salvar temporariamente
            temp_buffer = BytesIO()
            img.save(temp_buffer, format='PNG')
            temp_buffer.seek(0)
            
            # Desenhar no canvas
            c.drawImage(temp_buffer, x, y, width=size, height=size)
            
        except Exception as e:
            logger.warning(f"Erro ao gerar QR code: {e}")
            # Desenhar retângulo placeholder
            c.rect(x, y, size, size, stroke=1, fill=0)
            c.setFont("Helvetica", 8)
            c.drawCentredText(x + size/2, y + size/2, "QR")


def generate_label_from_database_xml(xml_record, pedido_number: str = None, area_code: str = "01") -> BytesIO:
    """
    Função utilitária para gerar etiqueta a partir de um registro XML do banco
    
    Args:
        xml_record: Registro XML do banco (ImportedXML ou XMLFile)
        pedido_number: Número do pedido (opcional)
        area_code: Código da área (padrão: "01")
        
    Returns:
        BytesIO contendo o PDF da etiqueta
    """
    try:
        generator = TransulLabelGenerator()
        
        xml_content = xml_record.xml_content
        if not xml_content:
            raise ValueError("XML content not found in record")
        
        # Usar o número NF como pedido se não fornecido
        if not pedido_number:
            pedido_number = getattr(xml_record, 'numero_nf', None) or xml_record.invoice_key[:5]
        
        return generator.generate_transport_label(xml_content, pedido_number, area_code)
        
    except Exception as e:
        logger.error(f"Erro ao gerar etiqueta do banco: {str(e)}")
        raise