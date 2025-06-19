"""
Gerador simples de DANFE a partir de XMLs de notas fiscais
"""

import os
import logging
import xml.etree.ElementTree as ET
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER, TA_LEFT

logger = logging.getLogger(__name__)

def extract_xml_data(xml_content: str):
    """Extract basic data from XML for DANFE generation"""
    try:
        # Clean XML content
        xml_clean = xml_content.replace(' xmlns="http://www.portalfiscal.inf.br/nfe"', '')
        root = ET.fromstring(xml_clean)
        
        # Find main elements
        inf_nfe = root.find('.//infNFe') or root.find('.//NFe//infNFe') or root
        
        # Extract basic info
        numero = get_xml_text(inf_nfe, './/nNF', 'S/N')
        serie = get_xml_text(inf_nfe, './/serie', '1')
        chave = get_xml_text(inf_nfe, './/chNFe', inf_nfe.get('Id', '').replace('NFe', ''))
        data_emissao = get_xml_text(inf_nfe, './/dhEmi', '')
        natureza = get_xml_text(inf_nfe, './/natOp', '')
        
        # Emitente
        emit = inf_nfe.find('.//emit')
        emit_nome = get_xml_text(emit, './/xNome', 'Emitente não informado') if emit is not None else 'Emitente não informado'
        emit_cnpj = format_cnpj(get_xml_text(emit, './/CNPJ', '')) if emit is not None else ''
        
        # Destinatário
        dest = inf_nfe.find('.//dest')
        dest_nome = get_xml_text(dest, './/xNome', 'Destinatário não informado') if dest is not None else 'Destinatário não informado'
        dest_doc = get_xml_text(dest, './/CNPJ', get_xml_text(dest, './/CPF', '')) if dest is not None else ''
        
        # Totais
        total = inf_nfe.find('.//total//ICMSTot')
        valor_total = get_xml_text(total, './/vNF', '0,00') if total is not None else '0,00'
        valor_produtos = get_xml_text(total, './/vProd', '0,00') if total is not None else '0,00'
        
        return {
            'numero': numero,
            'serie': serie,
            'chave': chave,
            'data_emissao': format_date(data_emissao),
            'natureza': natureza,
            'emit_nome': emit_nome,
            'emit_cnpj': emit_cnpj,
            'dest_nome': dest_nome,
            'dest_doc': format_cnpj(dest_doc) if len(dest_doc) == 14 else format_cpf(dest_doc),
            'valor_total': format_currency(valor_total),
            'valor_produtos': format_currency(valor_produtos)
        }
        
    except Exception as e:
        logger.error(f"Error parsing XML: {e}")
        return None

def get_xml_text(element, xpath, default=''):
    """Get text from XML element"""
    if element is None:
        return default
    found = element.find(xpath)
    return found.text if found is not None and found.text else default

def format_cnpj(cnpj):
    """Format CNPJ"""
    if not cnpj or len(cnpj) != 14:
        return cnpj
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"

def format_cpf(cpf):
    """Format CPF"""
    if not cpf or len(cpf) != 11:
        return cpf
    return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"

def format_date(date_str):
    """Format date"""
    if not date_str:
        return ""
    try:
        if 'T' in date_str:
            from datetime import datetime
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%d/%m/%Y')
        return date_str
    except:
        return date_str

def format_currency(value):
    """Format currency"""
    if not value:
        return "0,00"
    try:
        val = float(value)
        return f"{val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return value

def generate_simple_danfe(xml_content: str, output_path: str) -> bool:
    """Generate a simple DANFE PDF from XML content"""
    try:
        logger.info(f"Generating simple DANFE: {output_path}")
        
        # Extract data from XML
        data = extract_xml_data(xml_content)
        if not data:
            logger.error("Failed to extract data from XML")
            return False
        
        # Create PDF document
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=2*cm,
            leftMargin=2*cm,
            topMargin=2*cm,
            bottomMargin=2*cm
        )
        
        # Get styles
        styles = getSampleStyleSheet()
        
        # Build document content
        elements = []
        
        # Title
        title = Paragraph("<b>DANFE - Documento Auxiliar da Nota Fiscal Eletrônica</b>", styles['Title'])
        title.alignment = TA_CENTER
        elements.append(title)
        elements.append(Spacer(1, 20))
        
        # Basic info table
        basic_data = [
            ['Número:', data['numero'], 'Série:', data['serie']],
            ['Data de Emissão:', data['data_emissao'], 'Modelo:', '55'],
            ['Natureza da Operação:', data['natureza'], '', '']
        ]
        
        basic_table = Table(basic_data, colWidths=[3*cm, 4*cm, 3*cm, 4*cm])
        basic_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(basic_table)
        elements.append(Spacer(1, 15))
        
        # Access key
        key_data = [['Chave de Acesso:', data['chave']]]
        key_table = Table(key_data, colWidths=[3*cm, 11*cm])
        key_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, 0), colors.lightgrey),
            ('FONTNAME', (0, 0), (0, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(key_table)
        elements.append(Spacer(1, 15))
        
        # Emitente
        emitente_title = Paragraph("<b>EMITENTE</b>", styles['Heading2'])
        emitente_title.alignment = TA_CENTER
        elements.append(emitente_title)
        
        emitente_data = [
            ['Razão Social:', data['emit_nome']],
            ['CNPJ:', data['emit_cnpj']]
        ]
        
        emitente_table = Table(emitente_data, colWidths=[3*cm, 11*cm])
        emitente_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(emitente_table)
        elements.append(Spacer(1, 15))
        
        # Destinatário
        dest_title = Paragraph("<b>DESTINATÁRIO</b>", styles['Heading2'])
        dest_title.alignment = TA_CENTER
        elements.append(dest_title)
        
        dest_data = [
            ['Razão Social:', data['dest_nome']],
            ['CNPJ/CPF:', data['dest_doc']]
        ]
        
        dest_table = Table(dest_data, colWidths=[3*cm, 11*cm])
        dest_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        elements.append(dest_table)
        elements.append(Spacer(1, 15))
        
        # Totais
        totais_title = Paragraph("<b>TOTAIS</b>", styles['Heading2'])
        totais_title.alignment = TA_CENTER
        elements.append(totais_title)
        
        totais_data = [
            ['Valor dos Produtos:', data['valor_produtos']],
            ['VALOR TOTAL DA NF-e:', data['valor_total']]
        ]
        
        totais_table = Table(totais_data, colWidths=[3*cm, 11*cm])
        totais_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('BACKGROUND', (0, -1), (-1, -1), colors.yellow),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ]))
        elements.append(totais_table)
        
        # Build PDF
        doc.build(elements)
        
        logger.info(f"Simple DANFE generated successfully: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error generating simple DANFE: {e}")
        return False