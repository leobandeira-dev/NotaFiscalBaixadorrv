import xml.etree.ElementTree as ET
import re
from datetime import datetime
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

def extract_xml_data(xml_content: str) -> Dict[str, Any]:
    """
    Extrai dados importantes do XML da NFe para armazenamento no banco
    """
    try:
        # Remove namespace declarations for easier parsing
        xml_clean = re.sub(r'\s*xmlns[^=]*="[^"]*"', '', xml_content)
        
        root = ET.fromstring(xml_clean)
        
        # Find the infNFe element
        inf_nfe = root.find('.//infNFe') or root.find('.//NFe/infNFe')
        if not inf_nfe:
            raise ValueError("Elemento infNFe não encontrado no XML")
        
        # Dados do emitente
        emit = inf_nfe.find('emit')
        cnpj_emitente = emit.find('CNPJ').text if emit is not None and emit.find('CNPJ') is not None else None
        nome_emitente = emit.find('xNome').text if emit is not None and emit.find('xNome') is not None else None
        
        # Dados da nota fiscal
        ide = inf_nfe.find('ide')
        numero_nf = ide.find('nNF').text if ide is not None and ide.find('nNF') is not None else None
        serie_nf = ide.find('serie').text if ide is not None and ide.find('serie') is not None else None
        
        # Data de emissão
        data_emissao = None
        if ide is not None and ide.find('dhEmi') is not None:
            data_str = ide.find('dhEmi').text
            try:
                # Parse ISO datetime
                data_emissao = datetime.fromisoformat(data_str.replace('Z', '+00:00')).date()
            except:
                try:
                    # Try alternative format
                    data_emissao = datetime.strptime(data_str[:10], '%Y-%m-%d').date()
                except:
                    logger.warning(f"Não foi possível parsear data de emissão: {data_str}")
        
        # Valor total
        valor_total = None
        total = inf_nfe.find('.//total/ICMSTot')
        if total is not None and total.find('vNF') is not None:
            try:
                valor_total = float(total.find('vNF').text)
            except:
                logger.warning("Não foi possível parsear valor total")
        
        return {
            'cnpj_emitente': cnpj_emitente,
            'nome_emitente': nome_emitente,
            'numero_nf': numero_nf,
            'serie_nf': serie_nf,
            'data_emissao': data_emissao,
            'valor_total': valor_total
        }
        
    except Exception as e:
        logger.error(f"Erro ao extrair dados do XML: {str(e)}")
        return {
            'cnpj_emitente': None,
            'nome_emitente': None,
            'numero_nf': None,
            'serie_nf': None,
            'data_emissao': None,
            'valor_total': None
        }

def save_xml_to_database(user_id: int, invoice_key: str, xml_content: str, 
                        file_path: str, import_type: str, job_id: str = None) -> Optional[int]:
    """
    Salva XML no banco de dados e registra cobrança
    """
    try:
        from models import db, ImportedXML, User, UsageRecord, ServiceModule
        
        # Verificar se já existe
        existing = ImportedXML.query.filter_by(
            user_id=user_id, 
            invoice_key=invoice_key
        ).first()
        
        if existing:
            logger.info(f"XML {invoice_key} já existe no banco para usuário {user_id}")
            return existing.id
        
        # Extrair dados do XML
        xml_data = extract_xml_data(xml_content)
        
        # Criar registro do XML importado
        imported_xml = ImportedXML(
            user_id=user_id,
            invoice_key=invoice_key,
            xml_content=xml_content,
            file_path=file_path,
            import_type=import_type,
            job_id=job_id,
            cnpj_emitente=xml_data['cnpj_emitente'],
            nome_emitente=xml_data['nome_emitente'],
            numero_nf=xml_data['numero_nf'],
            serie_nf=xml_data['serie_nf'],
            data_emissao=xml_data['data_emissao'],
            valor_total=xml_data['valor_total']
        )
        
        db.session.add(imported_xml)
        db.session.flush()  # Get the ID
        
        # Registrar uso do serviço de download XML
        xml_module = ServiceModule.query.filter_by(name='Download XML').first()
        if xml_module:
            user = User.query.get(user_id)
            
            # Verificar se usuário pode usar o serviço
            if user and user.can_use_service(xml_module.cost_per_use):
                # Deduzir do saldo
                user.deduct_balance(xml_module.cost_per_use, f'Download XML: {invoice_key}')
                
                # Registrar uso
                usage_record = UsageRecord(
                    user_id=user_id,
                    module_id=xml_module.id,
                    quantity=1,
                    cost=xml_module.cost_per_use,
                    description=f'Download XML: {invoice_key}',
                    invoice_keys=invoice_key,
                    job_id=job_id
                )
                
                db.session.add(usage_record)
                logger.info(f"Registrado uso de R${xml_module.cost_per_use:.2f} para usuário {user_id}")
            else:
                logger.warning(f"Usuário {user_id} sem saldo suficiente para download XML")
        
        db.session.commit()
        logger.info(f"XML {invoice_key} salvo no banco com ID {imported_xml.id}")
        return imported_xml.id
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao salvar XML no banco: {str(e)}")
        return None

def get_user_xmls(user_id: int, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
    """
    Recupera XMLs do usuário com paginação
    """
    try:
        from models import ImportedXML
        
        query = ImportedXML.query.filter_by(user_id=user_id)
        total = query.count()
        
        xmls = query.order_by(ImportedXML.imported_at.desc()).offset(offset).limit(limit).all()
        
        return {
            'xmls': [xml.to_dict() for xml in xmls],
            'total': total,
            'limit': limit,
            'offset': offset
        }
        
    except Exception as e:
        logger.error(f"Erro ao recuperar XMLs do usuário: {str(e)}")
        return {'xmls': [], 'total': 0, 'limit': limit, 'offset': offset}

def generate_danfe_for_xml(xml_id: int) -> Dict[str, Any]:
    """
    Gera DANFE PDF para um XML específico
    """
    try:
        from models import db, ImportedXML
        from danfe_generator import DANFEGenerator
        import os
        
        xml_record = ImportedXML.query.get(xml_id)
        if not xml_record:
            return {'success': False, 'error': 'XML não encontrado'}
        
        # Gerar DANFE
        generator = DANFEGenerator()
        
        # Criar diretório de saída
        output_dir = f'downloads/user_{xml_record.user_id}'
        os.makedirs(output_dir, exist_ok=True)
        
        pdf_filename = f"{xml_record.invoice_key}_danfe.pdf"
        pdf_path = os.path.join(output_dir, pdf_filename)
        
        success = generator.generate_danfe(xml_record.xml_content, pdf_path)
        
        if success:
            # Marcar como DANFE gerado
            xml_record.danfe_generated = True
            db.session.commit()
            
            return {
                'success': True,
                'pdf_path': pdf_path,
                'filename': pdf_filename
            }
        else:
            return {'success': False, 'error': 'Erro na geração do DANFE'}
            
    except Exception as e:
        logger.error(f"Erro ao gerar DANFE: {str(e)}")
        return {'success': False, 'error': str(e)}