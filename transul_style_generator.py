#!/usr/bin/env python3
"""
Gerador de Etiquetas Estilo Transul Profissional
Sistema que replica exatamente o layout e harmonia visual do modelo de inspiração
"""

import os
import sys
import logging
from io import BytesIO
from reportlab.lib.pagesizes import mm
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import qrcode
from reportlab.lib.utils import ImageReader
from xml.etree import ElementTree as ET

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TransulStyleLabelGenerator:
    """Gerador de etiquetas seguindo exatamente o estilo visual da Transul"""
    
    def __init__(self, company_name="TRANSUL", company_subtitle="TRANSPORTE", 
                 paper_width_mm=100, paper_height_mm=150):
        """
        Inicializa o gerador com configurações estilo Transul
        
        Args:
            company_name: Nome da empresa para o cabeçalho
            company_subtitle: Subtítulo da empresa
            paper_width_mm: Largura do papel em milímetros
            paper_height_mm: Altura do papel em milímetros
        """
        # Configurações de papel
        self.paper_width = paper_width_mm * mm
        self.paper_height = paper_height_mm * mm
        self.margin = 8 * mm
        self.content_width = self.paper_width - (2 * self.margin)
        self.content_height = self.paper_height - (2 * self.margin)
        
        # Configurações da empresa
        self.company_name = company_name
        self.company_subtitle = company_subtitle
        
        # Configurações visuais estilo Transul
        self._setup_transul_fonts()
        self._setup_transul_spacing()
        
        logger.info(f"Gerador Transul: {paper_width_mm}x{paper_height_mm}mm")
    
    def _setup_transul_fonts(self):
        """Configura tamanhos de fonte no estilo Transul"""
        base_scale = min(self.paper_width, self.paper_height) / (100 * mm)
        
        self.fonts = {
            'company_name': max(12, int(16 * base_scale)),
            'company_sub': max(8, int(10 * base_scale)),
            'section_header': max(10, int(12 * base_scale)),
            'content_text': max(8, int(10 * base_scale)),
            'small_text': max(6, int(8 * base_scale)),
            'id_text': max(7, int(9 * base_scale))
        }
    
    def _setup_transul_spacing(self):
        """Configura espaçamentos no estilo Transul"""
        self.spacing = {
            'section': 3 * mm,  # Espaçamento entre seções
            'internal': 2 * mm,  # Margem interna das seções
            'line': 1.5 * mm    # Espaçamento entre linhas
        }
    
    def generate_transul_label(self, xml_content: str, pedido_number: str = None, 
                              area_code: str = "01") -> BytesIO:
        """
        Gera etiqueta no estilo Transul profissional
        
        Args:
            xml_content: Conteúdo XML da NFe
            pedido_number: Número do pedido
            area_code: Código da área
            
        Returns:
            BytesIO contendo o PDF da etiqueta
        """
        # Extrair dados do XML
        xml_data = self._extract_xml_data(xml_content)
        
        # Criar PDF
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=(self.paper_width, self.paper_height))
        
        # Desenhar layout Transul
        self._draw_transul_layout(c, xml_data, pedido_number, area_code)
        
        c.save()
        buffer.seek(0)
        
        logger.info(f"Etiqueta Transul gerada: {self.paper_width/mm:.0f}x{self.paper_height/mm:.0f}mm")
        return buffer
    
    def _extract_xml_data(self, xml_content: str) -> dict:
        """Extrai dados relevantes do XML NFe"""
        try:
            root = ET.fromstring(xml_content)
            
            # Namespace da NFe
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
            
            # Buscar elementos principais
            infnfe = root.find('.//nfe:infNFe', ns)
            if infnfe is None:
                return {'error': 'Estrutura NFe não encontrada'}
            
            # Extrair dados básicos
            ide = infnfe.find('nfe:ide', ns)
            emit = infnfe.find('nfe:emit', ns)
            dest = infnfe.find('nfe:dest', ns)
            total = infnfe.find('nfe:total/nfe:ICMSTot', ns)
            transp = infnfe.find('nfe:transp', ns)
            
            # Montar dados estruturados
            data = {
                'numero_nf': ide.find('nfe:nNF', ns).text if ide is not None and ide.find('nfe:nNF', ns) is not None else '00000',
                'chave_nfe': infnfe.get('Id', '').replace('NFe', '') if infnfe.get('Id') else 'N/A',
                'emitente_nome': emit.find('nfe:xNome', ns).text if emit is not None and emit.find('nfe:xNome', ns) is not None else 'N/A',
                'destinatario_nome': dest.find('nfe:xNome', ns).text if dest is not None and dest.find('nfe:xNome', ns) is not None else 'N/A',
                'destinatario_endereco': '',
                'destinatario_cidade': '',
                'destinatario_uf': '',
                'destinatario_cep': '',
                'valor_total': '0,00',
                'peso_bruto': '0,000',
                'quantidade_volumes': '1'
            }
            
            # Endereço do destinatário
            if dest is not None:
                endereco_dest = dest.find('nfe:enderDest', ns)
                if endereco_dest is not None:
                    logradouro = endereco_dest.find('nfe:xLgr', ns)
                    numero = endereco_dest.find('nfe:nro', ns)
                    bairro = endereco_dest.find('nfe:xBairro', ns)
                    cidade = endereco_dest.find('nfe:xMun', ns)
                    uf = endereco_dest.find('nfe:UF', ns)
                    cep = endereco_dest.find('nfe:CEP', ns)
                    
                    # Montar endereço completo
                    endereco_parts = []
                    if logradouro is not None:
                        endereco_parts.append(logradouro.text)
                    if numero is not None:
                        endereco_parts.append(numero.text)
                    if bairro is not None:
                        endereco_parts.append(bairro.text)
                    
                    data['destinatario_endereco'] = ', '.join(endereco_parts)
                    data['destinatario_cidade'] = cidade.text if cidade is not None else 'N/A'
                    data['destinatario_uf'] = uf.text if uf is not None else 'N/A'
                    data['destinatario_cep'] = cep.text if cep is not None else ''
            
            # Valor total
            if total is not None:
                valor_nf = total.find('nfe:vNF', ns)
                if valor_nf is not None:
                    try:
                        valor = float(valor_nf.text)
                        data['valor_total'] = f"{valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    except:
                        pass
            
            # Transporte
            if transp is not None:
                vol = transp.find('nfe:vol', ns)
                if vol is not None:
                    qvol = vol.find('nfe:qVol', ns)
                    peso_bruto = vol.find('nfe:pesoB', ns)
                    
                    if qvol is not None:
                        data['quantidade_volumes'] = qvol.text
                    
                    if peso_bruto is not None:
                        try:
                            peso = float(peso_bruto.text) / 1000  # Converter para kg
                            data['peso_bruto'] = f"{peso:.3f}".replace('.', ',')
                        except:
                            pass
            
            return data
            
        except Exception as e:
            logger.error(f"Erro ao processar XML: {e}")
            return {'error': f'Erro no XML: {str(e)}'}
    
    def _draw_transul_layout(self, c, xml_data, pedido_number, area_code):
        """Desenha layout completo no estilo Transul"""
        current_y = self.paper_height - self.margin
        
        # 1. Cabeçalho da empresa (estilo Transul)
        company_height = 20 * mm
        current_y -= company_height
        self._draw_transul_header(c, current_y, company_height)
        current_y -= self.spacing['section']
        
        # 2. Linha ID + QR Code
        id_qr_height = 15 * mm
        current_y -= id_qr_height
        self._draw_id_qr_line(c, xml_data, current_y, id_qr_height)
        current_y -= self.spacing['section']
        
        # 3. NF (faixa preta)
        nf_height = 12 * mm
        current_y -= nf_height
        self._draw_black_section(c, f"NF: {xml_data.get('numero_nf', '00000')}", current_y, nf_height)
        current_y -= self.spacing['section']
        
        # 4. Pedido (faixa preta)
        if pedido_number:
            pedido_height = 12 * mm
            current_y -= pedido_height
            self._draw_black_section(c, f"Pedido: {pedido_number}", current_y, pedido_height)
            current_y -= self.spacing['section']
        
        # 5. Remetente (faixa preta)
        remetente_height = 12 * mm
        current_y -= remetente_height
        remetente_nome = xml_data.get('emitente_nome', 'N/A')
        if len(remetente_nome) > 45:
            remetente_nome = remetente_nome[:45] + "..."
        self._draw_black_section(c, f"Remetente: {remetente_nome}", current_y, remetente_height)
        current_y -= self.spacing['section']
        
        # 6. Destinatário (seção branca com detalhes)
        dest_height = 20 * mm
        current_y -= dest_height
        self._draw_destinatario_details(c, xml_data, current_y, dest_height)
        current_y -= self.spacing['section']
        
        # 7. Cidade/UF (faixa preta)
        cidade_height = 12 * mm
        current_y -= cidade_height
        cidade_uf = f"{xml_data.get('destinatario_cidade', 'N/A')} {xml_data.get('destinatario_uf', 'N/A')}"
        self._draw_black_section(c, f"Cidade/UF: {cidade_uf}", current_y, cidade_height)
        current_y -= self.spacing['section']
        
        # 8. Peso e Volume (faixas pretas separadas)
        peso_vol_height = 12 * mm
        current_y -= peso_vol_height
        self._draw_peso_volume_sections(c, xml_data, current_y, peso_vol_height)
        
        # 9. Área (canto inferior direito)
        self._draw_area_section(c, area_code)
        
        # 10. Rodapé discreto
        self._draw_footer(c)
    
    def _draw_transul_header(self, c, y_pos, height):
        """Desenha cabeçalho no estilo Transul"""
        # Fundo branco limpo
        c.setFillColor(colors.white)
        c.rect(self.margin, y_pos, self.content_width, height, fill=1, stroke=0)
        
        # Nome da empresa centralizado
        c.setFont("Helvetica-Bold", self.fonts['company_name'])
        c.setFillColor(colors.black)
        text_width = c.stringWidth(self.company_name, "Helvetica-Bold", self.fonts['company_name'])
        text_x = self.margin + (self.content_width - text_width) / 2
        text_y = y_pos + height * 0.65
        c.drawString(text_x, text_y, self.company_name)
        
        # Subtítulo centralizado
        c.setFont("Helvetica", self.fonts['company_sub'])
        sub_width = c.stringWidth(self.company_subtitle, "Helvetica", self.fonts['company_sub'])
        sub_x = self.margin + (self.content_width - sub_width) / 2
        sub_y = y_pos + height * 0.25
        c.drawString(sub_x, sub_y, self.company_subtitle)
    
    def _draw_id_qr_line(self, c, xml_data, y_pos, height):
        """Desenha linha ID + QR Code"""
        # ID da NF
        nf_key = xml_data.get('chave_nfe', 'N/A')
        id_display = f"ID: {nf_key}" if len(nf_key) <= 20 else f"ID: {nf_key[-15:]}"
        
        c.setFont("Helvetica", self.fonts['id_text'])
        c.setFillColor(colors.black)
        c.drawString(self.margin + self.spacing['internal'], y_pos + height * 0.4, id_display)
        
        # QR Code
        qr_size = height * 0.8
        qr_data = nf_key[:30] if nf_key != 'N/A' else "TRANSUL_LABEL"
        qr_x = self.paper_width - self.margin - qr_size
        qr_y = y_pos + (height - qr_size) / 2
        
        self._draw_qr_code(c, qr_data, qr_x, qr_y, qr_size)
    
    def _draw_black_section(self, c, text, y_pos, height):
        """Desenha seção com faixa preta e texto branco (estilo Transul)"""
        # Faixa preta
        c.setFillColor(colors.black)
        c.rect(self.margin, y_pos, self.content_width, height, fill=1, stroke=0)
        
        # Texto branco
        c.setFont("Helvetica-Bold", self.fonts['section_header'])
        c.setFillColor(colors.white)
        text_y = y_pos + height * 0.4
        c.drawString(self.margin + self.spacing['internal'], text_y, text)
        
        # Resetar cor
        c.setFillColor(colors.black)
    
    def _draw_destinatario_details(self, c, xml_data, y_pos, height):
        """Desenha seção de destinatário com detalhes (fundo branco)"""
        # Fundo branco
        c.setFillColor(colors.white)
        c.rect(self.margin, y_pos, self.content_width, height, fill=1, stroke=0)
        
        # Borda sutil
        c.setStrokeColor(colors.lightgrey)
        c.setLineWidth(0.5)
        c.rect(self.margin, y_pos, self.content_width, height, fill=0, stroke=1)
        
        # Conteúdo
        c.setFont("Helvetica", self.fonts['content_text'])
        c.setFillColor(colors.black)
        
        line_height = height / 3
        
        # Destinatário
        dest_nome = xml_data.get('destinatario_nome', 'N/A')
        if len(dest_nome) > 50:
            dest_nome = dest_nome[:50] + "..."
        c.drawString(self.margin + self.spacing['internal'], y_pos + line_height * 2.2, f"Destinatário: {dest_nome}")
        
        # Endereço
        endereco = xml_data.get('destinatario_endereco', '')
        if endereco and len(endereco) > 50:
            endereco = endereco[:50] + "..."
        if endereco:
            c.drawString(self.margin + self.spacing['internal'], y_pos + line_height * 1.2, f"Endereço: {endereco}")
        
        # CEP
        cep = xml_data.get('destinatario_cep', '')
        if cep and len(cep) == 8:
            cep_formatado = f"{cep[:5]}-{cep[5:]}"
            c.drawString(self.margin + self.spacing['internal'], y_pos + line_height * 0.2, f"CEP: {cep_formatado}")
    
    def _draw_peso_volume_sections(self, c, xml_data, y_pos, height):
        """Desenha seções de peso e volume lado a lado"""
        half_width = self.content_width / 2
        spacing = 2 * mm
        
        # Seção Peso (esquerda)
        peso_width = half_width - spacing
        peso_text = f"Peso: {xml_data.get('peso_bruto', '0,000')}"
        
        c.setFillColor(colors.black)
        c.rect(self.margin, y_pos, peso_width, height, fill=1, stroke=0)
        
        c.setFont("Helvetica-Bold", self.fonts['section_header'])
        c.setFillColor(colors.white)
        c.drawString(self.margin + self.spacing['internal'], y_pos + height * 0.4, peso_text)
        
        # Seção Volume (direita)
        volume_x = self.margin + half_width + spacing
        volume_width = half_width - spacing
        volume_text = f"Volume: 1/{xml_data.get('quantidade_volumes', '1')}"
        
        c.setFillColor(colors.black)
        c.rect(volume_x, y_pos, volume_width, height, fill=1, stroke=0)
        
        c.setFont("Helvetica-Bold", self.fonts['section_header'])
        c.setFillColor(colors.white)
        c.drawString(volume_x + self.spacing['internal'], y_pos + height * 0.4, volume_text)
        
        # Resetar cor
        c.setFillColor(colors.black)
    
    def _draw_area_section(self, c, area_code):
        """Desenha seção ÁREA no canto inferior direito"""
        area_width = 25 * mm
        area_height = 20 * mm
        
        area_x = self.paper_width - self.margin - area_width
        area_y = self.margin + 5 * mm
        
        # Faixa preta
        c.setFillColor(colors.black)
        c.rect(area_x, area_y, area_width, area_height, fill=1, stroke=0)
        
        # Texto "ÁREA"
        c.setFont("Helvetica-Bold", self.fonts['content_text'])
        c.setFillColor(colors.white)
        area_text_y = area_y + area_height * 0.7
        c.drawCentredString(area_x + area_width/2, area_text_y, "ÁREA")
        
        # Código da área
        c.setFont("Helvetica-Bold", self.fonts['company_name'])
        code_text_y = area_y + area_height * 0.3
        c.drawCentredString(area_x + area_width/2, code_text_y, area_code)
        
        # Resetar cor
        c.setFillColor(colors.black)
    
    def _draw_footer(self, c):
        """Desenha rodapé discreto"""
        c.setFont("Helvetica", 6)
        c.setFillColor(colors.grey)
        c.drawString(self.margin, 3 * mm, "CROSS WMS")
    
    def _draw_qr_code(self, c, data, x, y, size):
        """Desenha QR code"""
        try:
            qr = qrcode.QRCode(version=1, box_size=1, border=1)
            qr.add_data(data)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            img_buffer = BytesIO()
            img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            c.drawImage(ImageReader(img_buffer), x, y, width=size, height=size)
        except Exception as e:
            logger.warning(f"Erro ao gerar QR Code: {e}")
            # Fallback: retângulo simples
            c.setStrokeColor(colors.black)
            c.setLineWidth(1)
            c.rect(x, y, size, size, fill=0, stroke=1)


def generate_transul_style_label(xml_content: str, pedido_number: str = None, 
                                area_code: str = "01", company_name: str = "TRANSUL",
                                company_subtitle: str = "TRANSPORTE",
                                paper_width_mm: int = 100, paper_height_mm: int = 150) -> BytesIO:
    """
    Função utilitária para gerar etiqueta estilo Transul
    
    Args:
        xml_content: Conteúdo XML da NFe
        pedido_number: Número do pedido
        area_code: Código da área
        company_name: Nome da empresa
        company_subtitle: Subtítulo da empresa
        paper_width_mm: Largura do papel em milímetros
        paper_height_mm: Altura do papel em milímetros
        
    Returns:
        BytesIO contendo o PDF da etiqueta
    """
    generator = TransulStyleLabelGenerator(
        company_name=company_name,
        company_subtitle=company_subtitle,
        paper_width_mm=paper_width_mm,
        paper_height_mm=paper_height_mm
    )
    
    return generator.generate_transul_label(
        xml_content=xml_content,
        pedido_number=pedido_number,
        area_code=area_code
    )


if __name__ == "__main__":
    # Teste básico
    print("Gerador de Etiquetas Estilo Transul - Pronto para uso")