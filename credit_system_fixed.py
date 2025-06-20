"""
Sistema de Créditos XML Corrigido
Funções para calcular e exibir corretamente saldos e histórico de créditos
"""
from sqlalchemy import func
from models import db, StripeTransaction, CreditBalance, UsageRecord
from flask_login import current_user
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def get_user_xml_balance(user_id):
    """
    Calcula o saldo atual de créditos XML do usuário
    """
    try:
        # Buscar último saldo na tabela credit_balances
        last_balance = db.session.query(CreditBalance)\
            .filter(CreditBalance.user_id == user_id)\
            .order_by(CreditBalance.created_at.desc())\
            .first()
        
        if last_balance:
            return int(last_balance.balance_after)
        
        # Fallback: calcular baseado em transações Stripe
        total_purchased = db.session.query(func.sum(StripeTransaction.credits_purchased))\
            .filter(
                StripeTransaction.user_id == user_id,
                StripeTransaction.status == 'completed'
            ).scalar() or 0
        
        # Contar downloads (consumos) usando UsageRecord
        total_consumed = db.session.query(func.count(UsageRecord.id))\
            .filter(
                UsageRecord.user_id == user_id,
                UsageRecord.service_type == 'xml_download'
            ).scalar() or 0
        
        return max(0, int(total_purchased) - int(total_consumed))
        
    except Exception as e:
        logger.error(f"Erro ao calcular saldo XML do usuário {user_id}: {e}")
        return 0

def get_credit_history(user_id, limit=20):
    """
    Obtém histórico de créditos do usuário
    """
    try:
        # Histórico da tabela credit_balances
        credit_records = db.session.query(CreditBalance)\
            .filter(CreditBalance.user_id == user_id)\
            .order_by(CreditBalance.created_at.desc())\
            .limit(limit)\
            .all()
        
        history = []
        for record in credit_records:
            history.append({
                'data': record.created_at,
                'tipo': 'Compra' if record.transaction_type == 'credit' else 'Consumo',
                'quantidade': int(record.amount),
                'saldo_final': int(record.balance_after),
                'descricao': record.description
            })
        
        return history
        
    except Exception as e:
        logger.error(f"Erro ao obter histórico de créditos do usuário {user_id}: {e}")
        return []

def consume_xml_credit_fixed(user_id):
    """
    Consome 1 crédito XML do usuário e atualiza o saldo
    """
    try:
        current_balance = get_user_xml_balance(user_id)
        
        if current_balance <= 0:
            return False
        
        # Registrar consumo
        new_balance = current_balance - 1
        
        credit_record = CreditBalance(
            user_id=user_id,
            transaction_type='debit',
            amount=-1,
            balance_after=new_balance,
            description='Consumo de 1 crédito XML - Download automático',
            service_type='xml_credits',
            created_at=datetime.utcnow()
        )
        
        db.session.add(credit_record)
        
        # Registrar na tabela de uso
        usage_record = UsageRecord(
            user_id=user_id,
            service_type='xml_download',
            amount=1,
            description='Download XML automático',
            created_at=datetime.utcnow()
        )
        
        db.session.add(usage_record)
        db.session.commit()
        
        logger.info(f"Crédito XML consumido. Usuário {user_id}: {current_balance} -> {new_balance}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao consumir crédito XML do usuário {user_id}: {e}")
        db.session.rollback()
        return False

def add_xml_credits_fixed(user_id, credits, transaction_id=None, description=None):
    """
    Adiciona créditos XML ao usuário
    """
    try:
        current_balance = get_user_xml_balance(user_id)
        new_balance = current_balance + credits
        
        if not description:
            description = f'Compra de {credits} créditos XML via Stripe'
        
        credit_record = CreditBalance(
            user_id=user_id,
            transaction_type='credit',
            amount=credits,
            balance_after=new_balance,
            description=description,
            service_type='xml_credits',
            reference_id=transaction_id,
            created_at=datetime.utcnow()
        )
        
        db.session.add(credit_record)
        db.session.commit()
        
        logger.info(f"Créditos XML adicionados. Usuário {user_id}: {current_balance} -> {new_balance}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao adicionar créditos XML do usuário {user_id}: {e}")
        db.session.rollback()
        return False

def get_user_stats(user_id):
    """
    Estatísticas completas do usuário
    """
    try:
        current_balance = get_user_xml_balance(user_id)
        
        total_purchased = db.session.query(func.sum(StripeTransaction.credits_purchased))\
            .filter(
                StripeTransaction.user_id == user_id,
                StripeTransaction.status == 'completed'
            ).scalar() or 0
        
        total_consumed = db.session.query(func.count(FeatureUsage.id))\
            .filter(
                FeatureUsage.user_id == user_id,
                FeatureUsage.feature_key == 'xml_download'
            ).scalar() or 0
        
        return {
            'saldo_atual': current_balance,
            'total_comprado': int(total_purchased),
            'total_consumido': int(total_consumed),
            'economia_tempo': total_consumed * 5,  # 5 min por XML
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas do usuário {user_id}: {e}")
        return {
            'saldo_atual': 0,
            'total_comprado': 0, 
            'total_consumido': 0,
            'economia_tempo': 0
        }