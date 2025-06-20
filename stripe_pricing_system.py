"""
Sistema de Preços Dinâmicos para XMLs baseado em Volume
Integração com botões de compra Stripe
"""

import os
import stripe
from datetime import datetime, timedelta
from models import db, User
from package_models import StripeProduct, UserSubscription

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