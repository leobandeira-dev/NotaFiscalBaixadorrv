"""
Sistema de Pacotes baseado em produtos Stripe
Controle de acesso às funcionalidades por assinatura
"""

from datetime import datetime, timedelta
from models import db

class StripeProduct(db.Model):
    """Produtos do Stripe mapeados para pacotes do sistema"""
    __tablename__ = 'stripe_products'
    
    id = db.Column(db.Integer, primary_key=True)
    stripe_product_id = db.Column(db.String(100), unique=True, nullable=False)  # prod_xxx
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    active = db.Column(db.Boolean, default=True)
    
    # Configurações do pacote
    package_type = db.Column(db.String(50), nullable=False)  # 'xml_credits', 'labels_subscription', 'enterprise'
    credits_amount = db.Column(db.Integer, default=0)  # Para pacotes de créditos XML
    subscription_duration_days = db.Column(db.Integer, default=30)  # Para assinaturas
    
    # Preços (dados do Stripe)
    default_price_id = db.Column(db.String(100), nullable=True)  # price_xxx
    price_amount = db.Column(db.Integer, nullable=True)  # Em centavos
    price_currency = db.Column(db.String(3), default='brl')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    features = db.relationship('PackageFeature', back_populates='product', cascade='all, delete-orphan')
    user_subscriptions = db.relationship('UserSubscription', back_populates='product')

class PackageFeature(db.Model):
    """Funcionalidades disponíveis em cada pacote"""
    __tablename__ = 'package_features'
    
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('stripe_products.id'), nullable=False)
    
    # Identificador da funcionalidade
    feature_key = db.Column(db.String(100), nullable=False)  # 'xml_download', 'danfe_generation', 'transport_labels'
    feature_name = db.Column(db.String(200), nullable=False)
    
    # Limites e configurações
    enabled = db.Column(db.Boolean, default=True)
    usage_limit = db.Column(db.Integer, nullable=True)  # Limite de uso (-1 = ilimitado)
    rate_limit_per_minute = db.Column(db.Integer, default=60)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    product = db.relationship('StripeProduct', back_populates='features')

class UserSubscription(db.Model):
    """Assinaturas ativas dos usuários"""
    __tablename__ = 'user_subscriptions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('stripe_products.id'), nullable=False)
    
    # Dados da assinatura
    stripe_subscription_id = db.Column(db.String(100), unique=True, nullable=True)
    status = db.Column(db.String(50), default='active')  # active, canceled, past_due, etc.
    
    # Período de validade
    starts_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    trial_expires_at = db.Column(db.DateTime, nullable=True)
    
    # Créditos (para pacotes de XML)
    credits_remaining = db.Column(db.Integer, default=0)
    credits_total = db.Column(db.Integer, default=0)
    
    # Controle de renovação
    auto_renew = db.Column(db.Boolean, default=True)
    canceled_at = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    user = db.relationship('User', backref='subscriptions')
    product = db.relationship('StripeProduct', back_populates='user_subscriptions')
    
    def is_active(self):
        """Verifica se a assinatura está ativa"""
        if self.status not in ['active', 'trialing']:
            return False
        
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
            
        return True
    
    def is_trial_active(self):
        """Verifica se o trial está ativo"""
        if not self.trial_expires_at:
            return False
        return self.trial_expires_at > datetime.utcnow()
    
    def has_credits(self):
        """Verifica se tem créditos disponíveis"""
        return self.credits_remaining > 0

class FeatureUsage(db.Model):
    """Controle de uso das funcionalidades"""
    __tablename__ = 'feature_usage'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_id = db.Column(db.Integer, db.ForeignKey('user_subscriptions.id'), nullable=True)
    feature_key = db.Column(db.String(100), nullable=False)
    
    # Dados do uso
    usage_count = db.Column(db.Integer, default=1)
    credits_consumed = db.Column(db.Integer, default=1)  # Créditos consumidos nesta operação
    usage_data = db.Column(db.JSON, nullable=True)  # Dados específicos do uso
    description = db.Column(db.String(500), nullable=True)  # Descrição da operação
    extra_metadata = db.Column(db.JSON, nullable=True)  # Metadados adicionais
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    user = db.relationship('User')
    subscription = db.relationship('UserSubscription')

# StripeTransaction is already defined in models.py - using that one to avoid conflicts

def init_stripe_products():
    """Inicializar produtos padrão do Stripe"""
    
    # Produto: Créditos XML
    xml_credits_product = StripeProduct.query.filter_by(
        stripe_product_id='prod_SWv7Mmc4YDzCal'
    ).first()
    
    if not xml_credits_product:
        xml_credits_product = StripeProduct(
            stripe_product_id='prod_SWv7Mmc4YDzCal',
            name='Créditos para Download de XMLs',
            description='Créditos para download de arquivos XML de notas fiscais',
            package_type='xml_credits',
            credits_amount=1,  # 1 crédito por compra
            default_price_id='price_1QXOcqP4kAmBx7z3S9lKi5oF',
            price_amount=10,  # R$ 0,10 em centavos
            price_currency='brl'
        )
        db.session.add(xml_credits_product)
        
        # Funcionalidades do pacote XML
        xml_features = [
            PackageFeature(
                product=xml_credits_product,
                feature_key='xml_download',
                feature_name='Download de XMLs',
                enabled=True,
                usage_limit=1,  # 1 uso por crédito
                rate_limit_per_minute=30
            ),
            PackageFeature(
                product=xml_credits_product,
                feature_key='danfe_generation',
                feature_name='Geração de DANFE',
                enabled=True,
                usage_limit=-1,  # Ilimitado
                rate_limit_per_minute=10
            )
        ]
        
        for feature in xml_features:
            db.session.add(feature)
    
    # Produto: Módulo de Etiquetas
    labels_product = StripeProduct.query.filter_by(
        stripe_product_id='prod_SSVViDPzXYZHhO'
    ).first()
    
    if not labels_product:
        labels_product = StripeProduct(
            stripe_product_id='prod_SSVViDPzXYZHhO',
            name='Módulo de Etiquetas de Transporte',
            description='Assinatura mensal para geração ilimitada de etiquetas de transporte',
            package_type='labels_subscription',
            subscription_duration_days=30,
            default_price_id='price_1QXOd3P4kAmBx7z3nKdVaKz4',
            price_amount=4990,  # R$ 49,90 em centavos
            price_currency='brl'
        )
        db.session.add(labels_product)
        
        # Funcionalidades do módulo de etiquetas
        labels_features = [
            PackageFeature(
                product=labels_product,
                feature_key='transport_labels',
                feature_name='Etiquetas de Transporte',
                enabled=True,
                usage_limit=-1,  # Ilimitado
                rate_limit_per_minute=20
            ),
            PackageFeature(
                product=labels_product,
                feature_key='label_customization',
                feature_name='Personalização de Etiquetas',
                enabled=True,
                usage_limit=-1,
                rate_limit_per_minute=10
            ),
            PackageFeature(
                product=labels_product,
                feature_key='multi_volume_labels',
                feature_name='Etiquetas Multi-Volume',
                enabled=True,
                usage_limit=-1,
                rate_limit_per_minute=15
            )
        ]
        
        for feature in labels_features:
            db.session.add(feature)
    
    try:
        db.session.commit()
        print("Produtos Stripe inicializados com sucesso")
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao inicializar produtos: {e}")

def get_user_active_subscriptions(user_id):
    """Obter assinaturas ativas do usuário"""
    return UserSubscription.query.filter_by(
        user_id=user_id,
        status='active'
    ).filter(
        UserSubscription.expires_at > datetime.utcnow()
    ).all()

def user_has_feature_access(user_id, feature_key):
    """Verificar se usuário tem acesso a uma funcionalidade"""
    from models import User
    
    user = User.query.get(user_id)
    if not user:
        return False
    
    # Admin sempre tem acesso
    if user.is_admin:
        return True
    
    # Verificar trial geral
    if user.trial_expires_at and user.trial_expires_at > datetime.utcnow():
        return True
    
    # Verificar assinaturas ativas
    active_subscriptions = get_user_active_subscriptions(user_id)
    
    for subscription in active_subscriptions:
        # Verificar se está em trial da assinatura
        if subscription.is_trial_active():
            features = PackageFeature.query.filter_by(
                product_id=subscription.product_id,
                feature_key=feature_key,
                enabled=True
            ).first()
            if features:
                return True
        
        # Verificar assinatura ativa
        if subscription.is_active():
            features = PackageFeature.query.filter_by(
                product_id=subscription.product_id,
                feature_key=feature_key,
                enabled=True
            ).first()
            if features:
                # Para funcionalidades de XML, verificar créditos
                if feature_key == 'xml_download' and subscription.product.package_type == 'xml_credits':
                    return subscription.has_credits()
                return True
    
    return False

def consume_feature_credit(user_id, feature_key, usage_data=None):
    """Consumir crédito de uma funcionalidade"""
    active_subscriptions = get_user_active_subscriptions(user_id)
    
    for subscription in active_subscriptions:
        features = PackageFeature.query.filter_by(
            product_id=subscription.product_id,
            feature_key=feature_key,
            enabled=True
        ).first()
        
        if features and subscription.is_active():
            # Para downloads de XML, consumir crédito
            if feature_key == 'xml_download' and subscription.credits_remaining > 0:
                subscription.credits_remaining -= 1
                
                # Registrar uso
                usage = FeatureUsage(
                    user_id=user_id,
                    subscription_id=subscription.id,
                    feature_key=feature_key,
                    usage_data=usage_data
                )
                db.session.add(usage)
                db.session.commit()
                return True
            
            # Para outras funcionalidades (ilimitadas)
            elif feature_key != 'xml_download':
                usage = FeatureUsage(
                    user_id=user_id,
                    subscription_id=subscription.id,
                    feature_key=feature_key,
                    usage_data=usage_data
                )
                db.session.add(usage)
                db.session.commit()
                return True
    
    return False