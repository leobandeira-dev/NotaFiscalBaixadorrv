"""
Gerador de etiqueta que replica exatamente o layout Transul da imagem de referência
Layout específico baseado na análise visual da imagem fornecida com styling harmonioso
"""

import io
import os
import logging
from datetime import datetime
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
    
    def _generate_label_id(self, numero_nf, volume_number):
        """
        Gera ID único da etiqueta no formato: NumeroNF-Data-Hora-Volume
        Exemplo: 417549-2012-0614-3 (NF 417549 - 20/12 - 06:14 - Volume 3)
        """
        now = datetime.now()
        
        # Extrair apenas números da NF
        nf_numero = ''.join(filter(str.isdigit, str(numero_nf)))
        
        # Formato: DDMM (dia/mês)
        data_str = now.strftime("%d%m")
        
        # Formato: HHMM (hora:minuto)
        hora_str = now.strftime("%H%M")
        
        # Volume com 1 dígito
        volume_str = str(volume_number)
        
        # Combinar com separadores: NF-Data-Hora-Volume
        label_id = f"{nf_numero}-{data_str}-{hora_str}-{volume_str}"
        
        return label_id
    
    def _draw_company_header_with_logo(self, canvas, x, y, width, height, company_name, logo_path):
        """
        Desenha cabeçalho da empresa com logo integrada - SEM container em contraste
        
        Args:
            canvas: Canvas do ReportLab
            x, y: Posição do cabeçalho
            width, height: Dimensões do cabeçalho
            company_name: Nome da empresa
            logo_path: Caminho da logo
        """
        try:
            from reportlab.lib.utils import ImageReader
            
            # SEM fundo contrastante - logo deve aparecer diretamente
            # Apenas uma borda sutil para delimitar a área
            canvas.setStrokeColor(self.colors['light_gray'])
            canvas.setLineWidth(1)
            canvas.rect(x, y, width, height, fill=0, stroke=1)
            
            # Verificar se logo existe
            if logo_path and os.path.exists(logo_path):
                # Dimensões da logo (40% da largura, centralizada)
                logo_width = width * 0.4
                logo_height = height * 0.9
                logo_x = x + (width * 0.05)  # 5% de margem esquerda
                logo_y = y + (height - logo_height) / 2
                
                # Desenhar a logo da empresa SEM fundo
                canvas.drawImage(ImageReader(logo_path), logo_x, logo_y, 
                               width=logo_width, height=logo_height, 
                               preserveAspectRatio=True, mask='auto')
                
                # Nome da empresa ao lado da logo
                text_x = logo_x + logo_width + (width * 0.05)
                text_width = width - (text_x - x) - (width * 0.05)
                
                # Texto da empresa em preto para contraste com fundo branco
                canvas.setFillColor(self.colors['black'])
                canvas.setFont(self.fonts['header_large'][0], self.fonts['header_large'][1])
                
                # Centralizar texto verticalmente
                text_y = y + (height / 2) - (self.fonts['header_large'][1] / 2)
                canvas.drawString(text_x, text_y, company_name[:20])
                
            else:
                # Se não há logo, desenhar apenas o nome da empresa centralizado
                canvas.setFillColor(self.colors['black'])
                canvas.setFont(self.fonts['header_large'][0], self.fonts['header_large'][1])
                
                # Centralizar texto
                text_x = x + width / 2
                text_y = y + (height / 2) - (self.fonts['header_large'][1] / 2)
                canvas.drawCentredString(text_x, text_y, company_name[:25])
            
        except Exception as e:
            logger.error(f"Erro ao desenhar cabeçalho com logo: {e}")
            # Fallback: desenhar apenas texto simples
            canvas.setFillColor(self.colors['black'])
            canvas.setFont(self.fonts['header_large'][0], self.fonts['header_large'][1])
            text_x = x + width / 2
            text_y = y + (height / 2) - (self.fonts['header_large'][1] / 2)
            canvas.drawCentredString(text_x, text_y, company_name[:25])
    
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
        return self.generate_transul_exact_label_with_company(
            xml_content, pedido_number, area_code, company_logo_path, volume_info,
            'SUA EMPRESA', 'TRANSPORTE'
        )
    
    def generate_transul_exact_label_with_company(self, xml_content, pedido_number, area_code="01", 
                                                company_logo_path=None, volume_info="1/1",
                                                company_name="SUA EMPRESA", company_subtitle="TRANSPORTE"):
        """
        Gera etiqueta com layout exato usando configurações personalizadas da empresa
        
        Args:
            xml_content: Conteúdo XML da NFe
            pedido_number: Número do pedido
            area_code: Código da área
            company_logo_path: Caminho da logo da empresa
            volume_info: Informação do volume (ex: "1/2")
            company_name: Nome da empresa configurada pelo usuário
            company_subtitle: Subtítulo da empresa
            
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
                                          company_logo_path, volume_info, 
                                          company_name, company_subtitle)
            
            # Finalizar PDF
            c.save()
            buffer.seek(0)
            
            logger.info(f"Etiqueta Transul exata gerada: {len(buffer.getvalue())} bytes")
            return buffer
            
        except Exception as e:
            logger.error(f"Erro ao gerar etiqueta Transul exata: {e}")
            return None
    
    def _draw_transul_exact_layout(self, c, xml_data, pedido_number, area_code, 
                                 company_logo_path, volume_info, company_name="SUA EMPRESA", 
                                 company_subtitle="TRANSPORTE"):
        """Desenha o layout exato conforme a imagem de referência com styling harmonioso"""
        
        # Posições baseadas na análise da imagem
        y_start = self.page_height - self.margin
        current_y = y_start
        
        # Espaço de 4mm após a borda antes do primeiro container
        current_y -= 4 * mm
        
        # 1. CABEÇALHO EMPRESA COM LOGO - Centralizado
        header_height = 15 * mm
        
        # Se há logo, desenhar cabeçalho com logo
        # Construir caminho completo se apenas filename foi fornecido
        full_logo_path = None
        if company_logo_path:
            if os.path.exists(company_logo_path):
                full_logo_path = company_logo_path
            else:
                # Tentar construir caminho completo
                full_path = os.path.join('static', 'uploads', 'logos', company_logo_path)
                if os.path.exists(full_path):
                    full_logo_path = full_path
        
        if full_logo_path:
            self._draw_company_header_with_logo(c, self.margin, current_y - header_height, 
                                              self.content_width, header_height, 
                                              company_name, full_logo_path)
        else:
            # Cabeçalho apenas com texto
            self._draw_styled_text_section(
                c, self.margin, current_y - header_height, self.content_width, header_height,
                company_name, self.fonts['header_large'], 
                self.colors['white'], self.colors['black'], center_text=True
            )
        
        # Subtítulo da empresa
        subtitle_height = 8 * mm
        current_y -= header_height
        self._draw_styled_text_section(
            c, self.margin, current_y - subtitle_height, self.content_width, subtitle_height,
            company_subtitle, self.fonts['body_regular'], 
            self.colors['white'], self.colors['dark_gray'], center_text=True
        )
        current_y -= subtitle_height + self.section_spacing
        
        # 2. LINHA ID + QR CODE
        id_height = 12 * mm
        id_width = self.content_width * 0.65
        qr_width = self.content_width * 0.30
        
        # Gerar ID único estruturado
        volume_number = volume_info.split('/')[0] if '/' in volume_info else '1'
        unique_label_id = self._generate_label_id(xml_data.get('numero_nf', 'N/A'), volume_number)
        
        # ID no lado esquerdo
        id_text = f"ID: {unique_label_id}"
        self._draw_styled_text_section(
            c, self.margin, current_y - id_height, id_width, id_height,
            id_text, self.fonts['body_regular'], 
            self.colors['white'], self.colors['black'], center_text=False
        )
        
        # QR Code no lado direito (reflete o ID da etiqueta)
        self._draw_qr_code(c, self.margin + id_width + (self.content_width * 0.05), 
                          current_y - id_height, qr_width, id_height, unique_label_id)
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
        remetente_nome = xml_data.get('nome_emitente', xml_data.get('emitente_nome', 'N/A'))
        if remetente_nome and remetente_nome != 'N/A' and len(remetente_nome) > 30:
            # Pegar primeira palavra + última palavra se muito longo
            palavras = remetente_nome.split()
            if len(palavras) > 1:
                remetente_resumido = f"{palavras[0]} {palavras[-1]}"
            else:
                remetente_resumido = remetente_nome[:30]
        else:
            remetente_resumido = remetente_nome or 'N/A'
            
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
            f"AREA\n{area_code}", self.fonts['body_bold'], 
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
        """Desenha QR code estilizado com geração confiável"""
        try:
            import qrcode
            from reportlab.lib.utils import ImageReader
            import io
            
            # Criar QR code com configurações otimizadas
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(str(data) if data else "ID-NOT-AVAILABLE")
            qr.make(fit=True)
            
            # Gerar imagem do QR code
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Converter para buffer BytesIO
            img_buffer = io.BytesIO()
            qr_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            # Calcular tamanho e posição
            qr_size = min(width, height) * 0.85
            qr_x = x + (width - qr_size) / 2
            qr_y = y + (height - qr_size) / 2
            
            # Desenhar QR code no canvas
            c.drawImage(ImageReader(img_buffer), qr_x, qr_y, qr_size, qr_size)
            
            logger.info(f"QR code gerado com sucesso para dados: {data}")
            
        except Exception as e:
            logger.error(f"Erro ao gerar QR code: {e}")
            # Fallback: desenhar borda com texto QR
            c.setStrokeColor(self.colors['black'])
            c.setFillColor(self.colors['light_gray'])
            c.rect(x, y, width, height, fill=1, stroke=1)
            
            # Texto QR centralizado
            c.setFillColor(self.colors['black'])
            c.setFont(*self.fonts['body_small'])
            text_x = x + width / 2
            text_y = y + height / 2
            c.drawCentredString(text_x, text_y, "QR")

def generate_transul_exact_label_from_xml(xml_content, pedido_number=None, area_code="01", 
                                        company_logo_path=None, volume_info="1/1",
                                        paper_width_mm=100, paper_height_mm=150,
                                        company_name="SUA EMPRESA", company_subtitle="TRANSPORTE"):
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
        company_name: Nome da empresa configurada pelo usuário
        company_subtitle: Subtítulo da empresa
        
    Returns:
        BytesIO buffer com PDF estilizado
    """
    generator = TransulExactLayoutGenerator(paper_width_mm, paper_height_mm)
    
    # Atualizar método para aceitar parâmetros da empresa
    return generator.generate_transul_exact_label_with_company(
        xml_content, pedido_number, area_code, company_logo_path, volume_info,
        company_name, company_subtitle
    )