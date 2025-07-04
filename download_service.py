"""
Serviço de download com cobrança automática
Sistema completo para download de XMLs com cobrança e histórico
"""
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional

from models import db, User, XMLFile, UsageRecord, ServiceModule
from stripe_integration import CreditManager, PricingManager

logger = logging.getLogger(__name__)

class DownloadService:
    """Serviço para downloads com cobrança automática"""
    
    @staticmethod
    def create_download_job(user_id: int, invoice_keys: list) -> str:
        """Cria um job de download e verifica saldo do usuário"""
        try:
            user = User.query.get(user_id)
            if not user:
                raise ValueError("Usuário não encontrado")
            
            # Verificar se usuário está em período de teste (trial de 7 dias)
            from datetime import datetime
            is_trial_active = user.trial_expires_at and user.trial_expires_at > datetime.utcnow()
            
            # Se não está em trial, verificar créditos XML
            if not is_trial_active:
                from simple_credit_system import get_user_xml_balance
                available_credits = get_user_xml_balance(user_id)
                
                if available_credits < len(invoice_keys):
                    raise ValueError(f"Créditos XML insuficientes. Necessário: {len(invoice_keys)}, Disponível: {available_credits}")
            else:
                logger.info(f"Usuário {user_id} está em período de trial - acesso gratuito aos XMLs")
            
            job_id = str(uuid.uuid4())
            logger.info(f"Job {job_id} criado para usuário {user_id} com {len(invoice_keys)} XMLs")
            
            return job_id
            
        except Exception as e:
            logger.error(f"Erro ao criar job de download: {e}")
            raise
    
    @staticmethod
    def process_successful_download(user_id: int, invoice_key: str, xml_content: str, 
                                  file_path: str, job_id: str) -> bool:
        """Processa download bem-sucedido com cobrança e salvamento no banco"""
        from new_app import app
        with app.app_context():
            try:
                # Permitir downloads múltiplos - cada download gera registro único
                logger.info(f"Processando novo download de XML {invoice_key} para usuário {user_id}")
                
                # Sistema baseado em créditos XML
                
                # Verificar e deduzir créditos
                user = User.query.get(user_id)
                if not user:
                    logger.error(f"Usuário {user_id} não encontrado")
                    return False
                
                # Verificar se usuário está em período de teste
                from datetime import datetime
                is_trial_active = user.trial_expires_at and user.trial_expires_at > datetime.utcnow()
                
                # Verificar e consumir crédito XML
                if not is_trial_active:
                    from simple_credit_system import get_user_xml_balance, consume_xml_credit
                    available_credits = get_user_xml_balance(user_id)
                    if available_credits < 1:
                        logger.error(f"Créditos XML insuficientes para usuário {user_id}")
                        return False
                    
                    # Consumir 1 crédito XML
                    if not consume_xml_credit(user_id):
                        logger.error(f"Falha ao consumir crédito XML para usuário {user_id}")
                        return False
                
                # Extrair dados do XML antes de salvar
                from xml_processor import extract_xml_data
                xml_data = extract_xml_data(xml_content)
                
                # Salvar XML no banco com dados extraídos
                xml_file = XMLFile()
                xml_file.user_id = user_id
                xml_file.filename = f"{invoice_key}.xml"
                xml_file.invoice_key = invoice_key
                xml_file.file_path = file_path
                xml_file.xml_content = xml_content
                xml_file.import_type = 'SISTEMA'
                xml_file.job_id = job_id
                xml_file.imported_at = datetime.utcnow()
                
                # Dados extraídos do XML com limitação de caracteres
                xml_file.numero_nf = (xml_data.get('numero_nf', 'N/A') or 'N/A')[:50]
                xml_file.serie_nf = (xml_data.get('serie_nf', 'N/A') or 'N/A')[:10]
                xml_file.data_emissao = xml_data.get('data_emissao')
                xml_file.valor_total = xml_data.get('valor_total', 0.0)
                xml_file.peso_bruto = xml_data.get('peso_bruto', 0.0)
                xml_file.quantidade_volumes = xml_data.get('quantidade_volumes', 0)
                xml_file.cnpj_emitente = (xml_data.get('cnpj_emitente', 'N/A') or 'N/A')[:14]
                xml_file.nome_emitente = (xml_data.get('nome_emitente', 'N/A') or 'N/A')[:255]
                xml_file.remetente_razao = (xml_data.get('remetente_razao', xml_data.get('nome_emitente', '')) or '')[:255]
                xml_file.remetente_cidade = (xml_data.get('remetente_cidade', xml_data.get('cidade_emitente', '')) or '')[:100]
                xml_file.remetente_uf = (xml_data.get('remetente_uf', xml_data.get('uf_emitente', '')) or '')[:2]
                xml_file.remetente_endereco = (xml_data.get('remetente_endereco', xml_data.get('endereco_emitente', '')) or '')[:500]
                xml_file.remetente_cep = (xml_data.get('remetente_cep', xml_data.get('cep_emitente', '')) or '')[:8]
                xml_file.destinatario_cnpj_cpf = (xml_data.get('destinatario_cnpj_cpf', xml_data.get('cnpj_destinatario', '')) or '')[:14]
                xml_file.destinatario_razao = (xml_data.get('destinatario_razao', xml_data.get('nome_destinatario', '')) or '')[:255]
                xml_file.destinatario_cidade = (xml_data.get('destinatario_cidade', xml_data.get('cidade_destinatario', '')) or '')[:100]
                xml_file.destinatario_uf = (xml_data.get('destinatario_uf', xml_data.get('uf_destinatario', '')) or '')[:2]
                xml_file.destinatario_endereco = (xml_data.get('destinatario_endereco', xml_data.get('endereco_destinatario', '')) or '')[:500]
                xml_file.destinatario_cep = (xml_data.get('destinatario_cep', xml_data.get('cep_destinatario', '')) or '')[:8]
                
                db.session.add(xml_file)
                
                # Buscar módulo de serviço XML
                xml_module = ServiceModule.query.filter_by(name='xml_download').first()
                if not xml_module:
                    logger.error("Módulo xml_download não encontrado")
                    return False
                
                # Criar registro de uso
                usage_record = UsageRecord()
                usage_record.user_id = user_id
                usage_record.module_id = xml_module.id
                usage_record.quantity = 1
                usage_record.cost = 0.0  # Cost tracking moved to credit system
                usage_record.description = f"Download XML: {invoice_key[:10]}..."
                usage_record.job_id = job_id
                
                db.session.add(usage_record)
                
                # Log crédito debitado
                if not is_trial_active:
                    logger.info(f"1 crédito XML debitado do usuário {user_id}")
                else:
                    logger.info(f"Download gratuito para usuário {user_id} (período de teste)")
                
                user.updated_at = datetime.utcnow()
                
                # Commit todas as mudanças
                db.session.commit()
                
                logger.info(f"Download processado com sucesso: usuário {user_id}, XML {invoice_key}, XML salvo no banco")
                return True
                
            except Exception as e:
                logger.error(f"Erro ao processar download: {e}")
                db.session.rollback()
                return False
    
    @staticmethod
    def get_user_xmls(user_id: int, limit: int = 50) -> list:
        """Busca XMLs do usuário"""
        try:
            xmls = XMLFile.query.filter_by(user_id=user_id)\
                               .order_by(XMLFile.imported_at.desc())\
                               .limit(limit)\
                               .all()
            
            return [{
                'id': xml.id,
                'filename': xml.filename,
                'invoice_key': xml.invoice_key,
                'imported_at': xml.imported_at.strftime('%d/%m/%Y %H:%M'),
                'import_type': xml.import_type
            } for xml in xmls]
            
        except Exception as e:
            logger.error(f"Erro ao buscar XMLs do usuário {user_id}: {e}")
            return []
    
    @staticmethod
    def get_recent_activity(user_id: int, days: int = 7) -> list:
        """Busca atividades recentes do usuário"""
        try:
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Buscar registros de uso recentes
            usage_records = UsageRecord.query.filter(
                UsageRecord.user_id == user_id,
                UsageRecord.created_at >= cutoff_date
            ).order_by(UsageRecord.created_at.desc()).limit(20).all()
            
            activities = []
            for record in usage_records:
                activities.append({
                    'type': 'download',
                    'description': record.description,
                    'amount': record.cost,
                    'date': record.created_at.strftime('%d/%m/%Y %H:%M'),
                    'service': 'xml_download'
                })
            
            return activities
            
        except Exception as e:
            logger.error(f"Erro ao buscar atividades do usuário {user_id}: {e}")
            return []