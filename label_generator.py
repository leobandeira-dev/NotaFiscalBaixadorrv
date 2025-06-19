"""
Gerador de Etiquetas de Transporte para NFe
Módulo para geração de etiquetas personalizadas a partir dos XMLs
"""

import xml.etree.ElementTree as ET
import re
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.graphics.barcode import code128
import os

logger = logging.getLogger(__name__)

class LabelGenerator:
    def __init__(self):
        self.page_width = A4[0]
        self.page_height = A4[1]
        self.margin = 1 * cm
        
    def extract_shipping_data(self, xml_content: str) -> Dict[str, Any]:
        """
        Extrai dados de transporte do XML da NFe
        """
        try:
            # Remove namespace declarations
            xml_clean = re.sub(r'\s*xmlns[^=]*="[^"]*"', '', xml_content)
            root = ET.fromstring(xml_clean)
            
            # Find the infNFe element
            inf_nfe = root.find('.//infNFe') or root.find('.//NFe/infNFe')
            if not inf_nfe:
                raise ValueError("Elemento infNFe não encontrado no XML")
            
            # Dados do remetente (emitente)
            emit = inf_nfe.find('emit')
            remetente = {
                'nome': emit.find('xNome').text if emit.find('xNome') is not None else '',
                'cnpj': self.format_cnpj(emit.find('CNPJ').text if emit.find('CNPJ') is not None else ''),
                'endereco': self.extract_address(emit.find('enderEmit'))
            }
            
            # Dados do destinatário
            dest = inf_nfe.find('dest')
            destinatario = {
                'nome': dest.find('xNome').text if dest.find('xNome') is not None else '',
                'cnpj_cpf': self.format_document(dest),
                'endereco': self.extract_address(dest.find('enderDest'))
            }
            
            # Dados da nota fiscal
            ide = inf_nfe.find('ide')
            nfe_data = {
                'numero': ide.find('nNF').text if ide.find('nNF') is not None else '',
                'serie': ide.find('serie').text if ide.find('serie') is not None else '',
                'chave': inf_nfe.get('Id', '').replace('NFe', '') if inf_nfe.get('Id') else '',
                'data_emissao': self.format_date(ide.find('dhEmi').text if ide.find('dhEmi') is not None else '')
            }
            
            # Dados dos produtos para peso e volume
            produtos = []
            det_list = inf_nfe.findall('det')
            total_peso = 0
            total_volume = 0
            
            for det in det_list:
                prod = det.find('prod')
                if prod is not None:
                    produtos.append({
                        'codigo': prod.find('cProd').text if prod.find('cProd') is not None else '',
                        'descricao': prod.find('xProd').text if prod.find('xProd') is not None else '',
                        'quantidade': float(prod.find('qCom').text) if prod.find('qCom') is not None else 0,
                        'peso_liquido': float(prod.find('qCom').text) if prod.find('qCom') is not None else 0
                    })
                    
                    # Somar peso (aproximado pela quantidade)
                    total_peso += float(prod.find('qCom').text) if prod.find('qCom') is not None else 0
            
            # Dados da transportadora
            transp = inf_nfe.find('transp')
            transportadora = {}
            if transp is not None:
                transp_a = transp.find('transporta')
                if transp_a is not None:
                    transportadora = {
                        'nome': transp_a.find('xNome').text if transp_a.find('xNome') is not None else '',
                        'cnpj': self.format_cnpj(transp_a.find('CNPJ').text if transp_a.find('CNPJ') is not None else ''),
                        'endereco': transp_a.find('xEnder').text if transp_a.find('xEnder') is not None else ''
                    }
                
                # Dados do veículo
                veiculo = transp.find('veicTransp')
                if veiculo is not None:
                    transportadora['placa'] = veiculo.find('placa').text if veiculo.find('placa') is not None else ''
                
                # Volumes
                vol = transp.find('vol')
                if vol is not None:
                    total_volume = int(vol.find('qVol').text) if vol.find('qVol') is not None else 1
                    total_peso = float(vol.find('pesoB').text) if vol.find('pesoB') is not None else total_peso
            
            return {
                'remetente': remetente,
                'destinatario': destinatario,
                'nfe': nfe_data,
                'produtos': produtos,
                'transportadora': transportadora,
                'peso_total': total_peso,
                'volume_total': total_volume or 1
            }
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados de transporte: {str(e)}")
            raise
    
    def format_cnpj(self, cnpj: str) -> str:
        """Formatar CNPJ"""
        if not cnpj:
            return ''
        cnpj = re.sub(r'[^\d]', '', cnpj)
        if len(cnpj) == 14:
            return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
        return cnpj
    
    def format_cpf(self, cpf: str) -> str:
        """Formatar CPF"""
        if not cpf:
            return ''
        cpf = re.sub(r'[^\d]', '', cpf)
        if len(cpf) == 11:
            return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        return cpf
    
    def format_document(self, dest_elem) -> str:
        """Formatar CNPJ ou CPF do destinatário"""
        if dest_elem is None:
            return ''
        
        cnpj = dest_elem.find('CNPJ')
        if cnpj is not None:
            return self.format_cnpj(cnpj.text)
        
        cpf = dest_elem.find('CPF')
        if cpf is not None:
            return self.format_cpf(cpf.text)
        
        return ''
    
    def extract_address(self, endereco_elem) -> str:
        """Extrair endereço completo"""
        if endereco_elem is None:
            return ''
        
        parts = []
        
        logradouro = endereco_elem.find('xLgr')
        if logradouro is not None and logradouro.text:
            parts.append(logradouro.text)
        
        numero = endereco_elem.find('nro')
        if numero is not None and numero.text:
            parts.append(f"nº {numero.text}")
        
        complemento = endereco_elem.find('xCpl')
        if complemento is not None and complemento.text:
            parts.append(complemento.text)
        
        bairro = endereco_elem.find('xBairro')
        if bairro is not None and bairro.text:
            parts.append(bairro.text)
        
        cidade = endereco_elem.find('xMun')
        uf = endereco_elem.find('UF')
        if cidade is not None and uf is not None:
            parts.append(f"{cidade.text}/{uf.text}")
        
        cep = endereco_elem.find('CEP')
        if cep is not None and cep.text:
            cep_formatted = f"{cep.text[:5]}-{cep.text[5:]}" if len(cep.text) == 8 else cep.text
            parts.append(f"CEP: {cep_formatted}")
        
        return ', '.join(parts)
    
    def format_date(self, date_str: str) -> str:
        """Formatar data"""
        if not date_str:
            return ''
        try:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
            return dt.strftime('%d/%m/%Y')
        except:
            return date_str[:10] if len(date_str) >= 10 else date_str
    
    def generate_shipping_label(self, shipping_data: Dict[str, Any], output_path: str) -> bool:
        """
        Gera etiqueta de transporte em PDF
        """
        try:
            # Criar documento PDF
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=self.margin,
                leftMargin=self.margin,
                topMargin=self.margin,
                bottomMargin=self.margin
            )
            
            # Estilos
            styles = getSampleStyleSheet()
            title_style = styles['Title']
            title_style.alignment = TA_CENTER
            
            normal_style = styles['Normal']
            normal_style.fontSize = 9
            
            bold_style = styles['Normal'].clone('BoldStyle')
            bold_style.fontName = 'Helvetica-Bold'
            bold_style.fontSize = 10
            
            # Elementos do documento
            elements = []
            
            # Título
            elements.append(Paragraph("ETIQUETA DE TRANSPORTE", title_style))
            elements.append(Spacer(1, 0.5*cm))
            
            # Dados da NFe
            nfe_data = [
                ['NOTA FISCAL ELETRÔNICA', ''],
                [f"Número: {shipping_data['nfe']['numero']}", f"Série: {shipping_data['nfe']['serie']}"],
                [f"Data: {shipping_data['nfe']['data_emissao']}", f"Chave: {shipping_data['nfe']['chave'][:22]}..."]
            ]
            
            nfe_table = Table(nfe_data, colWidths=[8*cm, 8*cm])
            nfe_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('SPAN', (0, 0), (1, 0)),
            ]))
            
            elements.append(nfe_table)
            elements.append(Spacer(1, 0.5*cm))
            
            # Remetente
            elements.append(Paragraph("REMETENTE", bold_style))
            remetente_data = [
                [f"Nome: {shipping_data['remetente']['nome']}"],
                [f"CNPJ: {shipping_data['remetente']['cnpj']}"],
                [f"Endereço: {shipping_data['remetente']['endereco']}"]
            ]
            
            remetente_table = Table(remetente_data, colWidths=[16*cm])
            remetente_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(remetente_table)
            elements.append(Spacer(1, 0.3*cm))
            
            # Destinatário
            elements.append(Paragraph("DESTINATÁRIO", bold_style))
            destinatario_data = [
                [f"Nome: {shipping_data['destinatario']['nome']}"],
                [f"CNPJ/CPF: {shipping_data['destinatario']['cnpj_cpf']}"],
                [f"Endereço: {shipping_data['destinatario']['endereco']}"]
            ]
            
            destinatario_table = Table(destinatario_data, colWidths=[16*cm])
            destinatario_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(destinatario_table)
            elements.append(Spacer(1, 0.3*cm))
            
            # Dados do transporte
            if shipping_data.get('transportadora'):
                elements.append(Paragraph("TRANSPORTADORA", bold_style))
                transp_data = [
                    [f"Nome: {shipping_data['transportadora'].get('nome', 'N/A')}"],
                    [f"CNPJ: {shipping_data['transportadora'].get('cnpj', 'N/A')}"],
                    [f"Placa: {shipping_data['transportadora'].get('placa', 'N/A')}"]
                ]
                
                transp_table = Table(transp_data, colWidths=[16*cm])
                transp_table.setStyle(TableStyle([
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTSIZE', (0, 0), (-1, -1), 9),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ]))
                
                elements.append(transp_table)
                elements.append(Spacer(1, 0.3*cm))
            
            # Dados de peso e volume
            peso_volume_data = [
                ['PESO TOTAL', 'VOLUMES'],
                [f"{shipping_data['peso_total']:.2f} kg", f"{shipping_data['volume_total']} unidades"]
            ]
            
            peso_table = Table(peso_volume_data, colWidths=[8*cm, 8*cm])
            peso_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ]))
            
            elements.append(peso_table)
            elements.append(Spacer(1, 0.5*cm))
            
            # Código de barras da chave da NFe
            if shipping_data['nfe']['chave']:
                elements.append(Paragraph("CHAVE DE ACESSO", bold_style))
                elements.append(Paragraph(shipping_data['nfe']['chave'], normal_style))
            
            # Gerar PDF
            doc.build(elements)
            
            logger.info(f"Etiqueta de transporte gerada: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Erro ao gerar etiqueta: {str(e)}")
            return False

def generate_label_for_xml(xml_id: int) -> Dict[str, Any]:
    """
    Gera etiqueta de transporte para um XML específico
    """
    try:
        from models import db, ImportedXML
        
        xml_record = ImportedXML.query.get(xml_id)
        if not xml_record:
            return {'success': False, 'error': 'XML não encontrado'}
        
        # Gerar etiqueta
        generator = LabelGenerator()
        
        # Extrair dados de transporte
        shipping_data = generator.extract_shipping_data(xml_record.xml_content)
        
        # Criar diretório de saída
        output_dir = f'downloads/user_{xml_record.user_id}'
        os.makedirs(output_dir, exist_ok=True)
        
        label_filename = f"{xml_record.invoice_key}_etiqueta.pdf"
        label_path = os.path.join(output_dir, label_filename)
        
        success = generator.generate_shipping_label(shipping_data, label_path)
        
        if success:
            # Marcar como etiqueta gerada
            xml_record.label_generated = True
            db.session.commit()
            
            return {
                'success': True,
                'label_path': label_path,
                'filename': label_filename
            }
        else:
            return {'success': False, 'error': 'Erro na geração da etiqueta'}
            
    except Exception as e:
        logger.error(f"Erro ao gerar etiqueta: {str(e)}")
        return {'success': False, 'error': str(e)}

def bulk_generate_labels(xml_ids: List[int]) -> Dict[str, Any]:
    """
    Gera etiquetas em lote para múltiplos XMLs
    """
    try:
        results = []
        errors = []
        
        for xml_id in xml_ids:
            result = generate_label_for_xml(xml_id)
            if result['success']:
                results.append({
                    'xml_id': xml_id,
                    'filename': result['filename']
                })
            else:
                errors.append({
                    'xml_id': xml_id,
                    'error': result['error']
                })
        
        return {
            'success': True,
            'generated': len(results),
            'errors': len(errors),
            'results': results,
            'error_details': errors
        }
        
    except Exception as e:
        logger.error(f"Erro na geração em lote: {str(e)}")
        return {'success': False, 'error': str(e)}