"""
Sistema de Preços Dinâmicos para XMLs baseado em Volume
Integração com botões de compra Stripe
"""

import os
import stripe
import logging
from datetime import datetime, timedelta
from models import db, User, StripeTransaction
from package_models import StripeProduct, UserSubscription, FeatureUsage

# Configure logger
logger = logging.getLogger(__name__)

# Configurar Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

class XMLPricingTiers:
    """Estrutura de preços por volume de XMLs"""
    
    TIERS = [
        {
            'name': 'Pacote Básico',
            'xml_count': 100,
            'price_per_xml': 0.10,
            'total_price': 10.00,
            'savings': 0,
            'stripe_buy_button_id': 'buy_btn_1RbrKZKpjVGFiyHCl3l2hMEp',
            'stripe_price_id': 'price_basic_100',
            'description': 'Ideal para uso ocasional'
        },
        {
            'name': 'Pacote Profissional',
            'xml_count': 500,
            'price_per_xml': 0.08,
            'total_price': 40.00,
            'savings': 20,
            'stripe_buy_button_id': 'buy_btn_professional_500',
            'stripe_price_id': 'price_professional_500',
            'description': 'Para empresas de médio porte'
        },
        {
            'name': 'Pacote Empresarial',
            'xml_count': 1000,
            'price_per_xml': 0.07,
            'total_price': 70.00,
            'savings': 30,
            'stripe_buy_button_id': 'buy_btn_enterprise_1000',
            'stripe_price_id': 'price_enterprise_1000',
            'description': 'Para grandes volumes'
        },
        {
            'name': 'Pacote Corporativo',
            'xml_count': 2000,
            'price_per_xml': 0.06,
            'total_price': 120.00,
            'savings': 40,
            'stripe_buy_button_id': 'buy_btn_corporate_2000',
            'stripe_price_id': 'price_corporate_2000',
            'description': 'Para operações em larga escala'
        }
    ]
    
    @classmethod
    def get_tier_by_count(cls, xml_count):
        """Obter tier mais próximo para quantidade específica"""
        for tier in cls.TIERS:
            if xml_count <= tier['xml_count']:
                return tier
        return cls.TIERS[-1]  # Retorna o maior tier
    
    @classmethod
    def calculate_price(cls, xml_count):
        """Calcular preço para quantidade específica de XMLs"""
        tier = cls.get_tier_by_count(xml_count)
        return {
            'xml_count': xml_count,
            'price_per_xml': tier['price_per_xml'],
            'total_price': xml_count * tier['price_per_xml'],
            'recommended_tier': tier,
            'savings_vs_basic': (xml_count * 0.10) - (xml_count * tier['price_per_xml'])
        }
    
    @classmethod
    def get_all_tiers(cls):
        """Obter todos os tiers disponíveis"""
        return cls.TIERS

def create_xml_credit_subscription(user_id, tier_data, stripe_session_id=None):
    """Criar assinatura de créditos XML após pagamento confirmado"""
    try:
        user = User.query.get(user_id)
        if not user:
            return False
        
        # Buscar produto XML no sistema
        xml_product = StripeProduct.query.filter_by(
            package_type='xml_credits'
        ).first()
        
        if not xml_product:
            return False
        
        # Criar assinatura de créditos
        subscription = UserSubscription(
            user_id=user_id,
            product_id=xml_product.id,
            stripe_subscription_id=stripe_session_id,
            status='active',
            starts_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=365),  # Créditos válidos por 1 ano
            credits_remaining=tier_data['xml_count'],
            credits_total=tier_data['xml_count'],
            auto_renew=False  # Créditos não renovam automaticamente
        )
        
        db.session.add(subscription)
        db.session.commit()
        
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao criar assinatura de créditos: {e}")
        return False

def get_user_xml_credits(user_id):
    """Obter total de créditos XML disponíveis para o usuário"""
    try:
        total_credits = db.session.query(
            db.func.sum(UserSubscription.credits_remaining)
        ).filter(
            UserSubscription.user_id == user_id,
            UserSubscription.status == 'active',
            UserSubscription.expires_at > datetime.utcnow()
        ).scalar() or 0
        
        return int(total_credits)
        
    except Exception as e:
        print(f"Erro ao obter créditos XML: {e}")
        return 0

def consume_xml_credit(user_id):
    """Consumir um crédito XML do usuário"""
    try:
        # Buscar assinatura com créditos disponíveis
        subscription = UserSubscription.query.filter(
            UserSubscription.user_id == user_id,
            UserSubscription.status == 'active',
            UserSubscription.credits_remaining > 0,
            UserSubscription.expires_at > datetime.utcnow()
        ).order_by(UserSubscription.expires_at).first()
        
        if not subscription:
            return False
        
        # Consumir crédito
        subscription.credits_remaining -= 1
        db.session.commit()
        
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao consumir crédito XML: {e}")
        return False

def get_pricing_recommendations(user_id=None):
    """Obter recomendações de preços personalizadas"""
    recommendations = []
    
    for tier in XMLPricingTiers.TIERS:
        # Calcular economia
        basic_price = tier['xml_count'] * 0.10
        tier_price = tier['total_price']
        savings_amount = basic_price - tier_price
        savings_percentage = (savings_amount / basic_price) * 100 if basic_price > 0 else 0
        
        recommendation = {
            **tier,
            'savings_amount': savings_amount,
            'savings_percentage': savings_percentage,
            'cost_per_month': tier['total_price'] / 12,  # Distribuído em 12 meses
            'monthly_xml_capacity': tier['xml_count'] / 12
        }
        
        recommendations.append(recommendation)
    
    return recommendations

def validate_stripe_session(session_id):
    """Validar sessão de checkout do Stripe"""
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        return {
            'valid': True,
            'customer_email': session.customer_details.email if session.customer_details else None,
            'amount_total': session.amount_total,
            'payment_status': session.payment_status,
            'metadata': session.metadata or {}
        }
    except Exception as e:
        print(f"Erro ao validar sessão Stripe: {e}")
        return {'valid': False}

def create_stripe_checkout_session(tier_data, user_email, success_url, cancel_url):
    """Criar sessão de checkout personalizada no Stripe"""
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'brl',
                    'product_data': {
                        'name': f'{tier_data["name"]} - {tier_data["xml_count"]} XMLs',
                        'description': tier_data['description'],
                        'metadata': {
                            'xml_count': tier_data['xml_count'],
                            'tier_name': tier_data['name']
                        }
                    },
                    'unit_amount': int(tier_data['total_price'] * 100),  # Stripe usa centavos
                },
                'quantity': 1,
            }],
            mode='payment',
            customer_email=user_email,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={
                'xml_count': tier_data['xml_count'],
                'tier_name': tier_data['name'],
                'user_email': user_email
            }
        )
        
        return {
            'success': True,
            'session_id': session.id,
            'checkout_url': session.url
        }
        
    except Exception as e:
        print(f"Erro ao criar sessão de checkout: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def get_user_xml_credits(user_id: int) -> int:
    """
    Obter quantidade de créditos XML disponíveis para o usuário
    
    Args:
        user_id: ID do usuário
        
    Returns:
        Quantidade de créditos XML disponíveis
    """
    try:
        from models import db, StripeTransaction
        from package_models import FeatureUsage
        from sqlalchemy import func
        
        # Somar todas as compras de créditos XML
        total_purchased = db.session.query(func.sum(StripeTransaction.credits_purchased))\
            .filter(
                StripeTransaction.user_id == user_id,
                StripeTransaction.status == 'paid',
                StripeTransaction.product_type == 'xml_credits'
            ).scalar() or 0
        
        # Somar todos os créditos consumidos
        total_consumed = db.session.query(func.sum(FeatureUsage.credits_consumed))\
            .filter(
                FeatureUsage.user_id == user_id,
                FeatureUsage.feature_key == 'xml_download'
            ).scalar() or 0
        
        # Créditos disponíveis = comprados - consumidos
        available_credits = int(total_purchased) - int(total_consumed)
        
        return max(0, available_credits)  # Nunca retornar negativo
        
    except Exception as e:
        logger.error(f"Erro ao obter créditos XML do usuário {user_id}: {e}")
        return 0

def consume_xml_credit(user_id: int) -> bool:
    """
    Consumir 1 crédito XML do usuário
    
    Args:
        user_id: ID do usuário
        
    Returns:
        True se crédito foi consumido com sucesso
    """
    try:
        # Verificar se usuário tem créditos suficientes
        available_credits = get_user_xml_credits(user_id)
        if available_credits <= 0:
            return False
        
        # Registrar consumo será feito pelo decorator automaticamente
        return True
        
    except Exception as e:
        logger.error(f"Erro ao consumir crédito XML do usuário {user_id}: {e}")
        return False

def get_xml_usage_stats(user_id: int) -> dict:
    """
    Obter estatísticas completas de uso de créditos XML
    
    Args:
        user_id: ID do usuário
        
    Returns:
        Dicionário com estatísticas de uso
    """
    try:
        from models import db, StripeTransaction
        from package_models import FeatureUsage
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        # Total comprado
        total_purchased = db.session.query(func.sum(StripeTransaction.credits_added))\
            .filter(
                StripeTransaction.user_id == user_id,
                StripeTransaction.status == 'paid',
                StripeTransaction.product_type == 'xml_credits'
            ).scalar() or 0
        
        # Total consumido
        total_consumed = db.session.query(func.sum(FeatureUsage.credits_consumed))\
            .filter(
                FeatureUsage.user_id == user_id,
                FeatureUsage.feature_key == 'xml_download'
            ).scalar() or 0
        
        # Consumo este mês
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month_consumed = db.session.query(func.sum(FeatureUsage.credits_consumed))\
            .filter(
                FeatureUsage.user_id == user_id,
                FeatureUsage.feature_key == 'xml_download',
                FeatureUsage.created_at >= month_start
            ).scalar() or 0
        
        # Média diária dos últimos 30 dias
        thirty_days_ago = datetime.now() - timedelta(days=30)
        last_30_days_consumed = db.session.query(func.sum(FeatureUsage.credits_consumed))\
            .filter(
                FeatureUsage.user_id == user_id,
                FeatureUsage.feature_key == 'xml_download',
                FeatureUsage.created_at >= thirty_days_ago
            ).scalar() or 0
        
        avg_daily_usage = last_30_days_consumed / 30 if last_30_days_consumed > 0 else 0
        
        return {
            'total_purchased': int(total_purchased),
            'total_consumed': int(total_consumed),
            'this_month_consumed': int(this_month_consumed),
            'avg_daily_usage': round(avg_daily_usage, 1)
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas de uso XML do usuário {user_id}: {e}")
        return {
            'total_purchased': 0,
            'total_consumed': 0,
            'this_month_consumed': 0,
            'avg_daily_usage': 0
        }

def add_xml_credits_to_user(user_id: int, credits: int, transaction_id: str = None) -> bool:
    """
    Adicionar créditos XML ao usuário após compra
    
    Args:
        user_id: ID do usuário
        credits: Quantidade de créditos a adicionar
        transaction_id: ID da transação Stripe
        
    Returns:
        True se créditos foram adicionados com sucesso
    """
    try:
        from models import db
        from package_models import StripeTransaction
        from datetime import datetime
        
        # Criar registro da transação
        transaction = StripeTransaction(
            user_id=user_id,
            stripe_transaction_id=transaction_id or f"manual_{datetime.now().timestamp()}",
            amount=0.0,  # Será atualizado pelo webhook
            status='paid',
            product_type='xml_credits',
            credits_added=credits,
            package_name=f"Pacote {credits} XMLs",
            created_at=datetime.utcnow()
        )
        
        db.session.add(transaction)
        db.session.commit()
        
        logger.info(f"Adicionados {credits} créditos XML ao usuário {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Erro ao adicionar créditos XML ao usuário {user_id}: {e}")
        db.session.rollback()
        return False

def get_pricing_recommendations(user_id: int) -> dict:
    """
    Obter recomendações de pacotes baseadas no histórico do usuário
    
    Args:
        user_id: ID do usuário
        
    Returns:
        Dicionário com recomendações
    """
    try:
        stats = get_xml_usage_stats(user_id)
        current_credits = get_user_xml_credits(user_id)
        
        # Calcular uso médio mensal
        monthly_usage = stats.get('avg_daily_usage', 0) * 30
        
        # Recomendação baseada no uso
        if monthly_usage <= 100:
            recommended_tier = 'starter'
            recommended_message = "Baseado no seu uso, o pacote Starter (100 XMLs) é ideal para você."
        elif monthly_usage <= 500:
            recommended_tier = 'professional'
            recommended_message = "Baseado no seu uso, o pacote Professional (500 XMLs) oferece melhor custo-benefício."
        elif monthly_usage <= 1000:
            recommended_tier = 'business'
            recommended_message = "Baseado no seu uso, o pacote Business (1000 XMLs) é recomendado."
        else:
            recommended_tier = 'enterprise'
            recommended_message = "Baseado no seu alto volume, o pacote Enterprise (2000 XMLs) oferece o melhor preço por XML."
        
        # Previsão de duração dos créditos atuais
        days_remaining = 0
        if current_credits > 0 and stats.get('avg_daily_usage', 0) > 0:
            days_remaining = current_credits / stats.get('avg_daily_usage', 1)
        
        return {
            'recommended_tier': recommended_tier,
            'recommended_message': recommended_message,
            'monthly_usage_estimate': int(monthly_usage),
            'days_remaining': int(days_remaining),
            'should_buy_soon': days_remaining < 7 and current_credits < 20
        }
        
    except Exception as e:
        logger.error(f"Erro ao obter recomendações para usuário {user_id}: {e}")
        return {
            'recommended_tier': 'starter',
            'recommended_message': "Comece com o pacote Starter para testar o sistema.",
            'monthly_usage_estimate': 0,
            'days_remaining': 0,
            'should_buy_soon': False
        }