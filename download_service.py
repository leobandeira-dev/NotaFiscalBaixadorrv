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
            
            # Verificar saldo para todos os downloads
            xml_price = PricingManager.get_service_price('xml_download')
            total_cost = len(invoice_keys) * xml_price
            
            if user.current_balance < total_cost:
                raise ValueError(f"Saldo insuficiente. Necessário: R$ {total_cost:.2f}, Disponível: R$ {user.current_balance:.2f}")
            
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
        try:
            # Verificar se XML já existe para este usuário
            existing_xml = XMLFile.query.filter_by(
                user_id=user_id,
                invoice_key=invoice_key
            ).first()
            
            if existing_xml:
                logger.info(f"XML {invoice_key} já existe para usuário {user_id}")
                return True
            
            # Obter preço do serviço
            xml_price = PricingManager.get_service_price('xml_download')
            
            # Verificar e deduzir créditos
            user = User.query.get(user_id)
            if not user:
                logger.error(f"Usuário {user_id} não encontrado")
                return False
            
            # Verificar se usuário está em período de teste
            from datetime import datetime
            is_trial_active = user.trial_expires_at and user.trial_expires_at > datetime.utcnow()
            
            if not is_trial_active and user.current_balance < xml_price:
                logger.error(f"Saldo insuficiente para usuário {user_id}")
                return False
            
            # Salvar XML no banco
            xml_file = XMLFile(
                user_id=user_id,
                filename=f"{invoice_key}.xml",
                invoice_key=invoice_key,
                file_path=file_path,
                xml_content=xml_content,
                import_type='SISTEMA',
                job_id=job_id,
                imported_at=datetime.utcnow()
            )
            
            db.session.add(xml_file)
            
            # Buscar módulo de serviço XML
            xml_module = ServiceModule.query.filter_by(name='xml_download').first()
            if not xml_module:
                logger.error("Módulo xml_download não encontrado")
                return False
            
            # Criar registro de uso
            usage_record = UsageRecord(
                user_id=user_id,
                module_id=xml_module.id,
                quantity=1,
                cost=xml_price,
                description=f"Download XML: {invoice_key[:10]}...",
                job_id=job_id
            )
            
            db.session.add(usage_record)
            
            # Atualizar saldo do usuário apenas se não estiver em período de teste
            if not is_trial_active:
                user.current_balance -= xml_price
                logger.info(f"Cobrado R$ {xml_price:.2f} do usuário {user_id}")
            else:
                logger.info(f"Download gratuito para usuário {user_id} (período de teste)")
            
            user.updated_at = datetime.utcnow()
            
            # Commit todas as mudanças
            db.session.commit()
            
            logger.info(f"Download processado com sucesso: usuário {user_id}, XML {invoice_key}, cobrado R$ {xml_price:.2f}")
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