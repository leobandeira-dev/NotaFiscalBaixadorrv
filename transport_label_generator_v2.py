"""
Gerador de Etiquetas de Transporte Personalizáveis
Sistema genérico que permite personalização com logo da empresa
"""
import logging
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
import qrcode
from PIL import Image as PILImage
from xml_processor import extract_xml_data
import os

logger = logging.getLogger(__name__)

class CustomTransportLabelGenerator:
    """Gerador de etiquetas de transporte personalizáveis"""
    
    def __init__(self, company_name="SUA EMPRESA", company_subtitle="TRANSPORTE", 
                 paper_width_mm=100, paper_height_mm=150):
        # Configurações da página (dimensões personalizáveis)
        self.page_width = paper_width_mm * mm
        self.page_height = paper_height_mm * mm
        self.margin = min(10 * mm, self.page_width * 0.1)  # Margem adaptável
        self.content_width = self.page_width - (2 * self.margin)
        self.company_name = company_name
        self.company_subtitle = company_subtitle
        
        # Configurações de escala baseadas no tamanho do papel para impressão responsiva
        self.scale_factor = min(paper_width_mm / 100, paper_height_mm / 150)
        self.base_font_size = max(7, int(9 * self.scale_factor))
        self.header_font_size = max(9, int(11 * self.scale_factor))
        self.large_font_size = max(14, int(18 * self.scale_factor))
        
        # Configurações específicas para impressão responsiva
        self.line_height = max(3 * mm, self.base_font_size * 1.4)
        self.section_spacing = max(2 * mm, self.line_height * 0.6)
        self.field_spacing = max(1.5 * mm, self.line_height * 0.3)
    
    def generate_transport_label(self, xml_content: str, pedido_number: str = None, 
                               area_code: str = "01", company_logo_path: str = None) -> BytesIO:
        """
        Gera etiqueta de transporte personalizada
        
        Args:
            xml_content: Conteúdo XML da NFe
            pedido_number: Número do pedido (opcional)
            area_code: Código da área (padrão: "01")
            company_logo_path: Caminho para logo da empresa (opcional)
            
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
            self._draw_transport_label(c, xml_data, pedido_number, area_code, company_logo_path)
            
            c.showPage()
            c.save()
            buffer.seek(0)
            
            logger.info("Etiqueta de transporte personalizada gerada com sucesso")
            return buffer
            
        except Exception as e:
            logger.error(f"Erro ao gerar etiqueta: {str(e)}")
            raise
    
    def _draw_transport_label(self, c, xml_data, pedido_number, area_code, company_logo_path):
        """Desenha a etiqueta completa personalizada com layout responsivo"""
        
        # Calcular distribuição responsiva do espaço
        available_height = self.page_height - (20 * mm)  # Margem total
        num_sections = 9  # Número de seções principais
        
        # Distribuir espaço uniformemente para layout harmonioso
        section_spacing = available_height / num_sections
        
        # Posição inicial Y (começa do topo)
        y_pos = self.page_height - 10 * mm
        
        # 1. Header da empresa (compacto)
        y_pos = self._draw_company_header(c, y_pos, company_logo_path)
        y_pos -= section_spacing * 0.8
        
        # 2. ID e QR Code (lado a lado otimizado)
        y_pos = self._draw_id_section(c, xml_data, y_pos)
        y_pos -= section_spacing * 1.2
        
        # 3. NF Section
        y_pos = self._draw_nf_section(c, xml_data, y_pos)
        y_pos -= section_spacing * 0.6
        
        # 4. Pedido Section
        y_pos = self._draw_pedido_section(c, pedido_number or xml_data.get('numero_nf', '00000'), y_pos)
        y_pos -= section_spacing * 0.6
        
        # 5. Remetente (compacto)
        y_pos = self._draw_remetente_section(c, xml_data, y_pos)
        y_pos -= section_spacing * 0.8
        
        # 6. Destinatário (expandido)
        y_pos = self._draw_destinatario_section(c, xml_data, y_pos)
        y_pos -= section_spacing * 1.2
        
        # 7. Cidade/UF
        y_pos = self._draw_cidade_section(c, xml_data, y_pos)
        y_pos -= section_spacing * 0.6
        
        # 8. Peso Section
        y_pos = self._draw_peso_section(c, xml_data, y_pos)
        y_pos -= section_spacing * 0.6
        
        # 9. Volume Section
        y_pos = self._draw_volume_section(c, xml_data, y_pos)
        
        # 8. Área e Rodapé
        self._draw_area_section(c, area_code)
        self._draw_footer(c)
        
        # 10. Área (canto inferior direito)
        self._draw_area_section(c, area_code)
        
        # 11. Footer
        self._draw_footer(c)
    
    def _draw_company_header(self, c, y_pos, company_logo_path):
        """Desenha o cabeçalho da empresa com logo opcional"""
        try:
            # Se logo fornecida, tentar desenhar
            if company_logo_path and os.path.exists(company_logo_path):
                try:
                    # Desenhar logo
                    c.drawImage(company_logo_path, 
                              self.page_width/2 - 30*mm, y_pos - 20*mm, 
                              width=60*mm, height=20*mm, preserveAspectRatio=True)
                    return
                except Exception as e:
                    logger.warning(f"Erro ao carregar logo: {e}")
            
            # Fallback: texto da empresa
            c.setFont("Helvetica-Bold", 24)
            c.drawCentredString(self.page_width / 2, y_pos, self.company_name)
            
            c.setFont("Helvetica", 12)
            c.drawCentredString(self.page_width / 2, y_pos - 15, self.company_subtitle)
            
        except Exception as e:
            logger.warning(f"Erro no cabeçalho: {e}")
            # Fallback simples
            c.setFont("Helvetica-Bold", 20)
            c.drawCentredString(self.page_width / 2, y_pos, "ETIQUETA DE TRANSPORTE")
    
    def _draw_id_section(self, c, xml_data, y_pos):
        """Desenha seção do ID e QR Code"""
        # ID text
        c.setFont("Helvetica", 12)
        invoice_key = xml_data.get('chave_acesso', '00000-000-000-000')
        formatted_id = f"ID: {invoice_key[:5]}-{invoice_key[5:8]}-{invoice_key[8:11]}-{invoice_key[11:14]}"
        c.drawString(self.margin, y_pos, formatted_id)
        
        # QR Code
        qr_data = xml_data.get('chave_acesso', invoice_key)
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
        nf_number = xml_data.get('numero_nf', '00000')
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
        remetente = xml_data.get('nome_emitente', 'EMPRESA REMETENTE')
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
        destinatario = xml_data.get('destinatario_razao', 'EMPRESA DESTINATÁRIA')
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
        
        endereco = ", ".join(endereco_parts) or "Endereço não informado"
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
        cidade = xml_data.get('destinatario_cidade', 'CIDADE')
        uf = xml_data.get('destinatario_uf', 'UF')
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
        peso = xml_data.get('peso_bruto', '0.000')
        c.drawString(self.margin + 5, y_pos - 8, f"Peso: {peso}")
        
        # Transportadora (texto normal)
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 12)
        c.drawString(self.margin + peso_width + 10, y_pos - 8, f"Transportadora: {self.company_name}")
        
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
        volumes = xml_data.get('quantidade_volumes', '1')
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
        c.drawCentredString(area_x + area_width/2, area_y + area_height - 10, "ÁREA")
        
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(area_x + area_width/2, area_y + 8, area_code)
        
        # Voltar cor para preto
        c.setFillColor(colors.black)
    
    def _draw_footer(self, c):
        """Desenha rodapé com sistema"""
        c.setFont("Helvetica", 8)
        c.setFillColor(colors.grey)
        c.drawString(self.margin, 30 * mm, "Sistema de Etiquetas")
    
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
            
            # Salvar arquivo temporário
            import tempfile
            import os
            
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                img.save(temp_file.name, format='PNG')
                temp_path = temp_file.name
            
            # Desenhar no canvas
            c.drawImage(temp_path, x, y, width=size, height=size)
            
            # Limpar arquivo temporário
            os.unlink(temp_path)
            
        except Exception as e:
            logger.warning(f"Erro ao gerar QR code: {e}")
            # Desenhar retângulo placeholder
            c.rect(x, y, size, size, stroke=1, fill=0)
            c.setFont("Helvetica", 8)
            c.drawCentredString(x + size/2, y + size/2, "QR")


def generate_custom_label_from_database_xml(xml_record, pedido_number: str = None, 
                                           area_code: str = "01", company_name: str = "SUA EMPRESA",
                                           company_logo_path: str = None, paper_width_mm: int = 100,
                                           paper_height_mm: int = 150, volume_weight: float = None) -> BytesIO:
    """
    Função utilitária para gerar etiqueta personalizada a partir de um registro XML do banco
    
    Args:
        xml_record: Registro XML do banco (ImportedXML ou XMLFile)
        pedido_number: Número do pedido (opcional)
        area_code: Código da área (padrão: "01")
        company_name: Nome da empresa (padrão: "SUA EMPRESA")
        company_logo_path: Caminho para logo da empresa (opcional)
        
    Returns:
        BytesIO contendo o PDF da etiqueta
    """
    try:
        # Criar gerador com dimensões personalizadas
        generator = CustomTransportLabelGenerator(
            company_name=company_name,
            company_subtitle="TRANSPORTE",
            paper_width_mm=paper_width_mm,
            paper_height_mm=paper_height_mm
        )
        
        xml_content = xml_record.xml_content
        if not xml_content:
            raise ValueError("XML content not found in record")
        
        # Usar o número NF como pedido se não fornecido
        if not pedido_number:
            pedido_number = getattr(xml_record, 'numero_nf', None) or xml_record.invoice_key[:5]
        
        label_buffer = generator.generate_transport_label(
            xml_content=xml_content,
            pedido_number=pedido_number,
            area_code=area_code,
            company_logo_path=company_logo_path
        )
        
        logger.info(f"Etiqueta personalizada gerada: {paper_width_mm}x{paper_height_mm}mm")
        return label_buffer
        
    except Exception as e:
        logger.error(f"Erro ao gerar etiqueta personalizada: {str(e)}")
        raise


def generate_multiple_labels_from_volumes(xml_record, volumes_config: list, 
                                        company_name: str = "SUA EMPRESA", 
                                        company_logo_path: str = None,
                                        paper_width_mm: int = 100,
                                        paper_height_mm: int = 150,
                                        area_code: str = "01") -> list:
    """
    Gera múltiplas etiquetas separadas baseadas na configuração de volumes
    
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
    labels = []
    
    try:
        for i, volume_config in enumerate(volumes_config):
            peso = volume_config.get('peso', 0)
            pedido = volume_config.get('pedido', f'PED{getattr(xml_record, "numero_nf", "00000")}-{i+1}')
            
            # Gerar etiqueta para este volume específico
            label_buffer = generate_custom_label_from_database_xml(
                xml_record=xml_record,
                pedido_number=pedido,
                area_code=area_code,
                company_name=company_name,
                company_logo_path=company_logo_path,
                paper_width_mm=paper_width_mm,
                paper_height_mm=paper_height_mm,
                volume_weight=peso
            )
            
            if label_buffer:
                labels.append({
                    'buffer': label_buffer,
                    'filename': f'etiqueta_volume_{i+1}_{pedido}.pdf',
                    'volume': i+1,
                    'peso': peso,
                    'pedido': pedido
                })
        
        logger.info(f"Geradas {len(labels)} etiquetas separadas")
        return labels
        
    except Exception as e:
        logger.error(f"Erro ao gerar múltiplas etiquetas: {e}")
        return []