"""
Gerador de DANFE (Documento Auxiliar da Nota Fiscal Eletrônica)
Converte XMLs de notas fiscais em PDFs no formato DANFE padrão
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
import xml.etree.ElementTree as ET
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm, cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

logger = logging.getLogger(__name__)

class DANFEGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Configurar estilos customizados para o DANFE"""
        self.styles.add(ParagraphStyle(
            name='DANFETitle',
            parent=self.styles['Heading1'],
            fontSize=14,
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='DANFESubtitle',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=5,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='DANFEField',
            parent=self.styles['Normal'],
            fontSize=8,
            spaceAfter=2,
            alignment=TA_LEFT,
            fontName='Helvetica'
        ))
        
        self.styles.add(ParagraphStyle(
            name='DANFEValue',
            parent=self.styles['Normal'],
            fontSize=9,
            spaceAfter=2,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))
    
    def parse_xml(self, xml_content: str) -> Dict[str, Any]:
        """Extrair dados do XML da nota fiscal"""
        try:
            # Remove namespace declarations for easier parsing
            xml_content_clean = xml_content.replace(' xmlns="http://www.portalfiscal.inf.br/nfe"', '')
            xml_content_clean = xml_content_clean.replace('xmlns="http://www.portalfiscal.inf.br/nfe"', '')
            
            root = ET.fromstring(xml_content_clean)
            
            # Encontrar elementos principais
            nfe = root.find('.//NFe') or root.find('.//nfe')
            if nfe is None:
                nfe = root.find('.//infNFe') or root
            
            inf_nfe = nfe.find('.//infNFe') or nfe
            
            # Inicializar estrutura de dados
            data = {}
            
            # Dados básicos da NF-e
            data['numero'] = self.get_text(inf_nfe, './/nNF')
            data['serie'] = self.get_text(inf_nfe, './/serie')
            data['chave'] = self.get_text(inf_nfe, './/chNFe') or inf_nfe.get('Id', '').replace('NFe', '')
            data['data_emissao'] = self.format_date(self.get_text(inf_nfe, './/dhEmi'))
            data['natureza'] = self.get_text(inf_nfe, './/natOp')
            data['modelo'] = self.get_text(inf_nfe, './/mod')
            
            # Dados do emitente
            emit = inf_nfe.find('.//emit')
            emitente_data = {}
            if emit is not None:
                emitente_data['razao_social'] = self.get_text(emit, './/xNome')
                emitente_data['cnpj'] = self.format_cnpj(self.get_text(emit, './/CNPJ'))
                emitente_data['ie'] = self.get_text(emit, './/IE')
                emitente_data['endereco'] = self.get_endereco(emit.find('.//enderEmit'))
            data['emitente'] = emitente_data
            
            # Dados do destinatário
            dest = inf_nfe.find('.//dest')
            destinatario_data = {}
            if dest is not None:
                destinatario_data['razao_social'] = self.get_text(dest, './/xNome')
                destinatario_data['cnpj_cpf'] = self.format_cnpj_cpf(dest)
                destinatario_data['ie'] = self.get_text(dest, './/IE')
                destinatario_data['endereco'] = self.get_endereco(dest.find('.//enderDest'))
            data['destinatario'] = destinatario_data
            
            # Produtos/Serviços
            produtos_list = []
            produtos = inf_nfe.findall('.//det')
            for prod in produtos:
                produto_info = prod.find('.//prod')
                if produto_info is not None:
                    produto_data = {
                        'codigo': self.get_text(produto_info, './/cProd'),
                        'descricao': self.get_text(produto_info, './/xProd'),
                        'ncm': self.get_text(produto_info, './/NCM'),
                        'cfop': self.get_text(produto_info, './/CFOP'),
                        'unidade': self.get_text(produto_info, './/uCom'),
                        'quantidade': self.get_text(produto_info, './/qCom'),
                        'valor_unitario': self.format_currency(self.get_text(produto_info, './/vUnCom')),
                        'valor_total': self.format_currency(self.get_text(produto_info, './/vProd')),
                    }
                    produtos_list.append(produto_data)
            data['produtos'] = produtos_list
            
            # Totais
            total = inf_nfe.find('.//total')
            totais_data = {}
            if total is not None:
                icms_tot = total.find('.//ICMSTot')
                if icms_tot is not None:
                    totais_data['base_icms'] = self.format_currency(self.get_text(icms_tot, './/vBC'))
                    totais_data['valor_icms'] = self.format_currency(self.get_text(icms_tot, './/vICMS'))
                    totais_data['base_icms_st'] = self.format_currency(self.get_text(icms_tot, './/vBCST'))
                    totais_data['valor_icms_st'] = self.format_currency(self.get_text(icms_tot, './/vST'))
                    totais_data['valor_produtos'] = self.format_currency(self.get_text(icms_tot, './/vProd'))
                    totais_data['valor_frete'] = self.format_currency(self.get_text(icms_tot, './/vFrete'))
                    totais_data['valor_seguro'] = self.format_currency(self.get_text(icms_tot, './/vSeg'))
                    totais_data['valor_desconto'] = self.format_currency(self.get_text(icms_tot, './/vDesc'))
                    totais_data['valor_total'] = self.format_currency(self.get_text(icms_tot, './/vNF'))
            data['totais'] = totais_data
            
            return data
            
        except Exception as e:
            logger.error(f"Erro ao fazer parse do XML: {e}")
            raise Exception(f"Erro ao processar XML: {str(e)}")
    
    def get_text(self, element, xpath: str) -> str:
        """Obter texto de um elemento XML"""
        if element is None:
            return ""
        found = element.find(xpath)
        return found.text if found is not None and found.text else ""
    
    def get_endereco(self, endereco_elem) -> str:
        """Formatar endereço completo"""
        if endereco_elem is None:
            return ""
        
        logradouro = self.get_text(endereco_elem, './/xLgr')
        numero = self.get_text(endereco_elem, './/nro')
        bairro = self.get_text(endereco_elem, './/xBairro')
        municipio = self.get_text(endereco_elem, './/xMun')
        uf = self.get_text(endereco_elem, './/UF')
        cep = self.get_text(endereco_elem, './/CEP')
        
        endereco = f"{logradouro}"
        if numero:
            endereco += f", {numero}"
        if bairro:
            endereco += f" - {bairro}"
        if municipio:
            endereco += f" - {municipio}"
        if uf:
            endereco += f"/{uf}"
        if cep:
            endereco += f" - CEP: {self.format_cep(cep)}"
            
        return endereco
    
    def format_cnpj(self, cnpj: str) -> str:
        """Formatar CNPJ"""
        if not cnpj or len(cnpj) != 14:
            return cnpj
        return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
    
    def format_cnpj_cpf(self, dest_elem) -> str:
        """Formatar CNPJ ou CPF do destinatário"""
        if dest_elem is None:
            return ""
        
        cnpj = self.get_text(dest_elem, './/CNPJ')
        if cnpj:
            return self.format_cnpj(cnpj)
        
        cpf = self.get_text(dest_elem, './/CPF')
        if cpf and len(cpf) == 11:
            return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        
        return cpf
    
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
            # Parse ISO format
            if 'T' in date_str:
                dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                return dt.strftime('%d/%m/%Y')
            return date_str
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
    
    def generate_danfe(self, xml_content: str, output_path: str) -> bool:
        """Gerar PDF DANFE a partir do XML"""
        try:
            logger.info(f"Gerando DANFE: {output_path}")
            
            # Parse do XML
            data = self.parse_xml(xml_content)
            
            # Criar PDF
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=1*cm,
                leftMargin=1*cm,
                topMargin=1*cm,
                bottomMargin=1*cm
            )
            
            # Elementos do PDF
            elements = []
            
            # Cabeçalho DANFE
            elements.append(Paragraph("DANFE", self.styles['DANFETitle']))
            elements.append(Paragraph("Documento Auxiliar da Nota Fiscal Eletrônica", self.styles['DANFESubtitle']))
            elements.append(Spacer(1, 10))
            
            # Dados da NF-e
            nfe_data = [
                ['Número:', data.get('numero', ''), 'Série:', data.get('serie', '')],
                ['Data de Emissão:', data.get('data_emissao', ''), 'Modelo:', data.get('modelo', '')],
                ['Natureza da Operação:', data.get('natureza', ''), '', ''],
                ['Chave de Acesso:', data.get('chave', ''), '', '']
            ]
            
            nfe_table = Table(nfe_data, colWidths=[3*cm, 4*cm, 3*cm, 4*cm])
            nfe_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(nfe_table)
            elements.append(Spacer(1, 10))
            
            # Dados do emitente
            if 'emitente' in data:
                emit = data['emitente']
                elements.append(Paragraph("EMITENTE", self.styles['DANFESubtitle']))
                emit_data = [
                    ['Razão Social:', emit.get('razao_social', '')],
                    ['CNPJ:', emit.get('cnpj', '')],
                    ['Inscrição Estadual:', emit.get('ie', '')],
                    ['Endereço:', emit.get('endereco', '')]
                ]
                
                emit_table = Table(emit_data, colWidths=[4*cm, 12*cm])
                emit_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP')
                ]))
                elements.append(emit_table)
                elements.append(Spacer(1, 10))
            
            # Dados do destinatário
            if 'destinatario' in data:
                dest = data['destinatario']
                elements.append(Paragraph("DESTINATÁRIO", self.styles['DANFESubtitle']))
                dest_data = [
                    ['Razão Social:', dest.get('razao_social', '')],
                    ['CNPJ/CPF:', dest.get('cnpj_cpf', '')],
                    ['Inscrição Estadual:', dest.get('ie', '')],
                    ['Endereço:', dest.get('endereco', '')]
                ]
                
                dest_table = Table(dest_data, colWidths=[4*cm, 12*cm])
                dest_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP')
                ]))
                elements.append(dest_table)
                elements.append(Spacer(1, 10))
            
            # Produtos
            if 'produtos' in data and data['produtos']:
                elements.append(Paragraph("PRODUTOS/SERVIÇOS", self.styles['DANFESubtitle']))
                
                prod_headers = ['Código', 'Descrição', 'NCM', 'CFOP', 'Un', 'Qtd', 'Vl Unit', 'Vl Total']
                prod_data = [prod_headers]
                
                for prod in data['produtos']:
                    prod_data.append([
                        prod.get('codigo', ''),
                        prod.get('descricao', '')[:30] + '...' if len(prod.get('descricao', '')) > 30 else prod.get('descricao', ''),
                        prod.get('ncm', ''),
                        prod.get('cfop', ''),
                        prod.get('unidade', ''),
                        prod.get('quantidade', ''),
                        prod.get('valor_unitario', ''),
                        prod.get('valor_total', '')
                    ])
                
                prod_table = Table(prod_data, colWidths=[2*cm, 5*cm, 2*cm, 1.5*cm, 1*cm, 1.5*cm, 2*cm, 2*cm])
                prod_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 7),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('ALIGN', (4, 1), (-1, -1), 'RIGHT')
                ]))
                elements.append(prod_table)
                elements.append(Spacer(1, 10))
            
            # Totais
            if 'totais' in data:
                totais = data['totais']
                elements.append(Paragraph("TOTAIS", self.styles['DANFESubtitle']))
                
                totais_data = [
                    ['Base ICMS:', totais.get('base_icms', ''), 'Valor ICMS:', totais.get('valor_icms', '')],
                    ['Base ICMS ST:', totais.get('base_icms_st', ''), 'Valor ICMS ST:', totais.get('valor_icms_st', '')],
                    ['Valor Produtos:', totais.get('valor_produtos', ''), 'Valor Frete:', totais.get('valor_frete', '')],
                    ['Valor Seguro:', totais.get('valor_seguro', ''), 'Valor Desconto:', totais.get('valor_desconto', '')],
                    ['VALOR TOTAL DA NF-e:', totais.get('valor_total', ''), '', '']
                ]
                
                totais_table = Table(totais_data, colWidths=[4*cm, 3*cm, 4*cm, 3*cm])
                totais_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
                    ('BACKGROUND', (2, 0), (2, -1), colors.lightgrey),
                    ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
                    ('FONTNAME', (0, -1), (1, -1), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                    ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                    ('BACKGROUND', (0, -1), (1, -1), colors.yellow)
                ]))
                elements.append(totais_table)
            
            # Gerar PDF
            doc.build(elements)
            
            logger.info(f"DANFE gerado com sucesso: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao gerar DANFE: {e}")
            return False

def generate_danfe_from_xml(xml_file_path: str, output_dir: str = "downloads") -> Optional[str]:
    """Função utilitária para gerar DANFE a partir de um arquivo XML"""
    try:
        # Ler XML
        with open(xml_file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # Determinar nome do arquivo de saída
        base_name = os.path.splitext(os.path.basename(xml_file_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}.pdf")
        
        # Gerar DANFE
        generator = DANFEGenerator()
        success = generator.generate_danfe(xml_content, output_path)
        
        return output_path if success else None
        
    except Exception as e:
        logger.error(f"Erro ao gerar DANFE a partir do arquivo {xml_file_path}: {e}")
        return None