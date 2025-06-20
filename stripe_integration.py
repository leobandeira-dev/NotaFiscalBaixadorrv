"""
Integração com Stripe para sistema de pagamentos
Sistema de saldos pré-pagos com cobrança por uso
"""

import os
import stripe
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from flask import current_app
from models import db
from models import User, UsageRecord, Charge

# Configurar chave da API Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

class StripePaymentManager:
    """Gerenciador de pagamentos Stripe com sistema de saldos"""
    
    def __init__(self):
        self.api_key = os.environ.get('STRIPE_SECRET_KEY')
        if not self.api_key:
            raise ValueError("STRIPE_SECRET_KEY não configurada")
        stripe.api_key = self.api_key
    
    def create_payment_intent(self, amount_cents: int, currency: str = 'brl', 
                            customer_email: str = None, metadata: Dict = None) -> Dict[str, Any]:
        """
        Cria um Payment Intent para pagamento único
        
        Args:
            amount_cents: Valor em centavos (ex: 1990 = R$ 19,90)
            currency: Moeda (padrão BRL)
            customer_email: Email do cliente
            metadata: Dados adicionais
            
        Returns:
            Dados do Payment Intent criado
        """
        try:
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency,
                automatic_payment_methods={'enabled': True},
                receipt_email=customer_email,
                metadata=metadata or {}
            )
            
            current_app.logger.info(f"Payment Intent criado: {payment_intent.id}")
            return {
                'success': True,
                'payment_intent_id': payment_intent.id,
                'client_secret': payment_intent.client_secret,
                'amount': amount_cents,
                'currency': currency
            }
            
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Erro ao criar Payment Intent: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_checkout_session(self, price_data: Dict[str, Any], 
                              success_url: str, cancel_url: str,
                              customer_email: str = None, 
                              metadata: Dict = None) -> Dict[str, Any]:
        """
        Cria uma sessão de checkout Stripe
        
        Args:
            price_data: Dados do preço/produto
            success_url: URL de sucesso
            cancel_url: URL de cancelamento
            customer_email: Email do cliente
            metadata: Dados adicionais
            
        Returns:
            Dados da sessão de checkout
        """
        try:
            session_data = {
                'line_items': [{
                    'price_data': price_data,
                    'quantity': 1,
                }],
                'mode': 'payment',
                'success_url': success_url,
                'cancel_url': cancel_url,
                'metadata': metadata or {}
            }
            
            if customer_email:
                session_data['customer_email'] = customer_email
            
            session = stripe.checkout.Session.create(**session_data)
            
            current_app.logger.info(f"Checkout Session criada: {session.id}")
            return {
                'success': True,
                'session_id': session.id,
                'checkout_url': session.url
            }
            
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Erro ao criar Checkout Session: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def retrieve_payment_intent(self, payment_intent_id: str) -> Dict[str, Any]:
        """Recupera informações de um Payment Intent"""
        try:
            payment_intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                'success': True,
                'payment_intent': payment_intent
            }
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Erro ao recuperar Payment Intent: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def retrieve_checkout_session(self, session_id: str) -> Dict[str, Any]:
        """Recupera informações de uma sessão de checkout"""
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            return {
                'success': True,
                'session': session
            }
        except stripe.error.StripeError as e:
            current_app.logger.error(f"Erro ao recuperar Checkout Session: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

class CreditManager:
    """Gerenciador de créditos/saldos do usuário"""
    
    @staticmethod
    def add_credits(user_id: int, amount: float, description: str = "Créditos adicionados",
                   payment_method: str = "stripe", transaction_id: str = None) -> bool:
        """
        Adiciona créditos ao saldo do usuário
        
        Args:
            user_id: ID do usuário
            amount: Valor em reais
            description: Descrição da transação
            payment_method: Método de pagamento
            transaction_id: ID da transação externa
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            user = User.query.get(user_id)
            if not user:
                current_app.logger.error(f"Usuário {user_id} não encontrado")
                return False
            
            # Atualizar saldo do usuário
            user.current_balance = (user.current_balance or 0) + amount
            
            # Registrar transação
            charge = Charge(
                user_id=user_id,
                amount=amount,
                description=description,
                payment_method=payment_method,
                transaction_id=transaction_id,
                status='completed',
                created_at=datetime.now()
            )
            
            db.session.add(charge)
            db.session.commit()
            
            current_app.logger.info(f"Créditos adicionados: R$ {amount} para usuário {user_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao adicionar créditos: {str(e)}")
            return False
    
    @staticmethod
    def deduct_credits(user_id: int, amount: float, description: str = "Uso de créditos",
                      service_type: str = "xml_download") -> bool:
        """
        Deduz créditos do saldo do usuário
        
        Args:
            user_id: ID do usuário
            amount: Valor a deduzir
            description: Descrição do uso
            service_type: Tipo de serviço usado
            
        Returns:
            True se sucesso, False se saldo insuficiente
        """
        try:
            user = User.query.get(user_id)
            if not user:
                current_app.logger.error(f"Usuário {user_id} não encontrado")
                return False
            
            # Verificar se usuário está em período de teste
            if user.is_trial_active():
                current_app.logger.info(f"Usuário {user_id} em período de teste - sem cobrança")
                return True
            
            # Verificar saldo suficiente
            current_balance = user.current_balance or 0
            if current_balance < amount:
                current_app.logger.warning(f"Saldo insuficiente para usuário {user_id}: R$ {current_balance} < R$ {amount}")
                return False
            
            # Deduzir saldo
            user.current_balance = current_balance - amount
            
            # Registrar uso
            usage = UsageRecord(
                user_id=user_id,
                service_type=service_type,
                amount_charged=amount,
                description=description,
                usage_date=datetime.now()
            )
            
            db.session.add(usage)
            db.session.commit()
            
            current_app.logger.info(f"Créditos deduzidos: R$ {amount} do usuário {user_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao deduzir créditos: {str(e)}")
            return False
    
    @staticmethod
    def get_user_balance(user_id: int) -> float:
        """Retorna o saldo atual do usuário"""
        user = User.query.get(user_id)
        return user.current_balance if user else 0.0
    
    @staticmethod
    def get_usage_history(user_id: int, days: int = 30) -> List[Dict]:
        """Retorna histórico de uso dos últimos N dias"""
        start_date = datetime.now() - timedelta(days=days)
        
        usage_records = UsageRecord.query.filter(
            UsageRecord.user_id == user_id,
            UsageRecord.created_at >= start_date
        ).order_by(UsageRecord.created_at.desc()).all()
        
        return [{
            'date': record.created_at.strftime('%d/%m/%Y %H:%M') if record.created_at else 'N/A',
            'service': 'xml_download',  # Serviço padrão
            'amount': record.cost,
            'description': record.description or 'Download XML'
        } for record in usage_records]

class PricingManager:
    """Gerenciador de preços e pacotes"""
    
    # IDs dos produtos Stripe
    STRIPE_PRODUCTS = {
        'xml_download': 'prod_SWv7Mmc4YDzCal',  # Download XML
        'labels_module': 'prod_SSVViDPzXYZHhO',  # Etiquetas de Transporte
    }
    
    # Preços escalonados por volume para XML
    XML_VOLUME_PRICING = {
        # Faixas de volume: (quantidade_min, quantidade_max, preço_unitário)
        (1, 500): 0.10,      # 1-500 XMLs: R$ 0,10 cada
        (501, 1000): 0.08,   # 501-1.000: R$ 0,08 cada
        (1001, 2000): 0.07,  # 1.001-2.000: R$ 0,07 cada
        (2001, float('inf')): 0.06  # 2.001+: R$ 0,06 cada
    }
    
    # Preços em reais
    PRICES = {
        'xml_download': 0.10,  # Preço base - calculado dinamicamente por volume
        'labels_module': 49.90,  # R$ 49,90 mensal para módulo de etiquetas - Produto Stripe: prod_SSVViDPzXYZHhO
        'danfe_generation': 0.00,  # Gratuito - sempre incluído
    }
    
    # Pacotes de créditos
    CREDIT_PACKAGES = {
        'starter_500': {
            'name': 'Starter 500 XML',
            'credits': 50.0,  # R$ 50,00 em créditos (500 XMLs)
            'price_brl': 4990,  # R$ 49,90 em centavos
            'description': '500 downloads de XML por R$ 49,90'
        },
        'professional_1500': {
            'name': 'Professional 1500 XML', 
            'credits': 120.0,  # R$ 120,00 em créditos (1500 XMLs) com desconto
            'price_brl': 11990,  # R$ 119,90 em centavos  
            'description': '1500 downloads de XML por R$ 119,90'
        },
        'enterprise_5000': {
            'name': 'Enterprise 5000 XML',
            'credits': 350.0,  # R$ 350,00 em créditos (5000 XMLs) com desconto
            'price_brl': 34990,  # R$ 349,90 em centavos
            'description': '5000 downloads de XML por R$ 349,90'
        }
    }
    
    @classmethod
    def get_xml_price_by_volume(cls, quantity: int) -> float:
        """Retorna o preço por XML baseado na quantidade"""
        for (min_qty, max_qty), price in cls.XML_VOLUME_PRICING.items():
            if min_qty <= quantity <= max_qty:
                return price
        return cls.PRICES['xml_download']  # Preço padrão se não encontrar faixa
    
    @classmethod
    def calculate_total_xml_cost(cls, quantity: int) -> Dict[str, Any]:
        """Calcula o custo total para uma quantidade de XMLs com preços escalonados"""
        total_cost = 0.0
        breakdown = []
        remaining = quantity
        
        # Ordenar faixas por quantidade mínima
        sorted_ranges = sorted(cls.XML_VOLUME_PRICING.items(), key=lambda x: x[0][0])
        
        for (min_qty, max_qty), price in sorted_ranges:
            if remaining <= 0:
                break
                
            # Calcular quantos XMLs se enquadram nesta faixa
            range_start = max(1, min_qty - (quantity - remaining))
            range_end = min(max_qty, min_qty + remaining - 1)
            
            if range_start <= range_end:
                qty_in_range = range_end - range_start + 1
                if qty_in_range > remaining:
                    qty_in_range = remaining
                    
                cost_in_range = qty_in_range * price
                total_cost += cost_in_range
                
                breakdown.append({
                    'quantity': qty_in_range,
                    'price_per_unit': price,
                    'subtotal': cost_in_range,
                    'range': f"{min_qty}-{max_qty if max_qty != float('inf') else '∞'}"
                })
                
                remaining -= qty_in_range
        
        return {
            'total_cost': total_cost,
            'average_price': total_cost / quantity if quantity > 0 else 0,
            'breakdown': breakdown,
            'total_quantity': quantity
        }
    
    @classmethod
    def get_service_price(cls, service_type: str, quantity: int = 1) -> float:
        """Retorna o preço de um serviço"""
        if service_type == 'xml_download':
            return cls.get_xml_price_by_volume(quantity)
        return cls.PRICES.get(service_type, 0.0)
    
    @classmethod
    def get_credit_package(cls, package_id: str) -> Optional[Dict]:
        """Retorna informações de um pacote de créditos"""
        return cls.CREDIT_PACKAGES.get(package_id)
    
    @classmethod
    def calculate_xml_package_savings(cls, package_id: str) -> Dict[str, Any]:
        """Calcula economia de um pacote vs preço unitário"""
        package = cls.get_credit_package(package_id)
        if not package:
            return {}
        
        xml_count = int(package['credits'] / cls.PRICES['xml_download'])
        unit_price_total = xml_count * cls.PRICES['xml_download'] * 100  # Em centavos
        package_price = package['price_brl']
        savings = unit_price_total - package_price
        savings_percent = (savings / unit_price_total) * 100
        
        return {
            'xml_count': xml_count,
            'unit_price_total_brl': unit_price_total,
            'package_price_brl': package_price,
            'savings_brl': savings,
            'savings_percent': round(savings_percent, 1)
        }
    
    @classmethod
    def create_labels_subscription(cls, user_id: int) -> Dict[str, Any]:
        """Cria assinatura mensal do módulo de etiquetas"""
        try:
            import stripe
            from models import User, db
            
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'Usuário não encontrado'}
            
            # Criar customer no Stripe se não existir
            customer_data = {
                'email': user.email,
                'name': user.name,
                'metadata': {'user_id': str(user_id)}
            }
            
            customer = stripe.Customer.create(**customer_data)
            
            # Criar assinatura para o produto de etiquetas
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{
                    'price_data': {
                        'currency': 'brl',
                        'product': cls.STRIPE_PRODUCTS['labels_module'],
                        'unit_amount': int(cls.PRICES['labels_module'] * 100),  # R$ 49,90 em centavos
                        'recurring': {'interval': 'month'}
                    }
                }],
                payment_behavior='default_incomplete',
                expand=['latest_invoice.payment_intent'],
            )
            
            return {
                'success': True,
                'subscription_id': subscription.id,
                'client_secret': subscription.latest_invoice.payment_intent.client_secret,
                'customer_id': customer.id
            }
            
        except Exception as e:
            logger.error(f"Erro ao criar assinatura de etiquetas: {str(e)}")
            return {'success': False, 'error': str(e)}

def process_stripe_webhook(payload: bytes, sig_header: str, endpoint_secret: str) -> Dict[str, Any]:
    """
    Processa webhook do Stripe
    
    Args:
        payload: Dados do webhook
        sig_header: Cabeçalho de assinatura
        endpoint_secret: Segredo do endpoint webhook
        
    Returns:
        Resultado do processamento
    """
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        
        current_app.logger.info(f"Webhook recebido: {event['type']}")
        
        # Processar diferentes tipos de eventos
        if event['type'] == 'payment_intent.succeeded':
            payment_intent = event['data']['object']
            return handle_payment_success(payment_intent)
            
        elif event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            return handle_checkout_success(session)
            
        else:
            current_app.logger.info(f"Evento não processado: {event['type']}")
            return {'success': True, 'message': 'Evento não processado'}
            
    except ValueError as e:
        current_app.logger.error(f"Payload inválido: {str(e)}")
        return {'success': False, 'error': 'Payload inválido'}
        
    except stripe.error.SignatureVerificationError as e:
        current_app.logger.error(f"Assinatura inválida: {str(e)}")
        return {'success': False, 'error': 'Assinatura inválida'}

def handle_payment_success(payment_intent) -> Dict[str, Any]:
    """Processa pagamento bem-sucedido"""
    try:
        metadata = payment_intent.get('metadata', {})
        user_id = metadata.get('user_id')
        package_id = metadata.get('package_id')
        
        if not user_id:
            current_app.logger.error("user_id não encontrado no metadata")
            return {'success': False, 'error': 'user_id não encontrado'}
        
        # Adicionar créditos ao usuário
        if package_id:
            package = PricingManager.get_credit_package(package_id)
            if package:
                credits_added = CreditManager.add_credits(
                    user_id=int(user_id),
                    amount=package['credits'],
                    description=f"Compra: {package['name']}",
                    payment_method="stripe",
                    transaction_id=payment_intent['id']
                )
                
                if credits_added:
                    current_app.logger.info(f"Créditos adicionados com sucesso para usuário {user_id}")
                    return {'success': True, 'credits_added': package['credits']}
        
        return {'success': False, 'error': 'Erro ao processar pagamento'}
        
    except Exception as e:
        current_app.logger.error(f"Erro ao processar pagamento: {str(e)}")
        return {'success': False, 'error': str(e)}

def handle_checkout_success(session) -> Dict[str, Any]:
    """Processa checkout bem-sucedido"""
    return handle_payment_success(session)