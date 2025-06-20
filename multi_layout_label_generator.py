"""
Gerador de Etiquetas com Múltiplos Layouts
Layout 1: Moderno com fundos cinza
Layout 2: Inspirado Transul com faixas pretas
"""

import os
from io import BytesIO
from reportlab.lib.pagesizes import A4, A5
from reportlab.lib.colors import black, white, Color
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import qrcode
from PIL import Image as PILImage
import xml.etree.ElementTree as ET

def parse_xml_data(xml_file_path):
    """Extrair dados do XML para a etiqueta"""
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
        
        # Namespace NFe
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        
        # Dados da NF
        inf_nfe = root.find('.//nfe:infNFe', ns)
        ide = inf_nfe.find('nfe:ide', ns) if inf_nfe else None
        emit = inf_nfe.find('nfe:emit', ns) if inf_nfe else None
        dest = inf_nfe.find('nfe:dest', ns) if inf_nfe else None
        total = inf_nfe.find('.//nfe:total/nfe:ICMSTot', ns) if inf_nfe else None
        transp = inf_nfe.find('nfe:transp', ns) if inf_nfe else None
        
        # Volumes
        vol_elements = inf_nfe.findall('.//nfe:vol', ns) if inf_nfe else []
        
        return {
            'numero_nf': ide.find('nfe:nNF', ns).text if ide is not None and ide.find('nfe:nNF', ns) is not None else 'N/A',
            'serie_nf': ide.find('nfe:serie', ns).text if ide is not None and ide.find('nfe:serie', ns) is not None else 'N/A',
            'chave_nfe': inf_nfe.get('Id', '').replace('NFe', '') if inf_nfe else 'N/A',
            
            # Emitente (Remetente)
            'remetente_razao': emit.find('nfe:xNome', ns).text if emit is not None and emit.find('nfe:xNome', ns) is not None else 'N/A',
            'remetente_cidade': emit.find('.//nfe:xMun', ns).text if emit is not None and emit.find('.//nfe:xMun', ns) is not None else 'N/A',
            'remetente_uf': emit.find('.//nfe:UF', ns).text if emit is not None and emit.find('.//nfe:UF', ns) is not None else 'N/A',
            
            # Destinatário
            'destinatario_razao': dest.find('nfe:xNome', ns).text if dest is not None and dest.find('nfe:xNome', ns) is not None else 'N/A',
            'destinatario_endereco': f"{dest.find('.//nfe:xLgr', ns).text if dest.find('.//nfe:xLgr', ns) is not None else ''}, {dest.find('.//nfe:nro', ns).text if dest.find('.//nfe:nro', ns) is not None else ''}, {dest.find('.//nfe:xBairro', ns).text if dest.find('.//nfe:xBairro', ns) is not None else ''}".strip(', ') if dest else 'N/A',
            'destinatario_cidade': dest.find('.//nfe:xMun', ns).text if dest is not None and dest.find('.//nfe:xMun', ns) is not None else 'N/A',
            'destinatario_uf': dest.find('.//nfe:UF', ns).text if dest is not None and dest.find('.//nfe:UF', ns) is not None else 'N/A',
            'destinatario_cep': dest.find('.//nfe:CEP', ns).text if dest is not None and dest.find('.//nfe:CEP', ns) is not None else 'N/A',
            
            # Valores e pesos
            'valor_total': float(total.find('nfe:vNF', ns).text) if total is not None and total.find('nfe:vNF', ns) is not None else 0.0,
            'peso_bruto': sum([float(vol.find('nfe:pesoB', ns).text) for vol in vol_elements if vol.find('nfe:pesoB', ns) is not None]) if vol_elements else 0.0,
            'quantidade_volumes': len(vol_elements) if vol_elements else 1
        }
    except Exception as e:
        print(f"Erro ao processar XML: {e}")
        return {
            'numero_nf': 'N/A', 'serie_nf': 'N/A', 'chave_nfe': 'N/A',
            'remetente_razao': 'N/A', 'remetente_cidade': 'N/A', 'remetente_uf': 'N/A',
            'destinatario_razao': 'N/A', 'destinatario_endereco': 'N/A', 
            'destinatario_cidade': 'N/A', 'destinatario_uf': 'N/A', 'destinatario_cep': 'N/A',
            'valor_total': 0.0, 'peso_bruto': 0.0, 'quantidade_volumes': 1
        }

def create_qr_code(data):
    """Criar QR Code"""
    qr = qrcode.QRCode(version=1, box_size=3, border=1)
    qr.add_data(data)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_buffer = BytesIO()
    img.save(img_buffer, format='PNG')
    img_buffer.seek(0)
    
    # Return a reportlab-compatible ImageReader
    from reportlab.lib.utils import ImageReader
    return ImageReader(img_buffer)

def generate_label_layout1(canvas_obj, xml_data, company_data, volume_info, paper_size):
    """Layout 1: Moderno com fundos cinza"""
    width, height = paper_size
    
    # Cores Layout 1
    bg_color = Color(0.95, 0.95, 0.95)  # Cinza claro
    border_color = Color(0.7, 0.7, 0.7)  # Cinza médio
    text_color = black
    
    # Cabeçalho da empresa
    y_pos = height - 30
    
    if company_data.get('logo_path') and isinstance(company_data['logo_path'], str) and os.path.exists(company_data['logo_path']):
        try:
            canvas_obj.drawImage(company_data['logo_path'], 20, y_pos - 25, width=60, height=25, preserveAspectRatio=True)
            x_text = 90
        except:
            x_text = 20
    else:
        x_text = 20
    
    canvas_obj.setFont("Helvetica-Bold", 14)
    canvas_obj.drawString(x_text, y_pos - 10, company_data.get('name', 'Empresa'))
    if company_data.get('subtitle'):
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.drawString(x_text, y_pos - 25, company_data['subtitle'])
    
    y_pos -= 50
    
    # Seções com fundo cinza
    sections = [
        f"NF: {xml_data['numero_nf']}/{xml_data['serie_nf']}",
        f"Pedido: {xml_data['numero_nf']}",
        f"Remetente: {xml_data['remetente_razao'][:40]}",
        f"Destinatário: {xml_data['destinatario_razao'][:40]}"
    ]
    
    for section in sections:
        # Fundo cinza
        canvas_obj.setFillColor(bg_color)
        canvas_obj.rect(20, y_pos - 20, width - 40, 18, fill=1, stroke=1)
        canvas_obj.setStrokeColor(border_color)
        
        # Texto
        canvas_obj.setFillColor(text_color)
        canvas_obj.setFont("Helvetica-Bold", 10)
        canvas_obj.drawString(25, y_pos - 15, section)
        y_pos -= 25
    
    # Endereço destinatário (30% do espaço)
    y_pos -= 10
    canvas_obj.setFont("Helvetica", 9)
    endereco_lines = [
        xml_data['destinatario_endereco'],
        f"{xml_data['destinatario_cidade']}/{xml_data['destinatario_uf']} - CEP: {xml_data['destinatario_cep']}"
    ]
    
    for line in endereco_lines:
        if line.strip():
            canvas_obj.drawString(25, y_pos, line[:60])
            y_pos -= 12
    
    # Seção inferior com peso, volume e área
    y_pos = 60
    
    # Peso
    canvas_obj.setFillColor(bg_color)
    canvas_obj.rect(20, y_pos, 80, 20, fill=1, stroke=1)
    canvas_obj.setFillColor(text_color)
    canvas_obj.setFont("Helvetica-Bold", 10)
    canvas_obj.drawString(25, y_pos + 8, f"Peso: {volume_info['peso']:.1f}kg")
    
    # Volume
    canvas_obj.setFillColor(bg_color)
    canvas_obj.rect(110, y_pos, 80, 20, fill=1, stroke=1)
    canvas_obj.setFillColor(text_color)
    canvas_obj.drawString(115, y_pos + 8, f"Volume: {volume_info['volume_atual']}/{volume_info['total_volumes']}")
    
    # Área (canto direito)
    area_x = width - 80
    canvas_obj.setFillColor(bg_color)
    canvas_obj.rect(area_x, y_pos, 60, 30, fill=1, stroke=1)
    canvas_obj.setFillColor(text_color)
    canvas_obj.setFont("Helvetica-Bold", 8)
    text_width = canvas_obj.stringWidth("ÁREA", "Helvetica-Bold", 8)
    canvas_obj.drawString(area_x + 30 - text_width/2, y_pos + 20, "ÁREA")
    canvas_obj.setFont("Helvetica-Bold", 16)
    area_text = company_data.get('area_code', '01')
    area_width = canvas_obj.stringWidth(area_text, "Helvetica-Bold", 16)
    canvas_obj.drawString(area_x + 30 - area_width/2, y_pos + 8, area_text)
    
    # QR Code
    if xml_data['chave_nfe'] != 'N/A':
        qr_buffer = create_qr_code(xml_data['chave_nfe'])
        canvas_obj.drawImage(qr_buffer, width - 60, height - 80, width=40, height=40)

def generate_label_layout2(canvas_obj, xml_data, company_data, volume_info, paper_size):
    """Layout 2: Inspirado Transul com faixas pretas"""
    width, height = paper_size
    
    # Cores Layout 2
    black_bg = black
    white_text = white
    
    # Cabeçalho da empresa (faixa preta)
    y_pos = height - 30
    
    # Faixa preta superior
    canvas_obj.setFillColor(black_bg)
    canvas_obj.rect(0, y_pos - 30, width, 30, fill=1, stroke=0)
    
    # Logo e nome da empresa em branco
    canvas_obj.setFillColor(white_text)
    if company_data.get('logo_path') and isinstance(company_data['logo_path'], str) and os.path.exists(company_data['logo_path']):
        try:
            canvas_obj.drawImage(company_data['logo_path'], 20, y_pos - 25, width=60, height=25, preserveAspectRatio=True)
            x_text = 90
        except:
            x_text = 20
    else:
        x_text = 20
    
    canvas_obj.setFont("Helvetica-Bold", 14)
    canvas_obj.drawString(x_text, y_pos - 10, company_data.get('name', 'Empresa'))
    if company_data.get('subtitle'):
        canvas_obj.setFont("Helvetica", 10)
        canvas_obj.drawString(x_text, y_pos - 25, company_data['subtitle'])
    
    y_pos -= 50
    
    # Seções com faixas pretas alternadas
    sections = [
        f"NF: {xml_data['numero_nf']}/{xml_data['serie_nf']}",
        f"Pedido: {xml_data['numero_nf']}",
        f"Remetente: {xml_data['remetente_razao'][:40]}",
        f"Destinatário: {xml_data['destinatario_razao'][:40]}"
    ]
    
    for i, section in enumerate(sections):
        # Faixa preta
        canvas_obj.setFillColor(black_bg)
        canvas_obj.rect(0, y_pos - 20, width, 18, fill=1, stroke=0)
        
        # Texto branco
        canvas_obj.setFillColor(white_text)
        canvas_obj.setFont("Helvetica-Bold", 10)
        canvas_obj.drawString(25, y_pos - 15, section)
        y_pos -= 25
    
    # Endereço destinatário (fundo branco, texto preto)
    y_pos -= 10
    canvas_obj.setFillColor(black)
    canvas_obj.setFont("Helvetica", 9)
    endereco_lines = [
        xml_data['destinatario_endereco'],
        f"{xml_data['destinatario_cidade']}/{xml_data['destinatario_uf']} - CEP: {xml_data['destinatario_cep']}"
    ]
    
    for line in endereco_lines:
        if line.strip():
            canvas_obj.drawString(25, y_pos, line[:60])
            y_pos -= 12
    
    # Seção inferior com faixas pretas
    y_pos = 60
    
    # Peso (faixa preta)
    canvas_obj.setFillColor(black_bg)
    canvas_obj.rect(20, y_pos, 80, 20, fill=1, stroke=0)
    canvas_obj.setFillColor(white_text)
    canvas_obj.setFont("Helvetica-Bold", 10)
    canvas_obj.drawString(25, y_pos + 8, f"Peso: {volume_info['peso']:.1f}kg")
    
    # Volume (faixa preta)
    canvas_obj.setFillColor(black_bg)
    canvas_obj.rect(110, y_pos, 80, 20, fill=1, stroke=0)
    canvas_obj.setFillColor(white_text)
    canvas_obj.drawString(115, y_pos + 8, f"Volume: {volume_info['volume_atual']}/{volume_info['total_volumes']}")
    
    # Área (faixa preta no canto direito)
    area_x = width - 80
    canvas_obj.setFillColor(black_bg)
    canvas_obj.rect(area_x, y_pos, 60, 30, fill=1, stroke=0)
    canvas_obj.setFillColor(white_text)
    canvas_obj.setFont("Helvetica-Bold", 8)
    text_width = canvas_obj.stringWidth("ÁREA", "Helvetica-Bold", 8)
    canvas_obj.drawString(area_x + 30 - text_width/2, y_pos + 20, "ÁREA")
    canvas_obj.setFont("Helvetica-Bold", 16)
    area_text = company_data.get('area_code', '01')
    area_width = canvas_obj.stringWidth(area_text, "Helvetica-Bold", 16)
    canvas_obj.drawString(area_x + 30 - area_width/2, y_pos + 8, area_text)
    
    # QR Code (fundo branco)
    if xml_data['chave_nfe'] != 'N/A':
        # Fundo branco para QR code
        canvas_obj.setFillColor(white)
        canvas_obj.rect(width - 65, height - 85, 50, 50, fill=1, stroke=1)
        
        qr_buffer = create_qr_code(xml_data['chave_nfe'])
        canvas_obj.drawImage(qr_buffer, width - 60, height - 80, width=40, height=40)

def generate_multi_layout_labels(xml_file_path, company_data, paper_config, layout_style='layout1'):
    """Gerador principal com múltiplos layouts"""
    
    # Parse XML data
    xml_data = parse_xml_data(xml_file_path)
    
    # Configurações de papel
    paper_sizes = {
        'A4': A4,
        'A5': A5,
        '10x15cm': (10*cm, 15*cm),
        '7x10cm': (7*cm, 10*cm),
        '5x8cm': (5*cm, 8*cm),
        'custom': (paper_config.get('custom_width', 10)*cm, paper_config.get('custom_height', 15)*cm)
    }
    
    paper_size = paper_sizes.get(paper_config['size'], (10*cm, 15*cm))
    
    # Criar buffer para PDF
    buffer = BytesIO()
    
    # Configurar volumes
    total_volumes = paper_config.get('total_volumes', xml_data['quantidade_volumes'])
    volume_weights = paper_config.get('volume_weights', [xml_data['peso_bruto']] * total_volumes)
    
    # Gerar etiquetas para cada volume
    for i in range(total_volumes):
        if i > 0:
            # Criar nova página para cada volume
            buffer_temp = BytesIO()
            c = canvas.Canvas(buffer_temp, pagesize=paper_size)
        else:
            c = canvas.Canvas(buffer, pagesize=paper_size)
        
        volume_info = {
            'volume_atual': i + 1,
            'total_volumes': total_volumes,
            'peso': volume_weights[i] if i < len(volume_weights) else xml_data['peso_bruto']
        }
        
        # Escolher layout
        if layout_style == 'layout2':
            generate_label_layout2(c, xml_data, company_data, volume_info, paper_size)
        else:
            generate_label_layout1(c, xml_data, company_data, volume_info, paper_size)
        
        c.save()
        
        if i > 0:
            # Adicionar ao buffer principal
            buffer_temp.seek(0)
            # Merge PDFs here if needed
    
    buffer.seek(0)
    return buffer

def generate_custom_label_with_layout(xml_id, user, paper_config, layout_style='layout1'):
    """Função principal para integração com o sistema"""
    from models import XMLFile
    from new_app import db
    
    # Buscar XML
    xml_file = XMLFile.query.filter_by(id=xml_id, user_id=user.id).first()
    if not xml_file:
        return None
    
    # Dados da empresa
    company_data = {
        'name': user.company_name or 'Sua Empresa',
        'subtitle': user.company_subtitle,
        'logo_path': user.company_logo_path,
        'area_code': user.default_area_code or '01'
    }
    
    # Gerar etiquetas
    return generate_multi_layout_labels(
        xml_file.file_path, 
        company_data, 
        paper_config, 
        layout_style
    )