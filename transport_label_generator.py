"""
Gerador de Etiquetas de Transporte
Baseado no modelo de etiquetas do CrossWMS
Gera etiquetas profissionais a partir de dados XML NFe
"""
import logging
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
import qrcode
from qrcode.constants import ERROR_CORRECT_L
from xml_processor import extract_xml_data
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)

class TransportLabelGenerator:
    """Gerador de etiquetas de transporte baseado no modelo CrossWMS"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Configura estilos customizados para as etiquetas"""
        # Estilo para títulos das seções (fundo preto, texto branco)
        self.black_header_style = ParagraphStyle(
            'BlackHeader',
            parent=self.styles['Normal'],
            fontSize=14,
            textColor=colors.white,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold',
            leftIndent=5,
            rightIndent=5,
            spaceAfter=2,
            spaceBefore=2
        )
        
        # Estilo para dados principais
        self.data_style = ParagraphStyle(
            'DataStyle',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.black,
            alignment=TA_LEFT,
            fontName='Helvetica',
            leftIndent=5
        )
        
        # Estilo para área de código
        self.area_style = ParagraphStyle(
            'AreaStyle',
            parent=self.styles['Normal'],
            fontSize=24,
            textColor=colors.white,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
    
    def format_cnpj(self, cnpj):
        """Formata CNPJ no padrão XX.XXX.XXX/XXXX-XX"""
        if not cnpj or len(cnpj) < 14:
            return cnpj
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:14]}"
    
    def format_cep(self, cep):
        """Formata CEP no padrão XXXXX-XXX"""
        if not cep or len(cep) < 8:
            return cep
        return f"{cep[:5]}-{cep[5:]}"
    
    def generate_qr_code(self, data, size=60):
        """Gera QR Code para a etiqueta"""
        try:
            qr_code = qrcode.QRCode(
                version=1,
                error_correction=ERROR_CORRECT_L,
                box_size=3,
                border=1,
            )
            qr_code.add_data(data)
            qr_code.make(fit=True)
            
            img = qr_code.make_image(fill_color="black", back_color="white")
            
            # Converter para formato que o ReportLab aceita
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            buffer.seek(0)
            
            return Image(buffer, width=size, height=size)
        except Exception as e:
            logger.error(f"Erro ao gerar QR Code: {e}")
            return None
    
    def create_header_cell(self, text, background_color=colors.black):
        """Cria célula com fundo colorido e texto branco"""
        return Paragraph(f"<para>{text}</para>", self.black_header_style)
    
    def create_data_cell(self, text):
        """Cria célula com dados"""
        return Paragraph(f"<para>{text}</para>", self.data_style)
    
    def generate_transport_label(self, xml_content, pedido_number=None, area_code="01"):
        """
        Gera etiqueta de transporte baseada no XML NFe
        
        Args:
            xml_content: Conteúdo XML da NFe
            pedido_number: Número do pedido (opcional)
            area_code: Código da área de armazenagem
            
        Returns:
            BytesIO: Buffer com PDF da etiqueta gerada
        """
        try:
            # Extrair dados do XML
            nf_data = extract_xml_data(xml_content)
            
            if not nf_data:
                raise ValueError("Não foi possível extrair dados do XML")
            
            # Configurar documento
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=(210*mm, 148*mm),  # Formato paisagem A6
                rightMargin=5*mm,
                leftMargin=5*mm,
                topMargin=5*mm,
                bottomMargin=5*mm
            )
            
            # Elementos da etiqueta
            elements = []
            
            # ID da etiqueta no topo
            id_text = f"ID: {nf_data.get('numero_nf', '')}-001-001-001"
            id_para = Paragraph(f"<para fontSize='10'>{id_text}</para>", self.data_style)
            elements.append(id_para)
            elements.append(Spacer(1, 3*mm))
            
            # Tabela principal com informações
            main_data = []
            
            # Linha 1: NF + QR Code
            nf_number = nf_data.get('numero_nf', 'N/A')
            qr_data = nf_data.get('chave_acesso', nf_number)
            qr_code = self.generate_qr_code(qr_data, size=40)
            
            nf_row = [
                [self.create_header_cell(f"NF: {nf_number}"), qr_code if qr_code else ""]
            ]
            
            # Linha 2: Pedido
            pedido_display = pedido_number or nf_data.get('numero_nf', 'N/A')
            pedido_row = [
                [self.create_header_cell(f"Pedido: {pedido_display}"), ""]
            ]
            
            # Linha 3: Remetente
            remetente = nf_data.get('nome_emitente', 'N/A')
            if len(remetente) > 35:
                remetente = remetente[:35] + "..."
            remetente_row = [
                [self.create_header_cell(f"Remetente: {remetente}"), ""]
            ]
            
            # Linha 4: Destinatário e endereço
            destinatario = nf_data.get('nome_destinatario', 'N/A')
            endereco = nf_data.get('endereco_destinatario', '')
            numero = nf_data.get('numero_destinatario', '')
            cidade = nf_data.get('cidade_destinatario', '')
            uf = nf_data.get('uf_destinatario', '')
            cep = self.format_cep(nf_data.get('cep_destinatario', ''))
            
            endereco_completo = f"{endereco}"
            if numero:
                endereco_completo += f", {numero}"
            if cidade and uf:
                endereco_completo += f" - {cidade}, CEP: {cep}"
            
            dest_info = [
                f"Destinatário: {destinatario}",
                f"Endereço: {endereco_completo}"
            ]
            
            # Linha 5: Cidade/UF
            cidade_uf = f"{cidade} {uf}" if cidade and uf else "N/A"
            cidade_row = [
                [self.create_header_cell(f"Cidade/UF: {cidade_uf}"), ""]
            ]
            
            # Linha 6: Peso e Volume
            peso = nf_data.get('peso_bruto', nf_data.get('peso_liquido', '0'))
            if peso and peso != '0':
                peso = f"{float(peso):.3f}" if '.' in peso else peso
            else:
                peso = "N/A"
            
            volume = nf_data.get('quantidade_volumes', '1')
            transportadora = nf_data.get('transportadora', 'TRANSUL TRANSPORTE')
            
            peso_info = [
                f"Peso: {peso}",
                f"Transportadora: {transportadora}"
            ]
            
            volume_row = [
                [self.create_header_cell(f"Volume: 1/{volume}"), ""]
            ]
            
            # Criar tabela principal
            table_data = []
            table_data.extend(nf_row)
            table_data.extend(pedido_row)
            table_data.extend(remetente_row)
            
            # Adicionar informações do destinatário
            for info in dest_info:
                table_data.append([self.create_data_cell(info), ""])
            
            table_data.extend(cidade_row)
            
            # Adicionar informações de peso
            for info in peso_info:
                table_data.append([self.create_data_cell(info), ""])
            
            table_data.extend(volume_row)
            
            # Criar tabela
            main_table = Table(
                table_data,
                colWidths=[140*mm, 50*mm],
                rowHeights=[8*mm] * len(table_data)
            )
            
            # Estilo da tabela
            table_style = TableStyle([
                # Bordas
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                
                # Cabeçalhos com fundo preto
                ('BACKGROUND', (0, 0), (0, 0), colors.black),  # NF
                ('BACKGROUND', (0, 1), (0, 1), colors.black),  # Pedido
                ('BACKGROUND', (0, 2), (0, 2), colors.black),  # Remetente
                ('BACKGROUND', (0, 5), (0, 5), colors.black),  # Cidade/UF
                ('BACKGROUND', (0, -1), (0, -1), colors.black),  # Volume
                
                # QR Code
                ('SPAN', (1, 0), (1, 2)),  # QR code ocupa 3 linhas
                ('ALIGN', (1, 0), (1, -1), 'CENTER'),
                ('VALIGN', (1, 0), (1, -1), 'MIDDLE'),
            ])
            
            main_table.setStyle(table_style)
            elements.append(main_table)
            
            # Espaço antes da área
            elements.append(Spacer(1, 10*mm))
            
            # Caixa da área (canto inferior direito)
            area_table = Table(
                [[self.create_header_cell("ÁREA"), ""],
                 [Paragraph(f"<para fontSize='24' alignment='center'><b>{area_code}</b></para>", 
                           ParagraphStyle('AreaNumber', fontSize=24, alignment=TA_CENTER, fontName='Helvetica-Bold')), ""]],
                colWidths=[120*mm, 70*mm],
                rowHeights=[8*mm, 15*mm]
            )
            
            area_style = TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.black),
                ('GRID', (0, 0), (0, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('ALIGN', (0, 1), (0, 1), 'CENTER'),
            ])
            
            area_table.setStyle(area_style)
            elements.append(area_table)
            
            # Rodapé
            elements.append(Spacer(1, 5*mm))
            footer = Paragraph("<para fontSize='8' alignment='left'>CROSS WMS</para>", self.data_style)
            elements.append(footer)
            
            # Construir PDF
            doc.build(elements)
            buffer.seek(0)
            
            logger.info(f"Etiqueta gerada com sucesso para NF {nf_number}")
            return buffer
            
        except Exception as e:
            logger.error(f"Erro ao gerar etiqueta: {e}")
            raise
    
    def generate_batch_labels(self, xml_list, area_code="01"):
        """
        Gera múltiplas etiquetas em lote
        
        Args:
            xml_list: Lista de tuplas (xml_content, pedido_number)
            area_code: Código da área
            
        Returns:
            BytesIO: Buffer com PDF contendo todas as etiquetas
        """
        try:
            buffer = BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                rightMargin=10*mm,
                leftMargin=10*mm,
                topMargin=10*mm,
                bottomMargin=10*mm
            )
            
            elements = []
            
            for i, (xml_content, pedido_number) in enumerate(xml_list):
                if i > 0:
                    elements.append(Spacer(1, 20*mm))  # Espaço entre etiquetas
                
                # Gerar etiqueta individual e adicionar aos elementos
                label_buffer = self.generate_transport_label(xml_content, pedido_number, area_code)
                # Aqui você poderia adicionar a etiqueta como imagem ou redesenhar
                
            doc.build(elements)
            buffer.seek(0)
            
            return buffer
            
        except Exception as e:
            logger.error(f"Erro ao gerar etiquetas em lote: {e}")
            raise

# Funções de conveniência
def generate_label_from_xml_file(xml_file_path, pedido_number=None, area_code="01"):
    """Gera etiqueta a partir de arquivo XML"""
    try:
        with open(xml_file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        generator = TransportLabelGenerator()
        return generator.generate_transport_label(xml_content, pedido_number, area_code)
        
    except Exception as e:
        logger.error(f"Erro ao gerar etiqueta do arquivo {xml_file_path}: {e}")
        raise

def generate_label_from_database_xml(xml_id, pedido_number=None, area_code="01"):
    """Gera etiqueta a partir de XML no banco de dados"""
    try:
        from models import XMLFile
        
        xml_file = XMLFile.query.get(xml_id)
        if not xml_file:
            raise ValueError(f"XML com ID {xml_id} não encontrado")
        
        generator = TransportLabelGenerator()
        return generator.generate_transport_label(xml_file.xml_content, pedido_number, area_code)
        
    except Exception as e:
        logger.error(f"Erro ao gerar etiqueta do XML ID {xml_id}: {e}")
        raise