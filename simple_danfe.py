"""
Gerador simples de DANFE em PDF
"""

import xml.etree.ElementTree as ET
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import logging

logger = logging.getLogger(__name__)

def generate_simple_danfe(xml_content: str, output_path: str) -> bool:
    """
    Gera um DANFE simplificado em PDF a partir do XML da nota fiscal
    
    Args:
        xml_content: Conteúdo XML da nota fiscal
        output_path: Caminho do arquivo PDF de saída
        
    Returns:
        True se gerado com sucesso, False caso contrário
    """
    try:
        # Parse XML
        root = ET.fromstring(xml_content)
        
        # Namespaces
        ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
        
        # Extrair dados básicos
        inf_nfe = root.find('.//nfe:infNFe', ns)
        if inf_nfe is None:
            logger.error("Elemento infNFe não encontrado no XML")
            return False
        
        # Dados da nota
        ide = inf_nfe.find('nfe:ide', ns)
        emit = inf_nfe.find('nfe:emit', ns)
        dest = inf_nfe.find('nfe:dest', ns)
        total = inf_nfe.find('.//nfe:total/nfe:ICMSTot', ns)
        
        # Criar PDF
        doc = SimpleDocTemplate(output_path, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Título
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=16,
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        elements.append(Paragraph("DANFE - Documento Auxiliar da Nota Fiscal Eletrônica", title_style))
        elements.append(Spacer(1, 20))
        
        # Dados da nota
        if ide is not None:
            nfe_data = [
                ['Série', get_text(ide, 'nfe:serie', ns)],
                ['Número', get_text(ide, 'nfe:nNF', ns)],
                ['Data Emissão', format_date(get_text(ide, 'nfe:dhEmi', ns))],
                ['Chave de Acesso', inf_nfe.get('Id', '').replace('NFe', '')]
            ]
            
            nfe_table = Table(nfe_data, colWidths=[80*mm, 100*mm])
            nfe_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(nfe_table)
            elements.append(Spacer(1, 20))
        
        # Dados do emitente
        if emit is not None:
            elements.append(Paragraph("EMITENTE", styles['Heading2']))
            
            emit_data = [
                ['Razão Social', get_text(emit, 'nfe:xNome', ns)],
                ['CNPJ', format_cnpj(get_text(emit, 'nfe:CNPJ', ns))],
                ['Endereço', get_endereco(emit, ns)],
                ['Município', get_text(emit.find('nfe:enderEmit', ns), 'nfe:xMun', ns)],
                ['UF', get_text(emit.find('nfe:enderEmit', ns), 'nfe:UF', ns)],
                ['CEP', format_cep(get_text(emit.find('nfe:enderEmit', ns), 'nfe:CEP', ns))]
            ]
            
            emit_table = Table(emit_data, colWidths=[40*mm, 140*mm])
            emit_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(emit_table)
            elements.append(Spacer(1, 15))
        
        # Dados do destinatário
        if dest is not None:
            elements.append(Paragraph("DESTINATÁRIO", styles['Heading2']))
            
            dest_data = [
                ['Razão Social', get_text(dest, 'nfe:xNome', ns)],
                ['CNPJ/CPF', format_cnpj_cpf(dest, ns)],
                ['Endereço', get_endereco(dest, ns)],
                ['Município', get_text(dest.find('nfe:enderDest', ns), 'nfe:xMun', ns)],
                ['UF', get_text(dest.find('nfe:enderDest', ns), 'nfe:UF', ns)],
                ['CEP', format_cep(get_text(dest.find('nfe:enderDest', ns), 'nfe:CEP', ns))]
            ]
            
            dest_table = Table(dest_data, colWidths=[40*mm, 140*mm])
            dest_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(dest_table)
            elements.append(Spacer(1, 15))
        
        # Produtos/Serviços
        products = inf_nfe.findall('.//nfe:det', ns)
        if products:
            elements.append(Paragraph("PRODUTOS/SERVIÇOS", styles['Heading2']))
            
            # Cabeçalho da tabela de produtos
            prod_header = [['Item', 'Descrição', 'Qtd', 'Valor Unit.', 'Valor Total']]
            prod_data = []
            
            for i, det in enumerate(products[:10], 1):  # Limitar a 10 itens
                prod = det.find('nfe:prod', ns)
                if prod is not None:
                    prod_data.append([
                        str(i),
                        get_text(prod, 'nfe:xProd', ns)[:30] + '...' if len(get_text(prod, 'nfe:xProd', ns)) > 30 else get_text(prod, 'nfe:xProd', ns),
                        get_text(prod, 'nfe:qCom', ns),
                        format_currency(get_text(prod, 'nfe:vUnCom', ns)),
                        format_currency(get_text(prod, 'nfe:vProd', ns))
                    ])
            
            if len(products) > 10:
                prod_data.append(['...', f'+ {len(products) - 10} itens adicionais', '', '', ''])
            
            prod_table = Table(prod_header + prod_data, colWidths=[15*mm, 80*mm, 20*mm, 30*mm, 35*mm])
            prod_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(prod_table)
            elements.append(Spacer(1, 15))
        
        # Totais
        if total is not None:
            elements.append(Paragraph("TOTAIS DA NOTA FISCAL", styles['Heading2']))
            
            total_data = [
                ['Base Cálculo ICMS', format_currency(get_text(total, 'nfe:vBC', ns))],
                ['Valor ICMS', format_currency(get_text(total, 'nfe:vICMS', ns))],
                ['Base Cálculo ICMS ST', format_currency(get_text(total, 'nfe:vBCST', ns))],
                ['Valor ICMS ST', format_currency(get_text(total, 'nfe:vST', ns))],
                ['Valor Total dos Produtos', format_currency(get_text(total, 'nfe:vProd', ns))],
                ['Valor Total da Nota', format_currency(get_text(total, 'nfe:vNF', ns))]
            ]
            
            total_table = Table(total_data, colWidths=[80*mm, 100*mm])
            total_table.setStyle(TableStyle([
                ('BACKGROUND', (0, -1), (-1, -1), colors.yellow),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            
            elements.append(total_table)
        
        # Gerar PDF
        doc.build(elements)
        logger.info(f"DANFE gerado com sucesso: {output_path}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao gerar DANFE: {str(e)}")
        return False

def get_text(element, xpath: str, ns: dict = None) -> str:
    """Obter texto de um elemento XML"""
    if element is None:
        return ""
    
    target = element.find(xpath, ns) if ns else element.find(xpath)
    return target.text if target is not None and target.text else ""

def get_endereco(element, ns: dict) -> str:
    """Formatar endereço completo"""
    if element is None:
        return ""
    
    endereco = element.find('nfe:enderEmit', ns) or element.find('nfe:enderDest', ns)
    if endereco is None:
        return ""
    
    logradouro = get_text(endereco, 'nfe:xLgr', ns)
    numero = get_text(endereco, 'nfe:nro', ns)
    complemento = get_text(endereco, 'nfe:xCpl', ns)
    bairro = get_text(endereco, 'nfe:xBairro', ns)
    
    endereco_completo = logradouro
    if numero:
        endereco_completo += f", {numero}"
    if complemento:
        endereco_completo += f", {complemento}"
    if bairro:
        endereco_completo += f" - {bairro}"
    
    return endereco_completo

def format_cnpj(cnpj: str) -> str:
    """Formatar CNPJ"""
    if not cnpj or len(cnpj) != 14:
        return cnpj
    
    return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"

def format_cnpj_cpf(element, ns: dict) -> str:
    """Formatar CNPJ ou CPF do destinatário"""
    if element is None:
        return ""
    
    cnpj = get_text(element, 'nfe:CNPJ', ns)
    if cnpj:
        return format_cnpj(cnpj)
    
    cpf = get_text(element, 'nfe:CPF', ns)
    if cpf and len(cpf) == 11:
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    
    return cpf

def format_cep(cep: str) -> str:
    """Formatar CEP"""
    if not cep or len(cep) != 8:
        return cep
    
    return f"{cep[:5]}-{cep[5:]}"

def format_date(date_str: str) -> str:
    """Formatar data"""
    if not date_str:
        return ""
    
    try:
        # Assumir formato ISO: 2020-05-07T14:30:00-03:00
        if 'T' in date_str:
            date_part = date_str.split('T')[0]
            year, month, day = date_part.split('-')
            return f"{day}/{month}/{year}"
    except:
        pass
    
    return date_str

def format_currency(value: str) -> str:
    """Formatar valor monetário"""
    if not value:
        return "0,00"
    
    try:
        float_value = float(value)
        return f"{float_value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    except:
        return value