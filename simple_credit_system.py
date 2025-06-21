"""
Sistema de Créditos XML Simplificado
Funções para calcular e exibir saldos de créditos XML corretamente
"""
from models import db, CreditBalance
from sqlalchemy import func
from flask_login import current_user
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_user_xml_balance(user_id):
    """
    Obter saldo atual de créditos XML do usuário (considera trial period)
    """
    try:
        from models import User
        user = User.query.get(user_id)
        if not user:
            return 0
            
        # Se usuário está em trial, retorna saldo "infinito" (999999) para bypass das verificações
        is_trial_active = user.trial_expires_at and user.trial_expires_at > datetime.utcnow()
        if is_trial_active:
            logger.info(f"Usuário {user_id} em trial - saldo ilimitado")
            return 999999  # Saldo "infinito" durante trial
        
        # Buscar último saldo na tabela credit_balances
        last_balance = db.session.query(CreditBalance)\
            .filter(CreditBalance.user_id == user_id)\
            .order_by(CreditBalance.created_at.desc())\
            .first()
        
        if last_balance:
            return max(0, int(last_balance.balance_after))
        else:
            return 0
            
    except Exception as e:
        logger.error(f"Erro ao calcular saldo XML do usuário {user_id}: {e}")
        return 0

def get_credit_history(user_id, limit=20):
    """
    Obter histórico de créditos do usuário
    """
    try:
        history = db.session.query(CreditBalance)\
            .filter(CreditBalance.user_id == user_id)\
            .order_by(CreditBalance.created_at.desc())\
            .limit(limit)\
            .all()
        
        return [transaction.to_dict() for transaction in history]
    except Exception as e:
        logger.error(f"Erro ao obter histórico de créditos: {e}")
        return []

def get_user_stats(user_id):
    """
    Estatísticas básicas do usuário
    """
    try:
        # Saldo atual
        saldo_atual = get_user_xml_balance(user_id)
        
        # Histórico de transações
        credit_history = get_credit_history(user_id, limit=10)
        
        # Calcular total de downloads realizados (débitos)
        total_downloads = sum(1 for tx in credit_history if tx['transaction_type'] == 'debit')
        
        return {
            'saldo_atual': saldo_atual,
            'total_downloads': total_downloads,
            'ultimas_transacoes': credit_history[:5]
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do usuário {user_id}: {e}")
        return {
            'saldo_atual': 0,
            'total_downloads': 0,
            'ultimas_transacoes': []
        }

def add_xml_credits(user_id, credits, description="Créditos adicionados"):
    """
    Adicionar créditos XML ao usuário
    """
    try:
        current_balance = get_user_xml_balance(user_id)
        new_balance = current_balance + credits
        
        # Criar registro de crédito
        credit_record = CreditBalance(
            user_id=user_id,
            transaction_type='credit',
            amount=credits,
            balance_after=new_balance,
            description=description,
            service_type='xml_credits',
            created_at=datetime.utcnow()
        )
        
        db.session.add(credit_record)
        db.session.commit()
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao adicionar créditos XML: {e}")
        db.session.rollback()
        return False

def consume_xml_credit(user_id, description="Download XML"):
    """
    Consumir um crédito XML do usuário (verifica período de trial)
    """
    try:
        from models import User
        user = User.query.get(user_id)
        if not user:
            logger.error(f"Usuário {user_id} não encontrado")
            return False
        
        # Verificar se usuário está em período de teste (trial de 7 dias)
        is_trial_active = user.trial_expires_at and user.trial_expires_at > datetime.utcnow()
        
        if is_trial_active:
            # Durante trial, não consome créditos mas registra uso para estatísticas
            logger.info(f"Usuário {user_id} em trial - download gratuito registrado")
            
            # Registrar uso durante trial (sem consumir créditos)
            trial_record = CreditBalance(
                user_id=user_id,
                transaction_type='trial_usage',
                amount=0,  # Sem cobrança durante trial
                balance_after=get_user_xml_balance(user_id),  # Saldo não muda
                description=f"{description} (Trial gratuito)",
                service_type='xml_download_trial',
                created_at=datetime.utcnow()
            )
            
            db.session.add(trial_record)
            db.session.commit()
            return True
        
        # Fora do trial - verificar e consumir créditos
        current_balance = get_user_xml_balance(user_id)
        
        if current_balance <= 0:
            logger.warning(f"Usuário {user_id} sem créditos XML suficientes")
            return False
        
        new_balance = current_balance - 1
        
        # Criar registro de débito
        debit_record = CreditBalance(
            user_id=user_id,
            transaction_type='debit',
            amount=1,
            balance_after=new_balance,
            description=description,
            service_type='xml_download',
            created_at=datetime.utcnow()
        )
        
        db.session.add(debit_record)
        db.session.commit()
        
        logger.info(f"Consumido 1 crédito XML para usuário {user_id}. Saldo: {current_balance} → {new_balance}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao consumir crédito XML: {e}")
        db.session.rollback()
        return False

def can_download_xml(user_id):
    """
    Verifica se o usuário pode fazer download de XML (trial ou créditos)
    """
    try:
        from models import User
        user = User.query.get(user_id)
        if not user:
            return False
        
        # Verificar se está em período de trial
        is_trial_active = user.trial_expires_at and user.trial_expires_at > datetime.utcnow()
        if is_trial_active:
            return True
        
        # Verificar se tem créditos suficientes
        balance = get_user_xml_balance(user_id)
        return balance > 0
        
    except Exception as e:
        logger.error(f"Erro ao verificar permissão de download: {e}")
        return False

def get_trial_status(user_id):
    """
    Obter status detalhado do trial do usuário
    """
    try:
        from models import User
        user = User.query.get(user_id)
        if not user:
            return {'active': False, 'days_left': 0}
        
        if user.trial_expires_at and user.trial_expires_at > datetime.utcnow():
            days_left = (user.trial_expires_at - datetime.utcnow()).days
            return {
                'active': True,
                'days_left': max(0, days_left),
                'expires_at': user.trial_expires_at
            }
        else:
            return {'active': False, 'days_left': 0}
            
    except Exception as e:
        logger.error(f"Erro ao obter status do trial: {e}")
        return {'active': False, 'days_left': 0}