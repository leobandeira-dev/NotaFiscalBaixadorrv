"""
Gerador de Etiquetas de Transporte Verdadeiramente Responsivo
Sistema que adapta completamente o layout ao tamanho do papel configurado
"""

import logging
import os
import qrcode
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class ResponsiveTransportLabelGenerator:
    """Gerador de etiquetas de transporte com layout verdadeiramente responsivo"""
    
    def __init__(self, company_name="SUA EMPRESA", company_subtitle="TRANSPORTE", 
                 paper_width_mm=100, paper_height_mm=150, layout_style="layout1"):
        """
        Inicializa o gerador com configurações responsivas
        
        Args:
            company_name: Nome da empresa para o cabeçalho
            company_subtitle: Subtítulo da empresa
            paper_width_mm: Largura do papel em milímetros
            paper_height_mm: Altura do papel em milímetros
            layout_style: Estilo de layout ("layout1" = moderno, "layout2" = alto contraste, "transul" = estilo Transul profissional)
        """
        self.company_name = company_name
        self.company_subtitle = company_subtitle
        self.paper_width_mm = paper_width_mm
        self.paper_height_mm = paper_height_mm
        self.layout_style = layout_style
        self.page_width = paper_width_mm * mm
        self.page_height = paper_height_mm * mm
        
        # Sistema de margem responsiva (3-8% da largura)
        margin_percent = 0.05
        self.margin = max(2 * mm, min(self.page_width * margin_percent, 6 * mm))
        
        # Área de conteúdo disponível
        self.content_width = self.page_width - (2 * self.margin)
        self.content_height = self.page_height - (2 * self.margin)
        
        # Sistema de escala baseado em papel padrão 100x150mm
        self.width_scale = paper_width_mm / 100.0
        self.height_scale = paper_height_mm / 150.0
        self.scale_factor = min(self.width_scale, self.height_scale)
        
        # Sistema de fontes responsivas
        self._setup_responsive_fonts()
        
        # Sistema de espaçamentos responsivos
        self._setup_responsive_spacing()
        
        logger.info(f"Gerador responsivo: {paper_width_mm}x{paper_height_mm}mm, escala: {self.scale_factor:.2f}")
    
    def _setup_responsive_fonts(self):
        """Configura tamanhos de fonte responsivos"""
        base_font = 8
        self.fonts = {
            'company_name': max(10, int(base_font * 2.2 * self.scale_factor)),
            'company_sub': max(7, int(base_font * 1.2 * self.scale_factor)),
            'section_header': max(8, int(base_font * 1.4 * self.scale_factor)),
            'section_content': max(7, int(base_font * 1.1 * self.scale_factor)),
            'id_text': max(6, int(base_font * 0.9 * self.scale_factor)),
            'normal_text': max(7, int(base_font * self.scale_factor)),
            'small_text': max(6, int(base_font * 0.8 * self.scale_factor))
        }
    
    def _setup_responsive_spacing(self):
        """Configura espaçamentos responsivos com melhor distribuição"""
        base_spacing = 4 * mm  # Aumentado para mais espaço entre seções
        self.spacing = {
            'section': max(3 * mm, base_spacing * self.scale_factor),  # Espaço entre containers
            'line': max(2 * mm, base_spacing * 0.8 * self.scale_factor),  # Espaço entre linhas
            'field': max(1 * mm, base_spacing * 0.5 * self.scale_factor),
            'header': max(4 * mm, base_spacing * 1.3 * self.scale_factor)
        }
    
    def generate_transport_label(self, xml_content: str, pedido_number: str = None, 
                               area_code: str = "01", company_logo_path: str = None) -> BytesIO:
        """
        Gera etiqueta de transporte responsiva
        
        Args:
            xml_content: Conteúdo XML da NFe
            pedido_number: Número do pedido (opcional)
            area_code: Código da área (padrão: "01")
            company_logo_path: Caminho para logo da empresa (opcional)
            
        Returns:
            BytesIO contendo o PDF da etiqueta
        """
        try:
            # Parse XML
            from xml_processor import extract_xml_data
            xml_data = extract_xml_data(xml_content)
            
            # Criar PDF em memória
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=(self.page_width, self.page_height))
            
            # Desenhar etiqueta responsiva
            self._draw_responsive_label(c, xml_data, pedido_number, area_code, company_logo_path)
            
            # Finalizar PDF
            c.save()
            buffer.seek(0)
            
            logger.info(f"Etiqueta responsiva gerada: {self.paper_width_mm}x{self.paper_height_mm}mm")
            return buffer
            
        except Exception as e:
            logger.error(f"Erro ao gerar etiqueta responsiva: {str(e)}")
            # Return a minimal PDF instead of failing completely
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=(self.page_width, self.page_height))
            c.setFont("Helvetica", 12)
            c.drawString(50, 100, f"Erro na geração: {str(e)[:50]}")
            c.save()
            buffer.seek(0)
            return buffer
    
    def generate_transport_label_with_volume_info(self, xml_content: str, pedido_number: str = None, 
                                                area_code: str = "01", company_logo_path: str = None,
                                                volume_info: str = None, current_volume: int = 1, 
                                                total_volumes: int = 1) -> BytesIO:
        """
        Gera etiqueta de transporte com informações dinâmicas de volume (1/62, 2/62, etc.)
        
        Args:
            xml_content: Conteúdo XML da NFe
            pedido_number: Número do pedido (opcional)
            area_code: Código da área (padrão: "01")
            company_logo_path: Caminho para logo da empresa (opcional)
            volume_info: String formatada "X/Y" para exibição
            current_volume: Número do volume atual
            total_volumes: Total de volumes
            
        Returns:
            BytesIO contendo o PDF da etiqueta com numeração dinâmica
        """
        try:
            # Parse XML
            from xml_processor import extract_xml_data
            xml_data = extract_xml_data(xml_content)
            
            # Criar PDF em memória
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=(self.page_width, self.page_height))
            
            # Desenhar etiqueta com informações de volume dinâmicas
            self._draw_responsive_label_with_volume_info(c, xml_data, pedido_number, area_code, 
                                                       company_logo_path, volume_info, current_volume, total_volumes)
            
            # Finalizar PDF
            c.save()
            buffer.seek(0)
            
            logger.info(f"Etiqueta responsiva gerada com volume {volume_info}: {self.paper_width_mm}x{self.paper_height_mm}mm")
            return buffer
            
        except Exception as e:
            logger.error(f"Erro ao gerar etiqueta responsiva com volume: {str(e)}")
            # Return a minimal PDF with volume info
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=(self.page_width, self.page_height))
            c.setFont("Helvetica-Bold", 14)
            c.drawString(50, 380, f"VOLUME {volume_info}")
            c.setFont("Helvetica", 12)
            c.drawString(50, 360, f"Pedido: {pedido_number}")
            c.drawString(50, 340, f"Erro: {str(e)[:40]}")
            c.save()
            buffer.seek(0)
            return buffer
    
    def _draw_responsive_label_with_volume_info(self, c, xml_data, pedido_number, area_code, 
                                               company_logo_path, volume_info, current_volume, total_volumes):
        """Desenha etiqueta com layout responsivo e informações de volume dinâmicas"""
        
        # Usar o mesmo layout da função principal, mas modificar seção de peso/volume
        # Configurar margens e altura das seções com melhor espaçamento
        margin = 15 * self.scale_factor
        current_y = self.page_height - margin
        section_spacing = 8 * self.scale_factor  # Aumentado para mais espaço entre containers
        
        # Definir alturas das seções com melhor proporção e espaçamento
        base_section_height = self.spacing['section'] * 3  # Aumentado para containers maiores
        company_section_height = base_section_height * 1.0  # Aumentado
        id_qr_section_height = base_section_height * 1.4   # Aumentado
        nf_section_height = base_section_height * 1.0      # Aumentado
        pedido_section_height = base_section_height * 1.0  # Aumentado
        remetente_section_height = base_section_height * 1.8  # Aumentado
        destinatario_section_height = base_section_height * 2.5  # Aumentado significativamente
        cidade_section_height = base_section_height * 1.2  # Aumentado
        peso_volume_section_height = base_section_height * 1.4  # Aumentado
        
        # 1. Seção da empresa/logo
        current_y -= company_section_height
        self._draw_company_section(c, current_y, company_section_height, company_logo_path)
        current_y -= section_spacing
        
        # 2. Seção ID e QR Code
        current_y -= id_qr_section_height
        self._draw_id_qr_section(c, xml_data, current_y, id_qr_section_height)
        current_y -= section_spacing
        
        # 3. Seção NF
        current_y -= nf_section_height
        self._draw_nf_section(c, xml_data, current_y, nf_section_height)
        current_y -= section_spacing
        
        # 4. Seção Pedido
        current_y -= pedido_section_height
        self._draw_pedido_section(c, pedido_number, current_y, pedido_section_height)
        current_y -= section_spacing
        
        # 5. Seção Remetente
        current_y -= remetente_section_height
        self._draw_remetente_section(c, xml_data, current_y, remetente_section_height)
        current_y -= section_spacing
        
        # 6. Seção Destinatário
        current_y -= destinatario_section_height
        self._draw_destinatario_section(c, xml_data, current_y, destinatario_section_height)
        current_y -= section_spacing
        
        # 7. Seção Cidade/UF
        current_y -= cidade_section_height
        self._draw_cidade_section(c, xml_data, current_y, cidade_section_height)
        current_y -= section_spacing
        
        # 8. Seção Peso e Volume com informações dinâmicas
        current_y -= peso_volume_section_height
        self._draw_peso_volume_section_with_dynamic_info(c, xml_data, current_y, peso_volume_section_height, 
                                                        volume_info, current_volume, total_volumes)
        
        # 9. Seção ÁREA (canto inferior direito)
        self._draw_area_section(c, area_code)
        
        # 10. Rodapé
        self._draw_footer(c)
    
    def _draw_responsive_label(self, c, xml_data, pedido_number, area_code, company_logo_path):
        """Desenha etiqueta com layout verdadeiramente responsivo"""
        
        # Usar o mesmo sistema de espaçamento da função com volume dinâmico
        margin = 15 * self.scale_factor
        current_y = self.page_height - margin
        section_spacing = 8 * self.scale_factor  # Espaço entre containers
        
        # Definir alturas das seções com melhor proporção e espaçamento
        base_section_height = self.spacing['section'] * 3  # Containers maiores
        company_section_height = base_section_height * 1.0
        id_qr_section_height = base_section_height * 1.4
        nf_section_height = base_section_height * 1.0
        pedido_section_height = base_section_height * 1.0
        remetente_section_height = base_section_height * 1.8
        destinatario_section_height = base_section_height * 2.5  # Aumentado significativamente
        cidade_section_height = base_section_height * 1.2
        peso_volume_section_height = base_section_height * 1.4
        
        # 1. Seção da empresa/logo
        current_y -= company_section_height
        self._draw_company_section(c, current_y, company_section_height, company_logo_path)
        current_y -= section_spacing
        
        # 2. Seção ID e QR Code
        current_y -= id_qr_section_height
        self._draw_id_qr_section(c, xml_data, current_y, id_qr_section_height)
        current_y -= section_spacing
        
        # 3. Seção NF
        current_y -= nf_section_height
        self._draw_nf_section(c, xml_data, current_y, nf_section_height)
        current_y -= section_spacing
        
        # 4. Seção Pedido
        current_y -= pedido_section_height
        self._draw_pedido_section(c, pedido_number, current_y, pedido_section_height)
        current_y -= section_spacing
        
        # 5. Seção Remetente
        current_y -= remetente_section_height
        self._draw_remetente_section(c, xml_data, current_y, remetente_section_height)
        current_y -= section_spacing
        
        # 6. Seção Destinatário
        current_y -= destinatario_section_height
        self._draw_destinatario_section(c, xml_data, current_y, destinatario_section_height)
        current_y -= section_spacing
        
        # 7. Seção Cidade/UF
        current_y -= cidade_section_height
        self._draw_cidade_section(c, xml_data, current_y, cidade_section_height)
        current_y -= section_spacing
        
        # 8. Seção Peso e Volume
        current_y -= peso_volume_section_height
        self._draw_peso_volume_section(c, xml_data, current_y, peso_volume_section_height)
        
        # 9. Seção ÁREA (canto inferior direito)
        self._draw_area_section(c, area_code)
        
        # 10. Rodapé
        self._draw_footer(c)
    
    def _draw_company_section(self, c, y_pos, section_height, company_logo_path):
        """Desenha seção da empresa com altura responsiva e enquadramento baseado no layout"""
        section_y = y_pos - section_height
        
        # Aplicar enquadramento usando função unificada
        self._apply_section_frame(c, self.margin, section_y, self.content_width, section_height)
        
        # Nome da empresa
        c.setFont("Helvetica-Bold", self.fonts['company_name'])
        
        if company_logo_path and isinstance(company_logo_path, str) and os.path.exists(company_logo_path):
            # Com logo
            logo_size = min(section_height * 0.7, self.content_width * 0.15)
            logo_x = self.margin + self.spacing['field']
            logo_y = section_y + (section_height - logo_size) / 2
            
            try:
                c.drawImage(company_logo_path, logo_x, logo_y, width=logo_size, height=logo_size)
                text_x = logo_x + logo_size + 8  # margem interna
                c.drawString(text_x, section_y + section_height * 0.75, self.company_name)
                c.setFont("Helvetica", self.fonts['company_sub'])
                c.drawString(text_x, section_y + section_height * 0.35, self.company_subtitle)
            except Exception as e:
                logger.warning(f"Erro ao carregar logo: {e}")
                # Fallback sem logo - com margem interna
                margin_interna = 8
                c.drawString(self.margin + margin_interna, section_y + section_height * 0.75, self.company_name)
                c.setFont("Helvetica", self.fonts['company_sub'])
                c.drawString(self.margin + margin_interna, section_y + section_height * 0.35, self.company_subtitle)
        else:
            # Sem logo - Espaçamento vertical corrigido com margem interna
            margin_interna = 8
            c.drawString(self.margin + margin_interna, section_y + section_height * 0.75, self.company_name)
            c.setFont("Helvetica", self.fonts['company_sub'])
            c.drawString(self.margin + margin_interna, section_y + section_height * 0.35, self.company_subtitle)
        
        # Resetar cor para preto
        c.setFillColor(colors.black)
        return section_y
    
    def _apply_section_frame(self, c, x, y, width, height):
        """ENQUADRAMENTO DEFINITIVO - bordas sempre visíveis"""
        
        # Primeiro, desenhar o fundo
        if self.layout_style == "layout2":
            c.setFillColor(colors.black)
        else:
            c.setFillColor(colors.lightgrey)
        c.rect(x, y, width, height, fill=1, stroke=0)
        
        # Segundo, desenhar a borda SEMPRE
        if self.layout_style == "layout2":
            c.setStrokeColor(colors.white)
        else:
            c.setStrokeColor(colors.black)
        
        c.setLineWidth(3)  # Borda grossa
        c.rect(x, y, width, height, fill=0, stroke=1)
        
        # Preparar cor do texto
        if self.layout_style == "layout2":
            c.setFillColor(colors.white)
        else:
            c.setFillColor(colors.black)
    
    def _draw_id_qr_section(self, c, xml_data, y_pos, section_height):
        """Desenha seção ID e QR Code COM ENQUADRAMENTO"""
        section_y = y_pos - section_height
        
        # Aplicar enquadramento na seção ID/QR
        self._apply_section_frame(c, self.margin, section_y, self.content_width, section_height)
        
        # ID da NF
        nf_key = xml_data.get('chave_nfe', 'N/A')
        id_display = f"ID: {nf_key[-6:]}" if len(nf_key) >= 6 else f"ID: {nf_key}"
        
        c.setFont("Helvetica", self.fonts['id_text'])
        margin_interna = 8
        c.drawString(self.margin + margin_interna, section_y + section_height * 0.7, id_display)
        
        # QR Code responsivo
        qr_size = min(section_height * 0.8, self.content_width * 0.15)
        qr_data = nf_key[:20] if nf_key != 'N/A' else "SEM_CHAVE"
        qr_x = self.page_width - self.margin - qr_size
        qr_y = section_y + (section_height - qr_size) / 2
        
        self._draw_qr_code(c, qr_data, qr_x, qr_y, qr_size)
        
        # Resetar cor
        c.setFillColor(colors.black)
        return section_y
    
    def _draw_highlighted_section(self, c, title, content, y_pos, section_height):
        """Desenha seção com enquadramento baseado no estilo de layout"""
        section_y = y_pos - section_height
        
        # Aplicar enquadramento baseado no estilo
        self._apply_section_frame(c, self.margin, section_y, self.content_width, section_height)
        
        # Texto com margens internas adequadas
        c.setFont("Helvetica-Bold", self.fonts['section_content'])
        # Posicionamento vertical centralizado com margem interna
        text_y = section_y + section_height * 0.6  # Centralizar com margem interna
        # Margem interna horizontal de 8 pontos
        margin_interna = 8
        c.drawString(self.margin + margin_interna, text_y, f"{title}: {content}")
        
        # Resetar cor para preto
        c.setFillColor(colors.black)
        return section_y
    
    def _draw_nf_section(self, c, xml_data, y_pos, section_height):
        """Desenha seção NF"""
        numero_nf = xml_data.get('numero_nf', '00000')
        return self._draw_highlighted_section(c, "NF", numero_nf, y_pos, section_height)
    
    def _draw_pedido_section(self, c, pedido_number, y_pos, section_height):
        """Desenha seção Pedido"""
        return self._draw_highlighted_section(c, "Pedido", pedido_number, y_pos, section_height)
    
    def _draw_remetente_section(self, c, xml_data, y_pos, section_height):
        """Desenha seção Remetente"""
        remetente = xml_data.get('remetente_razao', xml_data.get('remetente_nome', 'N/A'))[:50]  # Truncar se muito longo
        return self._draw_highlighted_section(c, "Remetente", remetente, y_pos, section_height)
    
    def _draw_destinatario_section(self, c, xml_data, y_pos, section_height):
        """Desenha seção Destinatário com controle dinâmico de limites"""
        section_y = y_pos - section_height
        
        # Calcular largura disponível (considerando área ÁREA no canto direito)
        area_width = self.content_width * 0.25  # 25% para área
        available_width = self.content_width - area_width - (self.spacing['field'] * 2)  # Espaçamento
        
        # Aplicar enquadramento baseado no estilo com largura controlada
        self._apply_section_frame(c, self.margin, section_y, available_width, section_height)
        
        # Calcular espaçamentos proporcionais dinamicamente
        line_spacing = max(8, section_height * 0.15)  # Mínimo 8 pontos
        start_y = section_y + section_height * 0.85
        margin_interna = 8
        
        # TÍTULO "DESTINATÁRIO" com controle de largura
        c.setFont("Helvetica-Bold", self.fonts['section_content'])
        c.drawString(self.margin + margin_interna, start_y, "DESTINATÁRIO")
        current_y = start_y - line_spacing
        
        # Nome da empresa destinatária com quebra dinâmica
        dest_nome = xml_data.get('destinatario_razao', xml_data.get('destinatario_nome', 'N/A'))
        c.setFont("Helvetica-Bold", self.fonts['normal_text'])
        
        # Calcular caracteres por linha baseado na largura disponível
        chars_per_line = max(25, int((available_width - margin_interna * 2) / 6))  # ~6 pontos por char
        
        if len(dest_nome) > chars_per_line:
            linha1 = dest_nome[:chars_per_line]
            linha2 = dest_nome[chars_per_line:chars_per_line*2] if len(dest_nome) > chars_per_line else ""
            c.drawString(self.margin + margin_interna, current_y, linha1)
            current_y -= line_spacing * 0.9
            if linha2:
                c.drawString(self.margin + margin_interna, current_y, linha2)
                current_y -= line_spacing * 0.9
        else:
            c.drawString(self.margin + margin_interna, current_y, dest_nome)
            current_y -= line_spacing
        
        # Endereço com controle de largura
        endereco = xml_data.get('destinatario_endereco', '')
        if endereco and current_y > section_y + line_spacing:  # Verificar se há espaço
            c.setFont("Helvetica", self.fonts['small_text'])
            
            # Quebrar endereço baseado na largura disponível
            if len(endereco) > chars_per_line:
                linha1_end = endereco[:chars_per_line]
                linha2_end = endereco[chars_per_line:chars_per_line*2] if len(endereco) > chars_per_line else ""
                c.drawString(self.margin + margin_interna, current_y, linha1_end)
                current_y -= line_spacing * 0.8
                if linha2_end and current_y > section_y + line_spacing * 0.5:
                    c.drawString(self.margin + margin_interna, current_y, linha2_end)
                    current_y -= line_spacing * 0.8
            else:
                c.drawString(self.margin + margin_interna, current_y, endereco)
                current_y -= line_spacing * 0.8
        
        # Cidade/UF + CEP (apenas se houver espaço)
        if current_y > section_y + line_spacing * 0.5:
            cidade = xml_data.get('destinatario_cidade', '')
            uf = xml_data.get('destinatario_uf', '')
            cep = xml_data.get('destinatario_cep', '')
            
            if cidade and uf:
                c.setFont("Helvetica-Bold", self.fonts['small_text'])
                cidade_texto = f"{cidade}/{uf}"
                
                # Adicionar CEP se couber na largura
                if cep and len(cep) == 8 and cep.isdigit():
                    cep_formatado = f"{cep[:5]}-{cep[5:]}"
                    if len(cidade_texto + f" - CEP: {cep_formatado}") <= chars_per_line:
                        cidade_texto += f" - CEP: {cep_formatado}"
                
                c.drawString(self.margin + margin_interna, current_y, cidade_texto)
        
        # Resetar cor para preto
        c.setFillColor(colors.black)
        return section_y
    
    def _draw_cidade_section(self, c, xml_data, y_pos, section_height):
        """Desenha seção Cidade/UF"""
        cidade = xml_data.get('destinatario_cidade', 'N/A')
        uf = xml_data.get('destinatario_uf', 'N/A')
        cidade_uf = f"{cidade} {uf}"
        return self._draw_highlighted_section(c, "Cidade/UF", cidade_uf, y_pos, section_height)
    
    def _draw_peso_volume_section(self, c, xml_data, y_pos, section_height):
        """Desenha seção Peso e Volume com controle dinâmico de limites COM ENQUADRAMENTO COMPLETO"""
        section_y = y_pos - section_height
        
        # Aplicar enquadramento em toda a seção peso/volume primeiro
        area_width = self.content_width * 0.25
        available_width = self.content_width - area_width - (self.spacing['field'] * 2)
        self._apply_section_frame(c, self.margin, section_y, available_width, section_height)
        
        # Dividir largura disponível entre peso e volume
        half_width = available_width / 2
        spacing_between = self.spacing['field']
        
        # Calcular posições verticais com melhor espaçamento
        title_y = section_y + section_height * 0.75
        value_y = section_y + section_height * 0.35
        margin_interna = 8
        
        # Título e valor do peso
        c.setFont("Helvetica-Bold", self.fonts['small_text'])
        c.drawString(self.margin + margin_interna, title_y, "PESO (KG)")
        
        # Usar peso específico do volume se disponível
        peso = xml_data.get('volume_weight') or xml_data.get('peso_bruto', '0.000')
        try:
            peso_formatado = f"{float(peso):.1f}".replace('.', ',')
        except:
            peso_formatado = str(peso)
        
        c.setFont("Helvetica-Bold", self.fonts['normal_text'])
        c.drawString(self.margin + margin_interna, value_y, peso_formatado)
        
        # Seção Volume (lado direito)
        volume_x = self.margin + half_width + spacing_between
        volume_width = half_width - spacing_between/2
        self._apply_section_frame(c, volume_x, section_y, volume_width, section_height)
        
        # Título e valor do volume
        c.setFont("Helvetica-Bold", self.fonts['small_text'])
        c.drawString(volume_x + margin_interna, title_y, "VOLUME")
        
        # Usar volume específico se disponível
        current_volume = xml_data.get('current_volume', 1)
        total_volumes = xml_data.get('total_volumes') or xml_data.get('quantidade_volumes', '1')
        volume_text = f"{current_volume}/{total_volumes}"
        
        c.setFont("Helvetica-Bold", self.fonts['normal_text'])
        c.drawString(volume_x + margin_interna, value_y, volume_text)
        
        # Resetar cor
        c.setFillColor(colors.black)
        return section_y
    
    def _draw_peso_volume_section_with_dynamic_info(self, c, xml_data, y_pos, section_height, 
                                                   volume_info, current_volume, total_volumes):
        """Desenha seção Peso e Volume com informações dinâmicas de volume (1/62, 2/62, etc.)"""
        section_y = y_pos - section_height
        
        # Dividir seção em duas partes: peso e volume
        half_width = self.content_width / 2
        spacing_between = self.spacing['field']
        
        # Seção Peso (lado esquerdo) - aplicar enquadramento
        peso_width = half_width - spacing_between/2
        self._apply_section_frame(c, self.margin, section_y, peso_width, section_height)
        
        # Calcular posições verticais com melhor espaçamento
        title_y = section_y + section_height * 0.75
        value_y = section_y + section_height * 0.35
        
        # Título Peso
        c.setFont("Helvetica-Bold", self.fonts['small_text'])
        c.drawString(self.margin + self.spacing['field'], title_y, "PESO (KG)")
        
        # Valor do peso calculado por volume
        peso_total = xml_data.get('peso_bruto', 'N/A')
        if peso_total and peso_total != 'N/A' and total_volumes:
            try:
                peso_total_num = float(str(peso_total).replace(',', '.'))
                peso_por_volume = peso_total_num / total_volumes
                peso_formatado = f"{peso_por_volume:.1f}" if peso_por_volume % 1 != 0 else f"{int(peso_por_volume)}"
            except (ValueError, AttributeError, ZeroDivisionError):
                peso_formatado = str(peso_total)
        else:
            peso_formatado = "N/A"
        
        c.setFont("Helvetica-Bold", self.fonts['normal_text'])
        c.drawString(self.margin + self.spacing['field'], value_y, peso_formatado)
        
        # Seção Volume (lado direito) - COM INFORMAÇÃO DINÂMICA - aplicar enquadramento
        volume_x = self.margin + half_width + spacing_between/2
        volume_width = half_width - spacing_between/2
        self._apply_section_frame(c, volume_x, section_y, volume_width, section_height)
        
        # Título Volume
        c.setFont("Helvetica-Bold", self.fonts['small_text'])
        c.drawString(volume_x + self.spacing['field'], title_y, "VOLUME")
        
        # Valor do volume dinâmico (1/62, 2/62, etc.)
        c.setFont("Helvetica-Bold", self.fonts['normal_text'])
        if volume_info:
            volume_display = volume_info  # "1/62", "2/62", etc.
        else:
            volume_display = f"{current_volume}/{total_volumes}"
        
        c.drawString(volume_x + self.spacing['field'], value_y, volume_display)
        
        # Resetar cor para preto
        c.setFillColor(colors.black)
        
        return section_y
    
    def _draw_area_section(self, c, area_code):
        """Desenha seção ÁREA posicionada para não sobrepor outras seções"""
        # Dimensões responsivas baseadas no papel
        area_width = self.content_width * 0.22  # 22% da largura
        area_height = self.content_height * 0.10  # 10% da altura
        
        # Posicionamento no canto direito, alinhado com seções peso/volume
        area_x = self.page_width - self.margin - area_width
        area_y = self.margin + (area_height * 0.2)  # Margem do fundo
        
        # Aplicar enquadramento baseado no estilo
        self._apply_section_frame(c, area_x, area_y, area_width, area_height)
        
        # Configurar cor do texto baseado no layout
        if self.layout_style == "layout2":
            c.setFillColor(colors.white)  # Texto branco para fundo preto
        else:
            c.setFillColor(colors.black)  # Texto preto para fundo cinza
            
        c.setFont("Helvetica-Bold", max(9, self.fonts['small_text'] + 1))
        title_y = area_y + area_height * 0.75
        c.drawCentredString(area_x + area_width/2, title_y, "ÁREA")
        
        # Código da área maior e em destaque
        c.setFont("Helvetica-Bold", max(16, self.fonts['section_content'] + 4))
        code_y = area_y + area_height * 0.35
        c.drawCentredString(area_x + area_width/2, code_y, area_code)
        
        # Linha separadora sutil entre título e código
        line_y = area_y + area_height * 0.6
        c.setStrokeColor(colors.Color(0.7, 0.7, 0.7))
        c.setLineWidth(0.5)
        margin_x = area_width * 0.15
        c.line(area_x + margin_x, line_y, area_x + area_width - margin_x, line_y)
    
    def _draw_footer(self, c):
        """Desenha rodapé"""
        c.setFont("Helvetica", self.fonts['small_text'])
        c.setFillColor(colors.grey)
        c.drawString(self.margin, self.margin / 2, "Sistema de Etiquetas")
    
    def _draw_qr_code(self, c, data, x, y, size):
        """Desenha QR code responsivo"""
        try:
            # Criar QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.ERROR_CORRECT_L,
                box_size=max(1, int(10 * self.scale_factor)),
                border=1,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            # Gerar imagem
            qr_img = qr.make_image(fill_color="black", back_color="white")
            
            # Salvar temporariamente
            temp_path = "/tmp/qr_temp.png"
            qr_img.save(temp_path)
            
            # Desenhar no PDF
            c.drawImage(temp_path, x, y, width=size, height=size)
            
            # Limpar arquivo temporário
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
        except Exception as e:
            logger.warning(f"Erro ao gerar QR code: {e}")
            # Fallback: desenhar retângulo
            c.setFillColor(colors.lightgrey)
            c.rect(x, y, size, size, fill=1)
            c.setFillColor(colors.black)
            c.setFont("Helvetica", max(6, int(8 * self.scale_factor)))
            c.drawCentredString(x + size/2, y + size/2, "QR")


def generate_responsive_label_from_database_xml(xml_record, pedido_number: str = None, 
                                               area_code: str = "01", company_name: str = "SUA EMPRESA",
                                               company_logo_path: str = None, paper_width_mm: int = 100,
                                               paper_height_mm: int = 150) -> BytesIO:
    """
    Função utilitária para gerar etiqueta responsiva a partir de um registro XML do banco
    
    Args:
        xml_record: Registro XML do banco (ImportedXML ou XMLFile)
        pedido_number: Número do pedido (opcional)
        area_code: Código da área (padrão: "01")
        company_name: Nome da empresa (padrão: "SUA EMPRESA")
        company_logo_path: Caminho para logo da empresa (opcional)
        paper_width_mm: Largura do papel em milímetros
        paper_height_mm: Altura do papel em milímetros
        
    Returns:
        BytesIO contendo o PDF da etiqueta responsiva
    """
    try:
        # Obter conteúdo XML
        xml_content = getattr(xml_record, 'xml_content', None) or getattr(xml_record, 'content', '')
        
        if not xml_content:
            raise ValueError("XML content not found in record")
        
        # Criar gerador responsivo
        generator = ResponsiveTransportLabelGenerator(
            company_name=company_name,
            paper_width_mm=paper_width_mm,
            paper_height_mm=paper_height_mm
        )
        
        # Gerar etiqueta
        return generator.generate_transport_label(
            xml_content=xml_content,
            pedido_number=pedido_number,
            area_code=area_code,
            company_logo_path=company_logo_path
        )
        
    except Exception as e:
        logger.error(f"Erro ao gerar etiqueta responsiva: {str(e)}")
        raise


def generate_multiple_responsive_labels_from_volumes(xml_record, volumes_config: list, 
                                                   company_name: str = "SUA EMPRESA", 
                                                   company_logo_path: str = None,
                                                   paper_width_mm: int = 100,
                                                   paper_height_mm: int = 150,
                                                   area_code: str = "01",
                                                   company_subtitle: str = "TRANSPORTE",
                                                   layout_style: str = "layout1") -> list:
    """
    Gera múltiplas etiquetas responsivas separadas baseadas na configuração de volumes
    
    Args:
        xml_record: Registro XML do banco
        volumes_config: Lista de dicionários com configurações de cada volume
                       [{"peso": 5.5, "pedido": "PED123-1"}, ...]
        company_name: Nome da empresa
        company_logo_path: Caminho para logo da empresa
        paper_width_mm: Largura do papel em milímetros
        paper_height_mm: Altura do papel em milímetros
        area_code: Código da área
        
    Returns:
        Lista de dicionários com os PDFs das etiquetas
    """
    try:
        labels = []
        
        # Obter conteúdo XML
        xml_content = getattr(xml_record, 'xml_content', None) or getattr(xml_record, 'content', '')
        
        if not xml_content:
            raise ValueError("XML content not found in record")
        
        total_volumes = len(volumes_config)
        logger.info(f"Configuração multi-volume: {total_volumes} volumes configurados")
        
        # Processar em lotes de 8 volumes para evitar problemas de memória
        batch_size = 8
        batches = [volumes_config[i:i + batch_size] for i in range(0, len(volumes_config), batch_size)]
        
        for batch_idx, batch in enumerate(batches):
            logger.info(f"Processando lote {batch_idx + 1}/{len(batches)} com {len(batch)} volumes")
            
            # Criar novo gerador para cada lote para evitar acúmulo de memória
            generator = ResponsiveTransportLabelGenerator(
                company_name=company_name,
                company_subtitle=company_subtitle,
                paper_width_mm=paper_width_mm,
                paper_height_mm=paper_height_mm,
                layout_style=layout_style
            )
            
            # Gerar etiquetas do lote atual
            for volume_config in batch:
                volume_idx = volumes_config.index(volume_config) + 1
                peso = volume_config.get('peso', 0)
                pedido = volume_config.get('pedido', f'PED{volume_idx}')
                
                try:
                    # Criar volume dinâmico com numeração X/Y
                    volume_info = f"{volume_idx}/{total_volumes}"
                    
                    label_buffer = generator.generate_transport_label_with_volume_info(
                        xml_content=xml_content,
                        pedido_number=pedido,
                        area_code=area_code,
                        company_logo_path=company_logo_path,
                        volume_info=volume_info,
                        current_volume=volume_idx,
                        total_volumes=total_volumes
                    )
                    
                    if label_buffer is None:
                        logger.warning(f"Label buffer é None para volume {volume_idx} - criando PDF de fallback")
                        # Criar PDF funcional de fallback
                        from io import BytesIO
                        from reportlab.pdfgen import canvas
                        label_buffer = BytesIO()
                        c = canvas.Canvas(label_buffer, pagesize=(284, 426))  # 100x150mm
                        c.setFont("Helvetica-Bold", 14)
                        c.drawString(50, 380, f"VOLUME {volume_idx} DE {total_volumes}")
                        c.setFont("Helvetica", 12)
                        c.drawString(50, 360, f"Pedido: {pedido}")
                        c.drawString(50, 340, f"Peso: {peso} kg")
                        c.drawString(50, 320, f"Área: {area_code}")
                        c.drawString(50, 300, f"Empresa: {company_name}")
                        c.save()
                        label_buffer.seek(0)
                        
                except Exception as e:
                    logger.error(f"Erro ao gerar etiqueta para volume {volume_idx}: {e}")
                    # Criar PDF de erro funcional
                    from io import BytesIO
                    from reportlab.pdfgen import canvas
                    label_buffer = BytesIO()
                    c = canvas.Canvas(label_buffer, pagesize=(284, 426))
                    c.setFont("Helvetica-Bold", 12)
                    c.drawString(50, 380, f"ERRO - VOLUME {volume_idx}")
                    c.setFont("Helvetica", 10)
                    c.drawString(50, 360, f"Pedido: {pedido}")
                    c.drawString(50, 340, f"Peso: {peso} kg")
                    c.drawString(50, 320, f"Erro: {str(e)[:40]}")
                    c.save()
                    label_buffer.seek(0)
                
                labels.append({
                    'volume': volume_idx,
                    'peso': peso,
                    'pedido': pedido,
                    'pdf_buffer': label_buffer,
                    'filename': f'etiqueta_volume_{volume_idx}_{pedido}.pdf'
                })
            
            # Limpar gerador do lote para liberar memória
            del generator
        
        logger.info(f"Geradas {len(labels)} etiquetas responsivas separadas")
        return labels
        
    except Exception as e:
        logger.error(f"Erro ao gerar etiquetas responsivas múltiplas: {str(e)}")
        raise


def merge_labels_into_single_pdf(labels: list) -> BytesIO:
    """
    Mescla múltiplas etiquetas em um único PDF com múltiplas páginas usando PyPDF2
    """
    try:
        from PyPDF2 import PdfWriter, PdfReader
        
        merged_buffer = BytesIO()
        
        if not labels:
            return merged_buffer
            
        # Se apenas uma etiqueta, retornar diretamente
        if len(labels) == 1:
            pdf_buffer = labels[0].get('pdf_buffer') or labels[0].get('buffer')
            return pdf_buffer
        
        # Criar writer para mesclar PDFs
        writer = PdfWriter()
        
        # Adicionar cada etiqueta como uma página
        for i, label in enumerate(labels):
            pdf_buffer = label.get('pdf_buffer') or label.get('buffer')
            
            if pdf_buffer is None:
                logger.error(f"PDF buffer é None para etiqueta {i+1}")
                continue
                
            pdf_buffer.seek(0)
            
            try:
                reader = PdfReader(pdf_buffer)
                # Adicionar todas as páginas do PDF atual
                for page in reader.pages:
                    writer.add_page(page)
                    
            except Exception as e:
                logger.error(f"Erro ao adicionar etiqueta {i+1} ao PDF: {e}")
                continue
        
        # Escrever PDF final
        writer.write(merged_buffer)
        merged_buffer.seek(0)
        
        logger.info(f"PDF multipáginas criado com {len(labels)} páginas usando PyPDF2")
        return merged_buffer
        
    except Exception as e:
        logger.error(f"Erro ao mesclar PDFs com PyPDF2: {str(e)}")
        # Fallback: retornar primeira etiqueta
        if labels:
            return labels[0].get('pdf_buffer') or labels[0].get('buffer')
        return BytesIO()