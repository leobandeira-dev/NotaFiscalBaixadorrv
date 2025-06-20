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

class ImportedXML(db.Model):
    """XMLs importados com sucesso"""
    __tablename__ = 'imported_xmls'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    invoice_key = db.Column(db.String(44), nullable=False)  # Chave de acesso da nota fiscal
    xml_content = db.Column(db.Text, nullable=False)  # Conteúdo XML completo
    file_path = db.Column(db.String(255))  # Caminho do arquivo salvo
    
    import_type = db.Column(db.String(20), nullable=False)  # 'API' ou 'SISTEMA'
    job_id = db.Column(db.String(100))  # ID do job relacionado
    
    # Dados básicos da nota fiscal
    cnpj_emitente = db.Column(db.String(14))
    nome_emitente = db.Column(db.String(255))
    numero_nf = db.Column(db.String(50))
    serie_nf = db.Column(db.String(10))
    data_emissao = db.Column(db.Date)
    valor_total = db.Column(db.Float)
    
    # Informações de transporte e volumes
    peso_bruto = db.Column(db.Float)
    quantidade_volumes = db.Column(db.Integer)
    
    # Dados do remetente (emitente)
    remetente_razao = db.Column(db.String(255))
    remetente_cidade = db.Column(db.String(100))
    remetente_uf = db.Column(db.String(2))
    remetente_endereco = db.Column(db.String(500))
    remetente_cep = db.Column(db.String(8))
    
    # Dados do destinatário
    destinatario_cnpj_cpf = db.Column(db.String(14))
    destinatario_razao = db.Column(db.String(255))
    destinatario_cidade = db.Column(db.String(100))
    destinatario_uf = db.Column(db.String(2))
    destinatario_endereco = db.Column(db.String(500))
    destinatario_cep = db.Column(db.String(8))
    
    # Controle de processamento
    danfe_generated = db.Column(db.Boolean, default=False)
    label_generated = db.Column(db.Boolean, default=False)
    
    # Timestamps
    imported_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'invoice_key': self.invoice_key,
            'import_type': self.import_type,
            'cnpj_emitente': self.cnpj_emitente,
            'nome_emitente': self.nome_emitente,
            'numero_nf': self.numero_nf,
            'serie_nf': self.serie_nf,
            'data_emissao': self.data_emissao.isoformat() if self.data_emissao else None,
            'valor_total': self.valor_total,
            'peso_bruto': self.peso_bruto,
            'quantidade_volumes': self.quantidade_volumes,
            'remetente_razao': self.remetente_razao,
            'remetente_cidade': self.remetente_cidade,
            'remetente_uf': self.remetente_uf,
            'remetente_endereco': self.remetente_endereco,
            'remetente_cep': self.remetente_cep,
            'destinatario_cnpj_cpf': self.destinatario_cnpj_cpf,
            'destinatario_razao': self.destinatario_razao,
            'destinatario_cidade': self.destinatario_cidade,
            'destinatario_uf': self.destinatario_uf,
            'destinatario_endereco': self.destinatario_endereco,
            'destinatario_cep': self.destinatario_cep,
            'danfe_generated': self.danfe_generated,
            'label_generated': self.label_generated,
            'imported_at': self.imported_at.isoformat()
        }

class StripeTransaction(db.Model):
    """Transações Stripe"""
    __tablename__ = 'stripe_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Dados Stripe
    stripe_payment_intent_id = db.Column(db.String(255), unique=True)
    stripe_session_id = db.Column(db.String(255), unique=True)
    
    # Transação
    amount_brl = db.Column(db.Float, nullable=False)  # Valor em reais
    credits_purchased = db.Column(db.Float, nullable=False)  # Créditos comprados
    package_id = db.Column(db.String(50))  # ID do pacote comprado
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed, refunded
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relacionamento
    user = db.relationship('User', backref='stripe_transactions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount_brl': self.amount_brl,
            'credits_purchased': self.credits_purchased,
            'package_id': self.package_id,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }

class CreditBalance(db.Model):
    """Histórico de saldos de créditos"""
    __tablename__ = 'credit_balances'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Transação de crédito
    transaction_type = db.Column(db.String(20), nullable=False)  # 'credit' (adicionar) ou 'debit' (usar)
    amount = db.Column(db.Float, nullable=False)  # Valor da transação
    balance_after = db.Column(db.Float, nullable=False)  # Saldo após transação
    
    # Detalhes
    description = db.Column(db.String(255))
    service_type = db.Column(db.String(50))  # xml_download, labels_module, etc
    reference_id = db.Column(db.String(255))  # ID de referência (job_id, transaction_id, etc)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamento
    user = db.relationship('User', backref='credit_history')
    
    def to_dict(self):
        return {
            'id': self.id,
            'transaction_type': self.transaction_type,
            'amount': self.amount,
            'balance_after': self.balance_after,
            'description': self.description,
            'service_type': self.service_type,
            'created_at': self.created_at.isoformat()
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


class XMLFile(db.Model):
    """Modelo para armazenar arquivos XML baixados"""
    __tablename__ = 'xml_files'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    invoice_key = db.Column(db.String(44), nullable=False)  # Chave de 44 dígitos
    file_path = db.Column(db.String(500), nullable=False)
    xml_content = db.Column(db.Text, nullable=True)  # Conteúdo XML opcional
    import_type = db.Column(db.String(50), default='SISTEMA')  # SISTEMA, MANUAL, API
    job_id = db.Column(db.String(50), nullable=True)  # ID do job de download
    
    # Timestamps
    imported_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamento com usuário
    user = db.relationship('User', backref='xml_files')
    
    def __repr__(self):
        return f'<XMLFile {self.filename}>'