"""
Modelos de dados para o sistema de autenticação e cobrança
"""

import os
import secrets
from datetime import datetime, timedelta
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

class User(UserMixin, db.Model):
    """Modelo de usuário do sistema"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    
    # Dados de cobrança
    current_balance = db.Column(db.Float, default=0.0)  # Saldo atual em R$
    trial_expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))
    active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)
    
    # Chaves API
    api_key = db.Column(db.String(64), unique=True)
    api_secret = db.Column(db.String(64), unique=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    usage_records = db.relationship('UsageRecord', backref='user', lazy=True, cascade='all, delete-orphan')
    charges = db.relationship('Charge', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if not self.api_key:
            self.api_key = self.generate_api_key()
        if not self.api_secret:
            self.api_secret = self.generate_api_secret()
    
    def set_password(self, password):
        """Define a senha do usuário"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verifica a senha do usuário"""
        return check_password_hash(self.password_hash, password)
    
    def generate_api_key(self):
        """Gera uma nova chave API"""
        return f"ak_{secrets.token_urlsafe(32)}"
    
    def generate_api_secret(self):
        """Gera um novo secret API"""
        return f"sk_{secrets.token_urlsafe(32)}"
    
    def regenerate_api_credentials(self):
        """Regenera as credenciais API"""
        self.api_key = self.generate_api_key()
        self.api_secret = self.generate_api_secret()
        db.session.commit()
    
    def is_trial_active(self):
        """Verifica se o trial está ativo"""
        return datetime.utcnow() < self.trial_expires_at
    
    def can_use_service(self, cost=0):
        """Verifica se o usuário pode usar um serviço"""
        if self.is_trial_active():
            return True
        return self.current_balance >= cost
    
    def deduct_balance(self, amount, description=""):
        """Deduz do saldo do usuário"""
        if self.current_balance >= amount:
            self.current_balance -= amount
            db.session.commit()
            return True
        return False
    
    def add_balance(self, amount):
        """Adiciona ao saldo do usuário"""
        self.current_balance += amount
        db.session.commit()
    
    def to_dict(self):
        """Converte o usuário para dicionário"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'current_balance': self.current_balance,
            'is_trial_active': self.is_trial_active(),
            'trial_expires_at': self.trial_expires_at.isoformat() if self.trial_expires_at else None,
            'is_active': self.active,
            'is_admin': self.is_admin,
            'api_key': self.api_key,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ServiceModule(db.Model):
    """Módulos de serviço disponíveis"""
    __tablename__ = 'service_modules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    cost_per_use = db.Column(db.Float, nullable=False, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    usage_records = db.relationship('UsageRecord', backref='module', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'cost_per_use': self.cost_per_use,
            'is_active': self.is_active
        }

class UsageRecord(db.Model):
    """Registro de uso de serviços"""
    __tablename__ = 'usage_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('service_modules.id'), nullable=False)
    
    quantity = db.Column(db.Integer, default=1)  # Quantidade usada
    cost = db.Column(db.Float, nullable=False)   # Custo total
    description = db.Column(db.String(255))      # Descrição da operação
    
    # Metadados específicos
    invoice_keys = db.Column(db.Text)  # JSON com chaves processadas
    job_id = db.Column(db.String(100))  # ID do job relacionado
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'module_name': self.service_module.name if self.service_module else None,
            'quantity': self.quantity,
            'cost': self.cost,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Charge(db.Model):
    """Cobrança via Asaas"""
    __tablename__ = 'charges'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Dados da cobrança
    asaas_charge_id = db.Column(db.String(100), unique=True)  # ID retornado pelo Asaas
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(255))
    due_date = db.Column(db.Date, nullable=False)
    
    # Status da cobrança
    status = db.Column(db.String(50), default='PENDING')  # PENDING, RECEIVED, OVERDUE, etc
    payment_url = db.Column(db.String(500))  # URL de pagamento
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'asaas_charge_id': self.asaas_charge_id,
            'amount': self.amount,
            'description': self.description,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'status': self.status,
            'payment_url': self.payment_url,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'paid_at': self.paid_at.isoformat() if self.paid_at else None
        }

class SystemSettings(db.Model):
    """Configurações do sistema"""
    __tablename__ = 'system_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.String(500))
    description = db.Column(db.Text)
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    @staticmethod
    def get_setting(key, default=None):
        """Obtém uma configuração do sistema"""
        setting = SystemSettings.query.filter_by(key=key).first()
        return setting.value if setting else default
    
    @staticmethod
    def set_setting(key, value, description=None):
        """Define uma configuração do sistema"""
        setting = SystemSettings.query.filter_by(key=key).first()
        if setting:
            setting.value = value
            if description:
                setting.description = description
        else:
            setting = SystemSettings(key=key, value=value, description=description)
            db.session.add(setting)
        db.session.commit()
        return setting

def init_default_data():
    """Inicializa dados padrão do sistema"""
    
    # Módulos de serviço padrão
    modules = [
        {
            'name': 'xml_download',
            'description': 'Download de XML de notas fiscais',
            'cost_per_use': 0.10
        },
        {
            'name': 'danfe_generation',
            'description': 'Geração de DANFE em PDF',
            'cost_per_use': 0.00
        },
        {
            'name': 'api_usage',
            'description': 'Uso da API para downloads',
            'cost_per_use': 0.10
        },
        {
            'name': 'label_generation',
            'description': 'Módulo de etiquetas',
            'cost_per_use': 49.90
        }
    ]
    
    for module_data in modules:
        existing = ServiceModule.query.filter_by(name=module_data['name']).first()
        if not existing:
            module = ServiceModule(**module_data)
            db.session.add(module)
    
    # Configurações padrão do sistema
    default_settings = [
        ('min_charge_amount', '19.90', 'Valor mínimo de cobrança em R$'),
        ('trial_days', '7', 'Dias de trial gratuito'),
        ('asaas_api_key', '$aact_prod_000MzkwODA2MWY2OGM3MWRlMDU2NWM3MzJlNzZmNGZhZGY6OjcyZTMyMGYyLTdkZDgtNGI4Yi1iYWQxLWI4ZjkyNmEzODg4Mzo6JGFhY2hfZjg3YTIyMjEtNDMzNi00ZjFlLTlhNjgtODllNjA3MjZmMmNh', 'Chave API do Asaas'),
        ('company_name', 'XML Downloader', 'Nome da empresa para cobranças')
    ]
    
    for key, value, description in default_settings:
        existing = SystemSettings.query.filter_by(key=key).first()
        if not existing:
            setting = SystemSettings(key=key, value=value, description=description)
            db.session.add(setting)
    
    db.session.commit()