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
    Obter saldo atual de créditos XML do usuário
    """
    try:
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
    Consumir um crédito XML do usuário
    """
    try:
        current_balance = get_user_xml_balance(user_id)
        
        if current_balance <= 0:
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
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao consumir crédito XML: {e}")
        db.session.rollback()
        return False