"""
Gerador de etiqueta que replica exatamente o layout Transul da imagem de referência
Layout específico baseado na análise visual da imagem fornecida com styling harmonioso
"""

import io
import logging
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from xml_processor import extract_xml_data

logger = logging.getLogger(__name__)

class TransulExactLayoutGenerator:
    """Gerador que replica o layout exato da etiqueta Transul com styling harmonioso profissional"""
    
    def __init__(self, paper_width_mm=100, paper_height_mm=150):
        """
        Inicializa gerador com dimensões específicas e configurações de design
        
        Args:
            paper_width_mm: Largura em milímetros
            paper_height_mm: Altura em milímetros
        """
        self.paper_width_mm = paper_width_mm
        self.paper_height_mm = paper_height_mm
        self.page_width = paper_width_mm * mm
        self.page_height = paper_height_mm * mm
        self.margin = 5 * mm
        self.content_width = self.page_width - (2 * self.margin)
        self.padding_internal = 3 * mm
        self.section_spacing = 2 * mm
        
        # Paleta de cores harmoniosa profissional
        self.colors = {
            'black': colors.Color(0, 0, 0),
            'white': colors.Color(1, 1, 1),
            'dark_gray': colors.Color(0.3, 0.3, 0.3),
            'light_gray': colors.Color(0.95, 0.95, 0.95),
            'border_gray': colors.Color(0.7, 0.7, 0.7)
        }
        
        # Sistema de tipografia hierárquica
        self.fonts = {
            'header_large': ('Helvetica-Bold', 16),
            'header_medium': ('Helvetica-Bold', 12),
            'body_bold': ('Helvetica-Bold', 10),
            'body_regular': ('Helvetica', 9),
            'body_small': ('Helvetica', 8),
            'footer': ('Helvetica', 7)
        }
        
        # Configurações de design
        self.corner_radius = 2  # Cantos arredondados sutis
        self.border_thickness = 1
    
    def _draw_rounded_rect(self, canvas, x, y, width, height, bg_color, border_color=None, radius=None):
        """
        Desenha retângulo com cantos arredondados e styling profissional
        
        Args:
            canvas: Canvas do ReportLab
            x, y: Posição
            width, height: Dimensões
            bg_color: Cor de fundo
            border_color: Cor da borda (opcional)
            radius: Raio dos cantos (opcional, usa padrão se None)
        """
        if radius is None:
            radius = self.corner_radius
            
        # Fundo
        canvas.setFillColor(bg_color)
        canvas.roundRect(x, y, width, height, radius, fill=1, stroke=0)
        
        # Borda opcional
        if border_color:
            canvas.setStrokeColor(border_color)
            canvas.setLineWidth(self.border_thickness)
            canvas.roundRect(x, y, width, height, radius, fill=0, stroke=1)
    
    def _draw_styled_text_section(self, canvas, x, y, width, height, text, font_config, 
                                 bg_color, text_color, border_color=None, center_text=True):
        """
        Desenha seção de texto com styling harmonioso baseado na referência
        
        Args:
            canvas: Canvas do ReportLab
            x, y: Posição da seção
            width, height: Dimensões da seção
            text: Texto a ser exibido
            font_config: Tupla (fonte, tamanho)
            bg_color: Cor de fundo
            text_color: Cor do texto
            border_color: Cor da borda (opcional)
            center_text: Se deve centralizar o texto
        """
        # Desenhar fundo com cantos arredondados
        self._draw_rounded_rect(canvas, x, y, width, height, bg_color, border_color)
        
        # Configurar texto
        canvas.setFont(*font_config)
        canvas.setFillColor(text_color)
        
        # Calcular posição do texto
        text_y = y + height/2 - font_config[1]/2
        
        if center_text:
            text_width = canvas.stringWidth(text, *font_config)
            text_x = x + (width - text_width) / 2
        else:
            text_x = x + self.padding_internal
            
        canvas.drawString(text_x, text_y, text)
    
    def _draw_multi_line_text_section(self, canvas, x, y, width, height, lines, font_config,
                                     bg_color, text_color, border_color=None):
        """
        Desenha seção com múltiplas linhas de texto, otimizada para destinatário
        
        Args:
            canvas: Canvas do ReportLab
            x, y: Posição da seção
            width, height: Dimensões da seção
            lines: Lista de linhas de texto
            font_config: Tupla (fonte, tamanho)
            bg_color: Cor de fundo
            text_color: Cor do texto
            border_color: Cor da borda (opcional)
        """
        # Desenhar fundo
        self._draw_rounded_rect(canvas, x, y, width, height, bg_color, border_color)
        
        # Configurar texto
        canvas.setFont(*font_config)
        canvas.setFillColor(text_color)
        
        # Calcular espaçamento entre linhas
        line_height = font_config[1] * 1.2
        start_y = y + height - self.padding_internal - font_config[1]
        
        # Desenhar cada linha
        for i, line in enumerate(lines):
            if line.strip():  # Apenas linhas não vazias
                text_y = start_y - (i * line_height)
                if text_y > y + self.padding_internal:  # Verificar se ainda está dentro da seção
                    canvas.drawString(x + self.padding_internal, text_y, line)
    
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
        """Desenha o layout exato conforme a imagem de referência com styling harmonioso"""
        
        # Posições baseadas na análise da imagem
        y_start = self.page_height - self.margin
        current_y = y_start
        
        # Espaço de 4mm após a borda antes do primeiro container
        current_y -= 4 * mm
        
        # 1. CABEÇALHO EMPRESA (LAF LOGISTICA / OPERADOR LOGISTICO) - Centralizado
        header_height = 15 * mm
        self._draw_styled_text_section(
            c, self.margin, current_y - header_height, self.content_width, header_height,
            "LAF LOGISTICA", self.fonts['header_large'], 
            self.colors['white'], self.colors['black'], center_text=True
        )
        
        # Subtítulo OPERADOR LOGISTICO
        subtitle_height = 8 * mm
        current_y -= header_height
        self._draw_styled_text_section(
            c, self.margin, current_y - subtitle_height, self.content_width, subtitle_height,
            "OPERADOR LOGISTICO", self.fonts['body_regular'], 
            self.colors['white'], self.colors['dark_gray'], center_text=True
        )
        current_y -= subtitle_height + self.section_spacing
        
        # 2. LINHA ID + QR CODE
        id_height = 12 * mm
        id_width = self.content_width * 0.65
        qr_width = self.content_width * 0.30
        
        # ID no lado esquerdo
        id_text = f"ID: {xml_data.get('numero_nf', 'N/A')}-{xml_data.get('serie', '001')}-001-001"
        self._draw_styled_text_section(
            c, self.margin, current_y - id_height, id_width, id_height,
            id_text, self.fonts['body_regular'], 
            self.colors['white'], self.colors['black'], center_text=False
        )
        
        # QR Code no lado direito
        self._draw_qr_code(c, self.margin + id_width + (self.content_width * 0.05), 
                          current_y - id_height, qr_width, id_height, volume_info)
        current_y -= id_height + self.section_spacing
        
        # 3. NF - Fundo preto com texto branco
        nf_height = 10 * mm
        nf_text = f"NF: {xml_data.get('numero_nf', 'N/A')}"
        self._draw_styled_text_section(
            c, self.margin, current_y - nf_height, self.content_width, nf_height,
            nf_text, self.fonts['body_bold'], 
            self.colors['black'], self.colors['white'], center_text=False
        )
        current_y -= nf_height + self.section_spacing
        
        # 4. PEDIDO - Fundo preto com texto branco
        pedido_height = 10 * mm
        pedido_text = f"Pedido: {pedido_number or 'N/A'}"
        self._draw_styled_text_section(
            c, self.margin, current_y - pedido_height, self.content_width, pedido_height,
            pedido_text, self.fonts['body_bold'], 
            self.colors['black'], self.colors['white'], center_text=False
        )
        current_y -= pedido_height + self.section_spacing
        
        # 5. REMETENTE - Fundo preto com texto branco
        remetente_height = 10 * mm
        # Resumir nome do remetente para caber no container
        remetente_nome = xml_data.get('emitente_nome', 'N/A')
        if len(remetente_nome) > 30:
            # Pegar primeira palavra + última palavra se muito longo
            palavras = remetente_nome.split()
            if len(palavras) > 1:
                remetente_resumido = f"{palavras[0]} {palavras[-1]}"
            else:
                remetente_resumido = remetente_nome[:30]
        else:
            remetente_resumido = remetente_nome
            
        remetente_text = f"Remetente: {remetente_resumido}"
        self._draw_styled_text_section(
            c, self.margin, current_y - remetente_height, self.content_width, remetente_height,
            remetente_text, self.fonts['body_bold'], 
            self.colors['black'], self.colors['white'], center_text=False
        )
        current_y -= remetente_height + self.section_spacing
        
        # 6. DESTINATÁRIO - Fundo branco com borda
        destinatario_height = 20 * mm
        destinatario_width = self.content_width * 0.70
        area_width = self.content_width * 0.25
        
        # Resumir nome do destinatário para caber no container
        dest_nome = xml_data.get('destinatario_nome', 'N/A')
        if len(dest_nome) > 25:
            # Pegar primeira palavra + última palavra se muito longo
            palavras = dest_nome.split()
            if len(palavras) > 1:
                dest_resumido = f"{palavras[0]} {palavras[-1]}"
            else:
                dest_resumido = dest_nome[:25]
        else:
            dest_resumido = dest_nome
        
        # Preparar endereço completo de entrega
        endereco = xml_data.get('destinatario_endereco', '')
        bairro = xml_data.get('destinatario_bairro', '')
        cidade = xml_data.get('destinatario_cidade', '')
        uf = xml_data.get('destinatario_uf', '')
        cep = xml_data.get('destinatario_cep', '')
        
        # Montar endereço completo
        endereco_completo = endereco
        if bairro and endereco:
            endereco_completo = f"{endereco}, {bairro}"
        elif bairro:
            endereco_completo = bairro
            
        # Preparar linhas do destinatário com endereço completo
        dest_lines = [
            f"DESTINATÁRIO: {dest_resumido}",
            f"Endereço: {endereco_completo[:30]}",
            f"{cidade}/{uf} - CEP: {cep}"
        ]
        
        # Destinatário
        self._draw_multi_line_text_section(
            c, self.margin, current_y - destinatario_height, destinatario_width, destinatario_height,
            dest_lines, self.fonts['body_regular'], 
            self.colors['white'], self.colors['black'], self.colors['border_gray']
        )
        
        # ÁREA no lado direito
        area_x = self.margin + destinatario_width + (self.content_width * 0.05)
        self._draw_styled_text_section(
            c, area_x, current_y - destinatario_height, area_width, destinatario_height,
            f"ÁREA\n{area_code}", self.fonts['body_bold'], 
            self.colors['black'], self.colors['white'], center_text=True
        )
        current_y -= destinatario_height + self.section_spacing
        
        # 7. CIDADE/UF - Fundo preto
        cidade_height = 10 * mm
        cidade_text = f"Cidade/UF: {xml_data.get('destinatario_cidade', 'N/A')} {xml_data.get('destinatario_uf', 'N/A')}"
        self._draw_styled_text_section(
            c, self.margin, current_y - cidade_height, self.content_width, cidade_height,
            cidade_text, self.fonts['body_bold'], 
            self.colors['black'], self.colors['white'], center_text=False
        )
        current_y -= cidade_height + self.section_spacing
        
        # 8. PESO E VOLUME - Layout horizontal
        peso_volume_height = 10 * mm
        peso_width = self.content_width * 0.60
        volume_width = self.content_width * 0.35
        
        # Peso
        peso_text = f"Peso: {xml_data.get('peso_bruto', '0')}kg"
        self._draw_styled_text_section(
            c, self.margin, current_y - peso_volume_height, peso_width, peso_volume_height,
            peso_text, self.fonts['body_bold'], 
            self.colors['black'], self.colors['white'], center_text=False
        )
        
        # Volume
        volume_x = self.margin + peso_width + (self.content_width * 0.05)
        volume_text = f"Volume: {volume_info}"
        self._draw_styled_text_section(
            c, volume_x, current_y - peso_volume_height, volume_width, peso_volume_height,
            volume_text, self.fonts['body_bold'], 
            self.colors['black'], self.colors['white'], center_text=False
        )
        current_y -= peso_volume_height + self.section_spacing
        
        # 9. RODAPÉ - CROSS WMS (canto inferior esquerdo)
        footer_y = self.margin + 5 * mm
        c.setFont(*self.fonts['footer'])
        c.setFillColor(self.colors['dark_gray'])
        c.drawString(self.margin, footer_y, "CROSS WMS")
    
    def _draw_qr_code(self, c, x, y, width, height, data):
        """Desenha QR code estilizado"""
        try:
            import qrcode
            qr = qrcode.QRCode(version=1, box_size=2, border=1)
            qr.add_data(data or "N/A")
            qr.make(fit=True)
            
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Converter para ReportLab
            from reportlab.lib.utils import ImageReader
            qr_size = min(width, height) * 0.8
            qr_x = x + (width - qr_size) / 2
            qr_y = y + (height - qr_size) / 2
            
            c.drawImage(ImageReader(qr_img), qr_x, qr_y, qr_size, qr_size)
            
        except Exception as e:
            # Fallback: desenhar retângulo com texto
            self._draw_styled_text_section(
                c, x, y, width, height, "QR", self.fonts['body_small'],
                self.colors['light_gray'], self.colors['black'], center_text=True
            )

def generate_transul_exact_label_from_xml(xml_content, pedido_number=None, area_code="01", 
                                        company_logo_path=None, volume_info="1/1",
                                        paper_width_mm=100, paper_height_mm=150):
    """
    Função wrapper para gerar etiqueta Transul exata com styling harmonioso
    
    Args:
        xml_content: Conteúdo XML da NFe
        pedido_number: Número do pedido
        area_code: Código da área
        company_logo_path: Caminho da logo da empresa
        volume_info: Informação do volume
        paper_width_mm: Largura do papel em mm
        paper_height_mm: Altura do papel em mm
        
    Returns:
        BytesIO buffer com PDF estilizado
    """
    generator = TransulExactLayoutGenerator(paper_width_mm, paper_height_mm)
    return generator.generate_transul_exact_label(
        xml_content, pedido_number, area_code, company_logo_path, volume_info
    )