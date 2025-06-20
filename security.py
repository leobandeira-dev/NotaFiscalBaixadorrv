"""
Sistema de Segurança e Isolamento de Dados para Produção
Implementa controle de acesso, validação de permissões e isolamento por usuário
"""

from functools import wraps
from flask import request, jsonify, abort, current_app
from flask_login import current_user
import logging
import re
from datetime import datetime, timedelta
from sqlalchemy import text

# Configurar logging de segurança
security_logger = logging.getLogger('security')

class SecurityManager:
    """Gerenciador de segurança centralizado"""
    
    @staticmethod
    def validate_user_access(user_id: int) -> bool:
        """Valida se o usuário atual pode acessar dados de outro usuário"""
        if not current_user.is_authenticated:
            return False
        
        # Super admin pode acessar tudo
        if current_user.is_super_admin:
            return True
        
        # Usuário só pode acessar seus próprios dados
        return current_user.id == user_id
    
    @staticmethod
    def validate_admin_access() -> bool:
        """Valida se o usuário atual é super admin"""
        return current_user.is_authenticated and current_user.is_super_admin
    
    @staticmethod
    def validate_xml_access(xml_file) -> bool:
        """Valida se o usuário pode acessar um XML específico"""
        if not current_user.is_authenticated:
            return False
        
        if current_user.is_super_admin:
            return True
        
        return xml_file.user_id == current_user.id
    
    @staticmethod
    def sanitize_input(data: str) -> str:
        """Sanitiza entrada de dados para prevenir XSS e SQL injection"""
        if not isinstance(data, str):
            return data
        
        # Remove caracteres perigosos
        data = re.sub(r'[<>"\';]', '', data)
        data = data.strip()
        
        return data
    
    @staticmethod
    def validate_invoice_key(key: str) -> bool:
        """Valida formato de chave de nota fiscal (44 dígitos)"""
        if not key or not isinstance(key, str):
            return False
        
        # Remove espaços e caracteres especiais
        clean_key = re.sub(r'[^0-9]', '', key)
        
        # Deve ter exatamente 44 dígitos
        return len(clean_key) == 44 and clean_key.isdigit()
    
    @staticmethod
    def log_security_event(event_type: str, user_id: int = None, details: str = None):
        """Registra eventos de segurança"""
        user_id = user_id or (current_user.id if current_user.is_authenticated else None)
        
        security_logger.warning(f"SECURITY_EVENT: {event_type} | User: {user_id} | IP: {request.remote_addr} | Details: {details}")

def require_authentication(f):
    """Decorator para exigir autenticação"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            SecurityManager.log_security_event("UNAUTHORIZED_ACCESS", details=f"Route: {request.endpoint}")
            abort(401)
        return f(*args, **kwargs)
    return decorated_function

def require_admin(f):
    """Decorator para exigir permissões de admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not SecurityManager.validate_admin_access():
            SecurityManager.log_security_event("ADMIN_ACCESS_DENIED", details=f"Route: {request.endpoint}")
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def require_user_access(f):
    """Decorator para validar acesso a dados de usuário específico"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = kwargs.get('user_id') or request.view_args.get('user_id')
        
        if user_id and not SecurityManager.validate_user_access(int(user_id)):
            SecurityManager.log_security_event("USER_DATA_ACCESS_DENIED", details=f"Attempted access to user {user_id}")
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function

def rate_limit_check(max_requests: int = 100, window_minutes: int = 60):
    """Decorator para controle de taxa de requisições"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Implementação simplificada - em produção usar Redis
            user_key = f"rate_limit_{current_user.id if current_user.is_authenticated else request.remote_addr}"
            
            # Por ora, apenas log - implementar controle real em produção
            SecurityManager.log_security_event("RATE_LIMIT_CHECK", details=f"Route: {request.endpoint}")
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

class DataIsolationManager:
    """Gerenciador de isolamento de dados por usuário"""
    
    @staticmethod
    def filter_user_xmls(query, user_id: int = None):
        """Filtra XMLs para mostrar apenas os do usuário atual"""
        user_id = user_id or current_user.id
        
        if current_user.is_super_admin and not user_id:
            return query
        
        return query.filter_by(user_id=user_id)
    
    @staticmethod
    def filter_user_usage(query, user_id: int = None):
        """Filtra registros de uso para o usuário atual"""
        user_id = user_id or current_user.id
        
        if current_user.is_super_admin and not user_id:
            return query
        
        return query.filter_by(user_id=user_id)
    
    @staticmethod
    def filter_user_charges(query, user_id: int = None):
        """Filtra cobranças para o usuário atual"""
        user_id = user_id or current_user.id
        
        if current_user.is_super_admin and not user_id:
            return query
        
        return query.filter_by(user_id=user_id)

class BillingSecurityManager:
    """Gerenciador de segurança para sistema de cobrança"""
    
    @staticmethod
    def validate_credit_operation(user, amount: float, operation_type: str) -> bool:
        """Valida operações de crédito para prevenir fraudes"""
        
        # Validar valores
        if amount <= 0 or amount > 10000:  # Limite máximo de R$ 10.000
            SecurityManager.log_security_event("INVALID_CREDIT_AMOUNT", user.id, f"{operation_type}: {amount}")
            return False
        
        # Validar frequência de operações
        recent_operations = user.get_recent_credit_operations(minutes=5)
        if len(recent_operations) > 10:  # Máximo 10 operações por 5 minutos
            SecurityManager.log_security_event("EXCESSIVE_CREDIT_OPERATIONS", user.id, f"Operations: {len(recent_operations)}")
            return False
        
        return True
    
    @staticmethod
    def validate_service_usage(user, service_type: str, quantity: int = 1) -> bool:
        """Valida uso de serviços para prevenir abuso"""
        
        # Verificar se usuário tem créditos suficientes
        if not user.has_sufficient_credits(service_type, quantity):
            SecurityManager.log_security_event("INSUFFICIENT_CREDITS", user.id, f"{service_type}: {quantity}")
            return False
        
        # Verificar limites de uso por período
        usage_limits = {
            'xml_download': 1000,  # 1000 XMLs por dia
            'label_generation': 500,  # 500 etiquetas por dia
            'danfe_generation': 1000  # 1000 DANFEs por dia
        }
        
        daily_usage = user.get_daily_usage(service_type)
        if daily_usage + quantity > usage_limits.get(service_type, 100):
            SecurityManager.log_security_event("USAGE_LIMIT_EXCEEDED", user.id, f"{service_type}: {daily_usage + quantity}")
            return False
        
        return True

def setup_security_headers(app):
    """Configura cabeçalhos de segurança para produção"""
    
    @app.after_request
    def add_security_headers(response):
        # Prevenir XSS
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # HTTPS Strict Transport Security
        if request.is_secure:
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Content Security Policy
        response.headers['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "img-src 'self' data: https:; "
            "font-src 'self' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "connect-src 'self';"
        )
        
        return response

def validate_production_config(app):
    """Valida configurações para ambiente de produção"""
    
    required_configs = [
        'SECRET_KEY',
        'DATABASE_URL', 
        'STRIPE_SECRET_KEY',
        'MAIL_USERNAME',
        'MAIL_PASSWORD'
    ]
    
    missing_configs = []
    for config in required_configs:
        if not app.config.get(config):
            missing_configs.append(config)
    
    if missing_configs:
        raise RuntimeError(f"Configurações obrigatórias ausentes: {', '.join(missing_configs)}")
    
    # Validar chave secreta
    if len(app.config.get('SECRET_KEY', '')) < 32:
        raise RuntimeError("SECRET_KEY deve ter pelo menos 32 caracteres")
    
    # Validar configuração de banco
    if 'sqlite' in app.config.get('DATABASE_URL', '').lower():
        raise RuntimeError("SQLite não é adequado para produção - use PostgreSQL")

class DatabaseSecurityManager:
    """Gerenciador de segurança do banco de dados"""
    
    @staticmethod
    def sanitize_sql_params(params: dict) -> dict:
        """Sanitiza parâmetros SQL para prevenir injection"""
        sanitized = {}
        
        for key, value in params.items():
            if isinstance(value, str):
                # Remove caracteres SQL perigosos
                value = re.sub(r'[;\'"\\]', '', value)
            
            sanitized[key] = value
        
        return sanitized
    
    @staticmethod
    def validate_database_operation(operation: str, table: str, user_id: int = None):
        """Valida operações de banco para auditoria"""
        
        # Log de operações sensíveis
        sensitive_operations = ['DELETE', 'UPDATE', 'INSERT']
        sensitive_tables = ['users', 'charges', 'usage_records']
        
        if operation.upper() in sensitive_operations and table.lower() in sensitive_tables:
            SecurityManager.log_security_event(
                "DATABASE_OPERATION", 
                user_id or (current_user.id if current_user.is_authenticated else None),
                f"{operation} on {table}"
            )