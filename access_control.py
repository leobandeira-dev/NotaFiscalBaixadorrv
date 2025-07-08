"""
Sistema de Controle de Acesso baseado em Pacotes Stripe
Decoradores para proteger rotas e funcionalidades
"""

from functools import wraps
from datetime import datetime, timedelta
from flask import jsonify, flash, redirect, url_for, request
from flask_login import current_user
from package_models import user_has_feature_access, consume_feature_credit

def require_feature(feature_key, consume_credit=False, error_message=None):
    """
    Decorator para proteger rotas que requerem funcionalidades específicas
    
    Args:
        feature_key: Chave da funcionalidade (xml_download, transport_labels, etc.)
        consume_credit: Se deve consumir crédito ao acessar
        error_message: Mensagem de erro customizada
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.is_json:
                    return jsonify({'error': 'Login necessário', 'redirect': url_for('login')}), 401
                flash('Faça login para acessar esta funcionalidade.', 'warning')
                return redirect(url_for('login'))
            
            # Verificar acesso à funcionalidade
            has_access = user_has_feature_access(current_user.id, feature_key)
            
            if not has_access:
                default_messages = {
                    'xml_download': 'Você não possui créditos para download de XMLs. Adquira créditos para continuar.',
                    'transport_labels': 'Você não possui assinatura ativa do módulo de etiquetas. Assine para continuar.',
                    'danfe_generation': 'Funcionalidade de DANFE não disponível em seu plano.',
                    'label_customization': 'Personalização de etiquetas disponível apenas com assinatura ativa.',
                    'multi_volume_labels': 'Etiquetas multi-volume disponíveis apenas com assinatura ativa.'
                }
                
                message = error_message or default_messages.get(feature_key, 'Funcionalidade não disponível em seu plano.')
                
                if request.is_json:
                    return jsonify({
                        'error': message,
                        'feature_required': feature_key,
                        'upgrade_url': url_for('pricing')
                    }), 403
                
                flash(message, 'error')
                return redirect(url_for('pricing'))
            
            # Consumir crédito se necessário
            if consume_credit:
                success = consume_feature_credit(
                    current_user.id, 
                    feature_key,
                    {
                        'route': request.endpoint,
                        'ip': request.remote_addr,
                        'user_agent': request.headers.get('User-Agent', '')
                    }
                )
                
                if not success:
                    message = f'Não foi possível consumir crédito para {feature_key}. Verifique seu saldo.'
                    if request.is_json:
                        return jsonify({'error': message}), 402
                    flash(message, 'error')
                    return redirect(url_for('dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_xml_credits(f):
    """Decorator específico para funcionalidades que consomem créditos XML"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': 'Login necessário'}), 401
            flash('Faça login para continuar.', 'warning')
            return redirect(url_for('login'))
        
        # Importar aqui para evitar import circular
        from stripe_pricing_system import get_user_xml_credits, consume_xml_credit
        
        # Verificar se usuário tem créditos XML suficientes
        available_credits = get_user_xml_credits(current_user.id)
        if available_credits <= 0:
            message = 'Você não possui créditos XML suficientes. Compre créditos para continuar.'
            if request.is_json:
                return jsonify({'error': message, 'credits': 0}), 402
            flash(message, 'warning')
            return redirect(url_for('comprar_creditos_xml'))
        
        # Consumir 1 crédito XML
        success = consume_xml_credit(current_user.id)
        if not success:
            message = 'Erro ao processar créditos XML. Tente novamente.'
            if request.is_json:
                return jsonify({'error': message}), 500
            flash(message, 'error')
            return redirect(url_for('dashboard'))
        
        # Registrar uso da funcionalidade para auditoria
        try:
            from package_models import FeatureUsage
            from models import db
            
            usage = FeatureUsage(
                user_id=current_user.id,
                feature_key='xml_download',
                credits_consumed=1,
                metadata={
                    'route': request.endpoint,
                    'ip': request.remote_addr,
                    'timestamp': datetime.utcnow().isoformat()
                }
            )
            db.session.add(usage)
            db.session.commit()
        except Exception as e:
            # Log error but don't fail the request
            print(f"Erro ao registrar uso de crédito XML: {e}")
        
        return f(*args, **kwargs)
    return decorated_function

def require_labels_subscription(f):
    """Decorator específico para módulo de etiquetas"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': 'Login necessário'}), 401
            flash('Faça login para continuar.', 'warning')
            return redirect(url_for('login'))
        
        # Admin tem acesso total ao módulo de etiquetas
        if current_user.is_admin:
            return f(*args, **kwargs)
        
        # Para usuários normais, verificar subscription
        return require_feature('transport_labels')(f)(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """Decorator para funcionalidades administrativas"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.is_json:
                return jsonify({'error': 'Login necessário'}), 401
            flash('Faça login para acessar o painel administrativo.', 'warning')
            return redirect(url_for('login'))
        
        if not current_user.is_admin:
            if request.is_json:
                return jsonify({'error': 'Acesso negado. Privilégios administrativos necessários.'}), 403
            flash('Acesso negado. Você não tem privilégios administrativos.', 'error')
            return redirect(url_for('dashboard'))
        
        return f(*args, **kwargs)
    return decorated_function

def get_user_package_status(user_id):
    """Obter status detalhado dos pacotes do usuário"""
    from package_models import get_user_active_subscriptions, StripeProduct
    from models import User
    
    user = User.query.get(user_id)
    if not user:
        return None
    
    status = {
        'user_id': user_id,
        'is_admin': user.is_admin,
        'trial_active': user.trial_expires_at and user.trial_expires_at > datetime.utcnow(),
        'trial_expires_at': user.trial_expires_at,
        'subscriptions': [],
        'features': {
            'xml_download': False,
            'danfe_generation': False,
            'transport_labels': False,
            'label_customization': False,
            'multi_volume_labels': False
        },
        'credits': {
            'xml_remaining': 0,
            'xml_total': 0
        }
    }
    
    # Se admin, liberar tudo
    if user.is_admin:
        for feature in status['features']:
            status['features'][feature] = True
        return status
    
    # Verificar trial geral
    if status['trial_active']:
        for feature in status['features']:
            status['features'][feature] = True
    
    # Verificar assinaturas ativas
    active_subscriptions = get_user_active_subscriptions(user_id)
    
    for subscription in active_subscriptions:
        sub_data = {
            'id': subscription.id,
            'product_name': subscription.product.name,
            'package_type': subscription.product.package_type,
            'status': subscription.status,
            'expires_at': subscription.expires_at,
            'trial_expires_at': subscription.trial_expires_at,
            'credits_remaining': subscription.credits_remaining,
            'credits_total': subscription.credits_total,
            'is_active': subscription.is_active(),
            'is_trial': subscription.is_trial_active()
        }
        status['subscriptions'].append(sub_data)
        
        # Atualizar funcionalidades disponíveis
        if subscription.is_active() or subscription.is_trial_active():
            for feature in subscription.product.features:
                if feature.enabled:
                    status['features'][feature.feature_key] = True
        
        # Atualizar créditos
        if subscription.product.package_type == 'xml_credits':
            status['credits']['xml_remaining'] += subscription.credits_remaining
            status['credits']['xml_total'] += subscription.credits_total
    
    return status

def check_rate_limit(user_id, feature_key, per_minute_limit=60):
    """Verificar limite de taxa para uma funcionalidade"""
    from datetime import datetime, timedelta
    from package_models import FeatureUsage
    
    # Contar usos na última hora
    one_minute_ago = datetime.utcnow() - timedelta(minutes=1)
    
    recent_usage = FeatureUsage.query.filter(
        FeatureUsage.user_id == user_id,
        FeatureUsage.feature_key == feature_key,
        FeatureUsage.created_at >= one_minute_ago
    ).count()
    
    return recent_usage < per_minute_limit

def get_package_recommendations(user_id):
    """Obter recomendações de pacotes para o usuário"""
    from package_models import StripeProduct, get_user_active_subscriptions
    
    active_subscriptions = get_user_active_subscriptions(user_id)
    active_product_ids = [sub.product_id for sub in active_subscriptions]
    
    # Produtos disponíveis que o usuário não possui
    available_products = StripeProduct.query.filter(
        StripeProduct.active == True,
        ~StripeProduct.id.in_(active_product_ids) if active_product_ids else True
    ).all()
    
    recommendations = []
    for product in available_products:
        rec = {
            'product_id': product.id,
            'stripe_product_id': product.stripe_product_id,
            'name': product.name,
            'description': product.description,
            'package_type': product.package_type,
            'price_amount': product.price_amount,
            'price_currency': product.price_currency,
            'features': [f.feature_name for f in product.features if f.enabled]
        }
        recommendations.append(rec)
    
    return recommendations

# Middleware para injetar status do pacote nos templates
def inject_package_status():
    """Injetar informações de pacote nos templates"""
    if current_user.is_authenticated:
        return {
            'user_package_status': get_user_package_status(current_user.id),
            'package_recommendations': get_package_recommendations(current_user.id)
        }
    return {}