"""
Gerador simplificado de DANFE com ReportLab
Versão focada na funcionalidade essencial e design visual atrativo
"""

import os
import xml.etree.ElementTree as ET
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import logging

logger = logging.getLogger(__name__)

class SimpleDanfeGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Configurar estilos personalizados para o DANFE"""
        # Título principal
        self.styles.add(ParagraphStyle(
            name='DANFETitle',
            parent=self.styles['Title'],
            fontSize=16,
            textColor=colors.darkblue,
            alignment=TA_CENTER,
            spaceAfter=20
        ))
        
        # Subtítulos
        self.styles.add(ParagraphStyle(
            name='DANFESubtitle',
            parent=self.styles['Heading2'],
            fontSize=12,
            textColor=colors.darkgreen,
            alignment=TA_LEFT,
            spaceBefore=10,
            spaceAfter=10
        ))
        
        # Texto normal
        self.styles.add(ParagraphStyle(
            name='DANFENormal',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_LEFT
        ))

    def extract_xml_data(self, xml_content: str) -> dict:
        """Extrair dados essenciais do XML da NFe"""
        try:
            root = ET.fromstring(xml_content)
            
            # Namespace NFe
            ns = {'nfe': 'http://www.portalfiscal.inf.br/nfe'}
            
            # Informações básicas
            inf_nfe = root.find('.//nfe:infNFe', ns)
            if inf_nfe is None:
                logger.error("Elemento infNFe não encontrado")
                return {}
            
            # Dados da NFe
            ide = inf_nfe.find('nfe:ide', ns)
            emit = inf_nfe.find('nfe:emit', ns)
            dest = inf_nfe.find('nfe:dest', ns)
            total = inf_nfe.find('nfe:total/nfe:ICMSTot', ns)
            
            data = {
                'numero': self.get_text(ide, 'nfe:nNF', ns) if ide is not None else '',
                'serie': self.get_text(ide, 'nfe:serie', ns) if ide is not None else '',
                'data_emissao': self.format_date(self.get_text(ide, 'nfe:dhEmi', ns)) if ide is not None else '',
                'chave_acesso': inf_nfe.get('Id', '').replace('NFe', '') if inf_nfe is not None else '',
                
                # Emitente
                'emit_nome': self.get_text(emit, 'nfe:xNome', ns) if emit is not None else '',
                'emit_cnpj': self.format_cnpj(self.get_text(emit, 'nfe:CNPJ', ns)) if emit is not None else '',
                'emit_endereco': self.extract_address(emit, ns) if emit is not None else '',
                
                # Destinatário
                'dest_nome': self.get_text(dest, 'nfe:xNome', ns) if dest is not None else '',
                'dest_doc': self.format_document(dest, ns) if dest is not None else '',
                'dest_endereco': self.extract_address(dest, ns) if dest is not None else '',
                
                # Totais
                'valor_produtos': self.format_currency(self.get_text(total, 'nfe:vProd', ns)) if total is not None else '0,00',
                'valor_total': self.format_currency(self.get_text(total, 'nfe:vNF', ns)) if total is not None else '0,00',
                'valor_icms': self.format_currency(self.get_text(total, 'nfe:vICMS', ns)) if total is not None else '0,00',
                
                # Produtos
                'produtos': self.extract_products(inf_nfe, ns)
            }
            
            return data
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados do XML: {e}")
            return {}
    
    def get_text(self, element, xpath: str, ns: dict) -> str:
        """Obter texto de um elemento XML com namespace"""
        if element is None:
            return ""
        found = element.find(xpath, ns)
        return found.text if found is not None and found.text else ""
    
    def extract_address(self, element, ns: dict) -> str:
        """Extrair endereço completo"""
        if element is None:
            return ""
        
        endereco = element.find('nfe:enderEmit', ns) or element.find('nfe:enderDest', ns)
        if endereco is None:
            return ""
        
        parts = []
        logradouro = self.get_text(endereco, 'nfe:xLgr', ns)
        numero = self.get_text(endereco, 'nfe:nro', ns)
        bairro = self.get_text(endereco, 'nfe:xBairro', ns)
        cidade = self.get_text(endereco, 'nfe:xMun', ns)
        uf = self.get_text(endereco, 'nfe:UF', ns)
        cep = self.get_text(endereco, 'nfe:CEP', ns)
        
        if logradouro and numero:
            parts.append(f"{logradouro}, {numero}")
        elif logradouro:
            parts.append(logradouro)
        
        if bairro:
            parts.append(bairro)
        
        if cidade and uf:
            parts.append(f"{cidade}/{uf}")
        
        if cep:
            parts.append(f"CEP: {self.format_cep(cep)}")
        
        return " - ".join(parts)
    
    def extract_products(self, inf_nfe, ns: dict) -> list:
        """Extrair lista de produtos"""
        produtos = []
        dets = inf_nfe.findall('nfe:det', ns)
        
        for det in dets:
            prod = det.find('nfe:prod', ns)
            if prod is not None:
                produto = {
                    'codigo': self.get_text(prod, 'nfe:cProd', ns),
                    'descricao': self.get_text(prod, 'nfe:xProd', ns),
                    'quantidade': self.get_text(prod, 'nfe:qCom', ns),
                    'unidade': self.get_text(prod, 'nfe:uCom', ns),
                    'valor_unitario': self.format_currency(self.get_text(prod, 'nfe:vUnCom', ns)),
                    'valor_total': self.format_currency(self.get_text(prod, 'nfe:vProd', ns))
                }
                produtos.append(produto)
        
        return produtos
    
    def format_cnpj(self, cnpj: str) -> str:
        """Formatar CNPJ"""
        if not cnpj or len(cnpj) != 14:
            return cnpj
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
    
    def format_cpf(self, cpf: str) -> str:
        """Formatar CPF"""
        if not cpf or len(cpf) != 11:
            return cpf
        return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
    
    def format_document(self, dest_element, ns: dict) -> str:
        """Formatar CNPJ ou CPF do destinatário"""
        if dest_element is None:
            return ""
        
        cnpj = self.get_text(dest_element, 'nfe:CNPJ', ns)
        if cnpj:
            return self.format_cnpj(cnpj)
        
        cpf = self.get_text(dest_element, 'nfe:CPF', ns)
        if cpf:
            return self.format_cpf(cpf)
        
        return ""
    
    def format_cep(self, cep: str) -> str:
        """Formatar CEP"""
        if not cep or len(cep) != 8:
            return cep
        return f"{cep[:5]}-{cep[5:]}"
    
    def format_date(self, date_str: str) -> str:
        """Formatar data"""
        if not date_str:
            return ""
        try:
            # Formato: 2025-06-19T10:30:00-03:00
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%d/%m/%Y %H:%M:%S')
        except:
            return date_str
    
    def format_currency(self, value: str) -> str:
        """Formatar valor monetário"""
        if not value:
            return "0,00"
        try:
            val = float(value)
            return f"{val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except:
            return value

    def generate_danfe_pdf(self, xml_content: str, output_path: str) -> bool:
        """Gerar PDF DANFE com design visual atrativo"""
        try:
            # Extrair dados do XML
            data = self.extract_xml_data(xml_content)
            if not data:
                logger.error("Não foi possível extrair dados do XML")
                return False
            
            # Criar documento PDF
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )
            
            elements = []
            
            # Cabeçalho DANFE
            elements.append(Paragraph("DOCUMENTO AUXILIAR DA NOTA FISCAL ELETRÔNICA", self.styles['DANFETitle']))
            elements.append(Paragraph("DANFE", self.styles['DANFETitle']))
            elements.append(Spacer(1, 20))
            
            # Informações principais
            info_data = [
                ['Número:', data.get('numero', ''), 'Série:', data.get('serie', '')],
                ['Data de Emissão:', data.get('data_emissao', ''), '', ''],
                ['Chave de Acesso:', data.get('chave_acesso', ''), '', '']
            ]
            
            info_table = Table(info_data, colWidths=[3*cm, 4*cm, 3*cm, 4*cm])
            info_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightblue),
                ('BACKGROUND', (2, 0), (2, -1), colors.lightblue),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))
            elements.append(info_table)
            elements.append(Spacer(1, 20))
            
            # Emitente
            elements.append(Paragraph("EMITENTE", self.styles['DANFESubtitle']))
            emit_data = [
                ['Nome:', data.get('emit_nome', '')],
                ['CNPJ:', data.get('emit_cnpj', '')],
                ['Endereço:', data.get('emit_endereco', '')]
            ]
            
            emit_table = Table(emit_data, colWidths=[3*cm, 11*cm])
            emit_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightgreen),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))
            elements.append(emit_table)
            elements.append(Spacer(1, 15))
            
            # Destinatário
            elements.append(Paragraph("DESTINATÁRIO", self.styles['DANFESubtitle']))
            dest_data = [
                ['Nome:', data.get('dest_nome', '')],
                ['Documento:', data.get('dest_doc', '')],
                ['Endereço:', data.get('dest_endereco', '')]
            ]
            
            dest_table = Table(dest_data, colWidths=[3*cm, 11*cm])
            dest_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (0, -1), colors.lightyellow),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))
            elements.append(dest_table)
            elements.append(Spacer(1, 15))
            
            # Produtos
            if data.get('produtos'):
                elements.append(Paragraph("PRODUTOS/SERVIÇOS", self.styles['DANFESubtitle']))
                
                prod_headers = ['Código', 'Descrição', 'Qtd', 'Un', 'Vl Unit', 'Vl Total']
                prod_data = [prod_headers]
                
                for produto in data['produtos']:
                    prod_data.append([
                        produto.get('codigo', ''),
                        produto.get('descricao', '')[:30] + '...' if len(produto.get('descricao', '')) > 30 else produto.get('descricao', ''),
                        produto.get('quantidade', ''),
                        produto.get('unidade', ''),
                        produto.get('valor_unitario', ''),
                        produto.get('valor_total', '')
                    ])
                
                prod_table = Table(prod_data, colWidths=[2*cm, 6*cm, 1.5*cm, 1*cm, 2*cm, 2*cm])
                prod_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                    ('ALIGN', (2, 1), (-1, -1), 'RIGHT')
                ]))
                elements.append(prod_table)
                elements.append(Spacer(1, 15))
            
            # Totais
            elements.append(Paragraph("TOTAIS", self.styles['DANFESubtitle']))
            totais_data = [
                ['Valor dos Produtos:', f"R$ {data.get('valor_produtos', '0,00')}"],
                ['Valor do ICMS:', f"R$ {data.get('valor_icms', '0,00')}"],
                ['VALOR TOTAL DA NF-e:', f"R$ {data.get('valor_total', '0,00')}"]
            ]
            
            totais_table = Table(totais_data, colWidths=[6*cm, 4*cm])
            totais_table.setStyle(TableStyle([
                ('BACKGROUND', (0, -1), (-1, -1), colors.darkgreen),
                ('TEXTCOLOR', (0, -1), (-1, -1), colors.white),
                ('BACKGROUND', (0, 0), (0, -2), colors.lightgrey),
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))
            elements.append(totais_table)
            elements.append(Spacer(1, 20))
            
            # Rodapé
            elements.append(Paragraph(
                f"DANFE gerado em {datetime.now().strftime('%d/%m/%Y às %H:%M:%S')} | XMLDownloader", 
                self.styles['DANFENormal']
            ))
            
            # Construir PDF
            doc.build(elements)
            logger.info(f"DANFE gerado com sucesso: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao gerar DANFE: {e}")
            return False

def generate_danfe_from_file(xml_file_path: str, output_dir: str = "downloads") -> str:
    """Função principal para gerar DANFE a partir de um arquivo XML"""
    try:
        # Ler conteúdo do XML
        with open(xml_file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # Determinar caminho de saída
        base_name = os.path.splitext(os.path.basename(xml_file_path))[0]
        output_path = os.path.join(output_dir, f"DANFE_{base_name}.pdf")
        
        # Gerar DANFE
        generator = SimpleDanfeGenerator()
        success = generator.generate_danfe_pdf(xml_content, output_path)
        
        return output_path if success else None
        
    except Exception as e:
        logger.error(f"Erro ao gerar DANFE: {e}")
        return None