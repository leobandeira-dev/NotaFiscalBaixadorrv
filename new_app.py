"""
Sistema completo de XML Downloader com autenticação e cobrança
"""

import os
import json
import uuid
import logging
import secrets
import pytz
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from threading import Thread, Lock
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory, send_file, make_response
from io import BytesIO
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer
# Import Google OAuth components
import requests
from oauthlib.oauth2 import WebApplicationClient
from models import db, User, ServiceModule, UsageRecord, Charge, SystemSettings, StripeTransaction, CreditBalance, XMLFile, UserActivity, init_default_data
from package_models import (
    StripeProduct, PackageFeature, UserSubscription, FeatureUsage,
    init_stripe_products, get_user_active_subscriptions, 
    user_has_feature_access, consume_feature_credit
)
from access_control import (
    require_feature, require_xml_credits, require_labels_subscription,
    require_admin, get_user_package_status, inject_package_status
)
from asaas_integration import AsaasAPI, create_minimum_charge, process_webhook_payment
from stripe_integration import StripePaymentManager, CreditManager, PricingManager, process_stripe_webhook
from stripe_pricing_system import XMLPricingTiers, get_user_xml_credits, consume_xml_credit, get_pricing_recommendations, create_xml_credit_subscription
from transport_label_generator import TransportLabelGenerator, generate_label_from_database_xml
from transport_label_generator_v2 import CustomTransportLabelGenerator, generate_custom_label_from_database_xml
from improved_transport_label import ImprovedTransportLabelGenerator
from transul_exact_layout_generator import generate_transul_exact_label_from_xml
from xml_processor import extract_xml_data
from email_encryption import encrypt_email_password, decrypt_email_password

def log_user_activity(user_id, activity_type, description, details=None):
    """Registra uma atividade do usuário no sistema"""
    try:
        activity = UserActivity(
            user_id=user_id,
            activity_type=activity_type,
            description=description,
            details=json.dumps(details) if details else None
        )
        db.session.add(activity)
        db.session.commit()
        logger.info(f"Atividade registrada para usuário {user_id}: {activity_type} - {description}")
    except Exception as e:
        logger.error(f"Erro ao registrar atividade: {e}")
        db.session.rollback()

def get_user_recent_activities(user_id, limit=5):
    """Obter atividades recentes do usuário"""
    try:
        activities = UserActivity.query.filter_by(
            user_id=user_id
        ).order_by(UserActivity.created_at.desc()).limit(limit).all()
        
        return [{
            'type': activity.activity_type,
            'description': activity.description,
            'details': json.loads(activity.details) if activity.details else {},
            'created_at': activity.created_at,
            'time_ago': get_time_ago(activity.created_at)
        } for activity in activities]
    except Exception as e:
        logger.error(f"Erro ao buscar atividades: {e}")
        return []

def get_time_ago(dt):
    """Calcular tempo decorrido em português"""
    now = datetime.utcnow()
    diff = now - dt
    
    if diff.days > 0:
        return f"{diff.days} dia{'s' if diff.days > 1 else ''} atrás"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hora{'s' if hours > 1 else ''} atrás"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minuto{'s' if minutes > 1 else ''} atrás"
    else:
        return "Agora mesmo"

def generate_improved_label_with_guaranteed_borders(xml_id, user, paper_config, layout_style='layout1'):
    """Função de integração que usa o novo sistema com bordas garantidas"""
    
    # Buscar XML
    xml_file = XMLFile.query.filter_by(id=xml_id, user_id=user.id).first()
    if not xml_file:
        return None
    
    # Ler conteúdo do XML
    try:
        with open(xml_file.file_path, 'r', encoding='utf-8') as f:
            xml_content = f.read()
    except Exception as e:
        logger.error(f"Erro ao ler XML {xml_file.file_path}: {e}")
        return None
    
    # Configurações da empresa
    company_name = user.company_name or "SUA EMPRESA"
    company_subtitle = user.company_subtitle or "TRANSPORTE"
    area_code = user.default_area_code or "01"
    company_logo_path = user.company_logo_path
    
    # Extrair dimensões do papel
    paper_size = paper_config.get('size', '10x15cm')
    if paper_size == 'A4':
        width_mm, height_mm = 210, 297
    elif paper_size == 'A5':
        width_mm, height_mm = 148, 210
    elif paper_size == '10x15cm':
        width_mm, height_mm = 100, 150
    elif paper_size == '7x10cm':
        width_mm, height_mm = 70, 100
    elif paper_size == '5x8cm':
        width_mm, height_mm = 50, 80
    else:
        width_mm, height_mm = 100, 150
    
    # Criar gerador melhorado
    generator = ImprovedTransportLabelGenerator(
        company_name=company_name,
        company_subtitle=company_subtitle,
        paper_width_mm=width_mm,
        paper_height_mm=height_mm,
        layout_style=layout_style,
        company_logo_path=company_logo_path
    )
    
    # Gerar etiquetas com volume info
    labels = []
    total_volumes = paper_config.get('total_volumes', 1)
    volume_weights = paper_config.get('volume_weights', [0.0] * total_volumes)
    
    for i in range(total_volumes):
        volume_number = i + 1
        volume_info = f"{volume_number}/{total_volumes}"
        
        # Gerar pedido dinâmico baseado no XML ID
        pedido_number = f"PED{xml_id}{volume_number:03d}"
        
        try:
            pdf_buffer = generator.generate_transport_label_with_volume_info(
                xml_content=xml_content,
                pedido_number=pedido_number,
                area_code=area_code,
                company_logo_path=user.company_logo_path,
                volume_info=volume_info,
                current_volume=volume_number,
                total_volumes=total_volumes
            )
            
            labels.append({
                'volume': volume_number,
                'pdf_data': pdf_buffer.getvalue(),
                'filename': f"etiqueta_volume_{volume_number}.pdf",
                'size': len(pdf_buffer.getvalue())
            })
            
        except Exception as e:
            logger.error(f"Erro ao gerar etiqueta volume {volume_number}: {e}")
            continue
    
    return labels

def generate_improved_labels_with_guaranteed_borders(xml_record, volumes_config, company_name, company_logo_path, paper_width_mm, paper_height_mm, area_code, company_subtitle, layout_style):
    """Gera etiquetas com sistema melhorado - bordas garantidas e espaçamento de 4mm"""
    
    try:
        labels = []
        
        # Obter conteúdo XML
        xml_content = getattr(xml_record, 'xml_content', None) or getattr(xml_record, 'content', '')
        
        if not xml_content:
            raise ValueError("XML content not found in record")
        
        total_volumes = len(volumes_config)
        logger.info(f"Geração otimizada: {total_volumes} volumes com layout Transul Exato")
        
        # Gerar etiquetas individuais usando TransulExactLayoutGenerator
        for volume_config in volumes_config:
            volume_idx = volumes_config.index(volume_config) + 1
            peso = volume_config.get('peso', 0)
            pedido = volume_config.get('pedido', f'PED{volume_idx}')
            
            try:
                volume_info = f"{volume_idx}/{total_volumes}"
                
                # Usar o gerador corrigido com espaçamento de 4mm
                label_buffer = generate_transul_exact_label_from_xml(
                    xml_content=xml_content,
                    pedido_number=pedido,
                    area_code=area_code,
                    company_logo_path=company_logo_path,
                    volume_info=volume_info,
                    paper_width_mm=paper_width_mm,
                    paper_height_mm=paper_height_mm,
                    company_name=company_name,
                    company_subtitle=company_subtitle
                )
                
                labels.append({
                    'volume': volume_idx,
                    'peso': peso,
                    'pedido': pedido,
                    'pdf_buffer': label_buffer,
                    'filename': f'etiqueta_volume_{volume_idx}_{pedido}.pdf'
                })
                
                logger.info(f"Etiqueta otimizada gerada: Volume {volume_idx}/{total_volumes} - {len(label_buffer.getvalue())} bytes")
                
            except Exception as e:
                logger.error(f"Erro ao gerar etiqueta otimizada volume {volume_idx}: {e}")
                continue
        
        logger.info(f"Geradas {len(labels)} etiquetas otimizadas com layout Transul Exato")
        return labels
        
    except Exception as e:
        logger.error(f"Erro no sistema de etiquetas otimizadas: {str(e)}")
        raise

from download_service import DownloadService
from security import (
    SecurityManager, DataIsolationManager, BillingSecurityManager,
    require_authentication, require_admin, require_user_access,
    rate_limit_check, setup_security_headers, validate_production_config
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure for custom domain
app.config['SERVER_NAME'] = None  # Allow any domain
app.config['PREFERRED_URL_SCHEME'] = 'https'

# Add middleware to handle custom domain
@app.before_request
def handle_custom_domain():
    """Handle requests from custom domain"""
    host = request.host
    if host in ['crossxml.com.br', 'www.crossxml.com.br']:
        # Domain is correctly configured
        pass

# Database configuration
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

# Email configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', 'noreply@xmldownloader.com')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')
app.config['MAIL_DEFAULT_SENDER'] = 'XMLDownloader <noreply@xmldownloader.com>'

# Initialize database
db.init_app(app)

# Initialize Flask-Mail
mail = Mail(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Google OAuth Configuration
GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_OAUTH_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_OAUTH_CLIENT_SECRET")
GOOGLE_DISCOVERY_URL = "https://accounts.google.com/.well-known/openid-configuration"

client = WebApplicationClient(GOOGLE_CLIENT_ID) if GOOGLE_CLIENT_ID else None

def get_google_redirect_url():
    """Get the appropriate redirect URL based on current domain"""
    if 'crossxml.com.br' in request.host:
        return 'https://crossxml.com.br/google_login/callback'
    elif os.environ.get("REPLIT_DEV_DOMAIN"):
        return f'https://{os.environ["REPLIT_DEV_DOMAIN"]}/google_login/callback'
    else:
        return 'http://localhost:5000/google_login/callback'

# Display Google OAuth setup instructions
if GOOGLE_CLIENT_ID:
    replit_redirect = f'https://{os.environ.get("REPLIT_DEV_DOMAIN", "your-repl")}/google_login/callback'
    custom_redirect = 'https://crossxml.com.br/google_login/callback'
    
    print(f"""Google OAuth configured. Redirect URIs:
    - {replit_redirect} (for Replit domain)
    - {custom_redirect} (for custom domain)
    """)
else:
    print("Google OAuth not configured - GOOGLE_OAUTH_CLIENT_ID missing")

# Google OAuth setup (routes will be defined after app initialization)

# Setup security headers
setup_security_headers(app)
login_manager.login_message = 'Faça login para acessar esta página.'
login_manager.login_message_category = 'info'

# Initialize password reset serializer
serializer = URLSafeTimedSerializer(app.secret_key)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Job management system
download_jobs = {}
jobs_lock = Lock()

class DownloadJob:
    def __init__(self, job_id, invoice_keys, user_id):
        self.job_id = job_id
        self.invoice_keys = invoice_keys
        self.user_id = user_id
        self.total_keys = len(invoice_keys)
        self.processed = 0
        self.successful = 0
        self.failed = 0
        self.status = "starting"  # starting, running, completed, failed
        self.downloaded_files = []
        self.files = []  # Add files attribute for compatibility
        self.errors = []
        self.start_time = datetime.now()
        self.end_time = None
        self.callback_url = None
        self.download_type = 'xml'
    
    @property
    def progress_percentage(self):
        """Calculate progress percentage"""
        if self.total_keys == 0:
            return 0
        return round((self.processed / self.total_keys) * 100, 1)

    def to_dict(self):
        return {
            'job_id': self.job_id,
            'total_keys': self.total_keys,
            'processed': self.processed,
            'successful': self.successful,
            'failed': self.failed,
            'status': self.status,
            'progress_percentage': (self.processed / self.total_keys * 100) if self.total_keys > 0 else 0,
            'downloaded_files': self.downloaded_files,
            'errors': self.errors,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None
        }

def process_download_job(job_id, user_id):
    """Process download job in background"""
    try:
        from automation_fixed import InvoiceDownloader
        
        with jobs_lock:
            job = download_jobs.get(job_id)
        
        if not job:
            logger.error(f"Job {job_id} not found for processing")
            return
        
        job.status = "running"
        downloader = InvoiceDownloader()
        
        for i, invoice_key in enumerate(job.invoice_keys):
            try:
                logger.info(f"[Job {job_id}] Processing key {i+1}/{job.total_keys}: {invoice_key}")
                
                result = downloader.download_invoice_xml(
                    invoice_key=invoice_key,
                    job_id=job_id,
                    download_type=job.download_type,
                    user_id=user_id
                )
                
                job.processed += 1
                
                if result.get('success') == True:
                    job.successful += 1
                    if result.get('file_path'):
                        job.downloaded_files.append(result['file_path'])
                        job.files.append(os.path.basename(result['file_path']))
                else:
                    job.failed += 1
                    job.errors.append({
                        'invoice_key': invoice_key,
                        'error': result.get('error', result.get('message', 'Unknown error'))
                    })
                    
            except Exception as e:
                logger.error(f"[Job {job_id}] Error processing {invoice_key}: {str(e)}")
                job.failed += 1
                job.processed += 1
                job.errors.append({
                    'invoice_key': invoice_key,
                    'error': str(e)
                })
        
        # Mark job as completed
        job.status = "completed" if job.successful > 0 else "failed"
        job.end_time = datetime.now()
        
        downloader.cleanup()
        logger.info(f"[Job {job_id}] Completed: {job.successful} successful, {job.failed} failed")
        
    except Exception as e:
        logger.error(f"[Job {job_id}] Critical error: {str(e)}")
        if job_id in download_jobs:
            download_jobs[job_id].status = "failed"

# Initialize Flask app with proper configuration
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key_12345")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database configuration  
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

# Initialize Flask extensions
db.init_app(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Create tables and initialize data
with app.app_context():
    db.create_all()
    init_default_data()
    init_stripe_products()  # Inicializar produtos Stripe
    
    # Create admin user if not exists
    admin = User.query.filter_by(email='admin@xmldownloader.com').first()
    if not admin:
        admin = User(
            email='admin@xmldownloader.com',
            name='Administrador',
            is_admin=True,
            current_balance=1000.0  # Admin starts with balance
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        logger.info("Admin user created: admin@xmldownloader.com / admin123")

# Context processors
@app.context_processor
def inject_xml_credits():
    """Injetar função de créditos XML nos templates"""
    if current_user.is_authenticated:
        try:
            from stripe_pricing_system import get_user_xml_credits
            return {'get_user_xml_credits': get_user_xml_credits}
        except:
            return {'get_user_xml_credits': lambda x: 0}
    return {'get_user_xml_credits': lambda x: 0}

# Routes

@app.route('/')
def index():
    """Home page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    # Serve static HTML landing page
    from flask import send_from_directory
    return send_from_directory('static', 'index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not all([name, email, password]):
            flash('Todos os campos são obrigatórios.', 'error')
            return render_template('register.html')
        
        # Check if user exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Este email já está cadastrado.', 'error')
            return render_template('register.html')
        
        # Create new user
        user = User(name=name, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Conta criada com sucesso! Você tem 7 dias de teste grátis.', 'success')
        login_user(user)
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Email ou senha incorretos.', 'error')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('Logout realizado com sucesso.', 'success')
    return redirect(url_for('index'))

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Password reset request"""
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Generate reset token
            token = serializer.dumps(email, salt='password-reset')
            
            # Create reset URL
            reset_url = url_for('reset_password', token=token, _external=True)
            
            # Send email (simplified - in production, use proper email template)
            try:
                msg = Message(
                    'Redefinição de Senha - XMLDownloader',
                    recipients=[email],
                    body=f'''
Olá {user.name},

Você solicitou a redefinição de sua senha. Clique no link abaixo para definir uma nova senha:

{reset_url}

Este link expira em 1 hora.

Se você não solicitou esta redefinição, ignore este email.

Atenciosamente,
Equipe XMLDownloader
'''
                )
                mail.send(msg)
                flash('Instruções de redefinição enviadas para seu email.', 'success')
            except Exception as e:
                logger.error(f"Erro ao enviar email: {e}")
                flash('Erro ao enviar email. Tente novamente mais tarde.', 'error')
        else:
            # Don't reveal if email exists
            flash('Se o email existir, você receberá as instruções.', 'info')
        
        return redirect(url_for('login'))
    
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """Password reset with token"""
    try:
        email = serializer.loads(token, salt='password-reset', max_age=3600)
    except:
        flash('Link de redefinição inválido ou expirado.', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('As senhas não coincidem.', 'error')
            return render_template('reset_password.html', token=token)
        
        if len(password) < 6:
            flash('A senha deve ter pelo menos 6 caracteres.', 'error')
            return render_template('reset_password.html', token=token)
        
        user = User.query.filter_by(email=email).first()
        if user:
            user.set_password(password)
            db.session.commit()
            flash('Senha redefinida com sucesso!', 'success')
            return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)



@app.route('/dashboard')
@login_required
@rate_limit_check(max_requests=50, window_minutes=10)
def dashboard():
    """User dashboard with data isolation"""
    from download_service import DownloadService
    
    # Registrar atividade de acesso ao dashboard
    log_user_activity(
        user_id=current_user.id,
        activity_type='dashboard_accessed',
        description="Acesso ao painel principal",
        details={'ip_address': request.environ.get('REMOTE_ADDR', 'unknown')}
    )
    
    # Get user XML statistics with isolation
    user_xmls_query = XMLFile.query.filter_by(user_id=current_user.id)
    user_xmls_query = DataIsolationManager.filter_user_xmls(user_xmls_query, current_user.id)
    user_xmls = user_xmls_query.all()
    xml_count = len(user_xmls)
    
    # Get usage statistics with data isolation
    try:
        usage_query = UsageRecord.query.filter_by(user_id=current_user.id)
        usage_query = DataIsolationManager.filter_user_usage(usage_query, current_user.id)
        total_usage = usage_query.count()
    except Exception as e:
        logger.error(f"Error counting usage records: {e}")
        SecurityManager.log_security_event("DATA_ACCESS_ERROR", current_user.id, f"Usage count error: {e}")
        db.session.rollback()
        total_usage = 0
    
    try:
        monthly_usage_query = UsageRecord.query.filter(
            UsageRecord.user_id == current_user.id,
            UsageRecord.created_at >= datetime.now().replace(day=1)
        )
        monthly_usage_query = DataIsolationManager.filter_user_usage(monthly_usage_query, current_user.id)
        this_month_usage = monthly_usage_query.count()
    except Exception as e:
        logger.error(f"Error counting monthly usage: {e}")
        SecurityManager.log_security_event("DATA_ACCESS_ERROR", current_user.id, f"Monthly usage error: {e}")
        db.session.rollback()
        this_month_usage = 0
    
    # Get recent activities using new UserActivity system
    recent_activities = get_user_recent_activities(current_user.id, limit=5)
    
    # Get pending charges
    pending_charges = Charge.query.filter_by(
        user_id=current_user.id,
        status='PENDING'
    ).all()
    
    # Get user XML credit balance using simplified system
    from simple_credit_system import get_user_xml_balance, get_user_stats, get_trial_status
    
    xml_balance = get_user_xml_balance(current_user.id)
    user_stats = get_user_stats(current_user.id)
    trial_status = get_trial_status(current_user.id)
    
    return render_template('dashboard.html', 
                         xml_count=xml_count,
                         xml_balance=xml_balance,
                         danfe_count=xml_count,  # DANFE is free for each XML
                         total_usage=total_usage,
                         this_month_usage=this_month_usage,
                         recent_activities=recent_activities,
                         pending_charges=pending_charges,
                         user_stats=user_stats,
                         trial_status=trial_status)

@app.route('/xml-download')
@login_required
def xml_download():
    """XML download page with current balance display"""
    # Obter saldo atual usando sistema simplificado
    from simple_credit_system import get_user_xml_balance
    xml_balance = get_user_xml_balance(current_user.id)
    
    return render_template('xml_download.html', xml_balance=xml_balance)

@app.route('/submit_keys', methods=['POST'])
@login_required
def submit_keys():
    """Process invoice keys submission"""
    try:
        keys_text = request.form.get('invoice_keys', '').strip()
        
        if not keys_text:
            flash('Por favor, insira pelo menos uma chave de nota fiscal.', 'error')
            return redirect(url_for('xml_download'))
        
        # Parse invoice keys
        invoice_keys = [key.strip() for key in keys_text.split('\n') if key.strip()]
        
        if not invoice_keys:
            flash('Nenhuma chave válida encontrada.', 'error')
            return redirect(url_for('xml_download'))
        
        # Validate invoice keys format (44 digits)
        valid_keys = []
        for key in invoice_keys:
            clean_key = ''.join(filter(str.isdigit, key))
            if len(clean_key) == 44:
                valid_keys.append(clean_key)
        
        if not valid_keys:
            flash('Nenhuma chave válida encontrada. Chaves devem ter 44 dígitos.', 'error')
            return redirect(url_for('xml_download'))
        
        # Check if user has sufficient XML credits using simplified system
        from simple_credit_system import get_user_xml_balance
        available_credits = get_user_xml_balance(current_user.id)
        
        if available_credits < len(valid_keys):
            flash(f'Créditos XML insuficientes. Você possui {available_credits} créditos, mas precisa de {len(valid_keys)} para processar estas chaves.', 'warning')
            return redirect(url_for('comprar_creditos_xml'))
        
        # Create download job
        job_id = str(uuid.uuid4())
        job = DownloadJob(job_id, valid_keys, current_user.id)
        
        with jobs_lock:
            download_jobs[job_id] = job
        
        # Note: XML credits will be deducted per successful download in automation_fixed.py
        
        # Record usage
        xml_module = ServiceModule.query.filter_by(name='xml_download').first()
        if xml_module:
            usage = UsageRecord(
                user_id=current_user.id,
                module_id=xml_module.id,
                quantity=len(valid_keys),
                cost=0.0,  # Cost tracking moved to credit system
                description=f"Download de {len(valid_keys)} XMLs",
                invoice_keys=json.dumps(valid_keys),
                job_id=job_id
            )
            db.session.add(usage)
            db.session.commit()
        
        # Start download process in background
        thread = Thread(target=process_download_job, args=(job_id, current_user.id))
        thread.daemon = True
        thread.start()
        
        flash(f'Processo de download iniciado para {len(valid_keys)} chave(s).', 'success')
        return redirect(url_for('download_status', job_id=job_id))
        
    except Exception as e:
        logger.error(f"Error in submit_keys: {str(e)}")
        flash('Erro interno do servidor. Tente novamente.', 'error')
        return redirect(url_for('xml_download'))

@app.route('/download/<job_id>')
@login_required
def download_status(job_id):
    """Display download progress and options"""
    with jobs_lock:
        job = download_jobs.get(job_id)
    
    if not job or job.user_id != current_user.id:
        flash('Job de download não encontrado.', 'error')
        return redirect(url_for('xml_download'))
    
    return render_template('download_status.html', job=job)

@app.route('/generate_danfe/<job_id>')
@login_required
def generate_danfe(job_id):
    """Generate DANFE for downloaded XMLs"""
    with jobs_lock:
        job = download_jobs.get(job_id)
    
    if not job or job.user_id != current_user.id:
        flash('Job não encontrado.', 'error')
        return redirect(url_for('xml_download'))
    
    if job.status != 'completed':
        flash('Aguarde o download dos XMLs terminar.', 'warning')
        return redirect(url_for('download_status', job_id=job_id))
    
    # DANFE generation is now FREE
    danfe_cost = 0.0
    
    # Record usage (free service)
    danfe_module = ServiceModule.query.filter_by(name='danfe_generation').first()
    if danfe_module:
        usage = UsageRecord(
            user_id=current_user.id,
            module_id=danfe_module.id,
            quantity=job.successful,
            cost=0.0,
            description=f"Geração GRATUITA de {job.successful} DANFEs",
            job_id=job_id
        )
        db.session.add(usage)
        db.session.commit()
    
    # Start DANFE generation in background
    thread = Thread(target=process_danfe_generation, args=(job_id,))
    thread.daemon = True
    thread.start()
    
    flash('Geração de DANFE iniciada.', 'success')
    return redirect(url_for('download_status', job_id=job_id))

@app.route('/add_balance')
@login_required
def add_balance():
    """Add balance page"""
    min_amount = float(SystemSettings.get_setting('min_charge_amount', '19.90'))
    pending_charges = Charge.query.filter_by(
        user_id=current_user.id,
        status='PENDING'
    ).all()
    
    return render_template('add_balance.html', 
                         min_amount=min_amount,
                         pending_charges=pending_charges)

@app.route('/create_charge', methods=['POST'])
@login_required
def create_charge():
    """Create a new charge"""
    try:
        amount = float(request.form.get('amount', 0))
        min_amount = float(SystemSettings.get_setting('min_charge_amount', '19.90'))
        
        if amount < min_amount:
            flash(f'Valor mínimo de recarga: R$ {min_amount:.2f}', 'error')
            return redirect(url_for('add_balance'))
        
        result = create_minimum_charge(current_user, amount)
        
        if result['success']:
            flash('Cobrança criada com sucesso! Use o link de pagamento abaixo.', 'success')
        else:
            flash(f'Erro ao criar cobrança: {result["error"]}', 'error')
        
        return redirect(url_for('add_balance'))
        
    except Exception as e:
        logger.error(f"Error creating charge: {str(e)}")
        flash('Erro interno. Tente novamente.', 'error')
        return redirect(url_for('add_balance'))

@app.route('/api_credentials')
@login_required
def api_credentials():
    """API credentials page"""
    return render_template('api_credentials.html')

@app.route('/download-demo')
@login_required
def download_demo():
    """Demonstração da interface de download melhorada"""
    return render_template('download_demo.html')



@app.route('/regenerate_api', methods=['POST'])
@login_required
def regenerate_api():
    """Regenerate API credentials"""
    current_user.regenerate_api_credentials()
    flash('Credenciais API regeneradas com sucesso.', 'success')
    return redirect(url_for('api_credentials'))

# Admin routes
@app.route('/admin')
@login_required
def admin_dashboard():
    """Admin dashboard"""
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get statistics com dados reais
    total_users = User.query.count()
    active_users = User.query.filter_by(active=True).count()
    total_usage = UsageRecord.query.count()
    
    # Receita real do Stripe - usar StripeTransaction ao invés de UsageRecord
    from models import StripeTransaction
    total_revenue = db.session.query(db.func.sum(StripeTransaction.amount_brl)).filter(
        StripeTransaction.status == 'completed'
    ).scalar() or 0
    
    # Recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    # Recent usage
    recent_usage = UsageRecord.query.order_by(UsageRecord.created_at.desc()).limit(10).all()
    
    # Calcular estatísticas mensais
    from datetime import datetime, timedelta
    current_month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    monthly_new_users = User.query.filter(User.created_at >= current_month_start).count()
    monthly_xmls = XMLFile.query.filter(XMLFile.created_at >= current_month_start).count()
    monthly_revenue = db.session.query(db.func.sum(StripeTransaction.amount_brl)).filter(
        StripeTransaction.created_at >= current_month_start,
        StripeTransaction.status == 'completed'
    ).scalar() or 0
    monthly_labels = XMLFile.query.filter(
        XMLFile.created_at >= current_month_start,
        XMLFile.label_generated == True
    ).count()
    
    # Total de XMLs processados (dados reais)
    total_xmls = XMLFile.query.count()
    
    # Breakdown de XMLs por tipo para demonstrar dados corretos
    xml_breakdown = db.session.query(
        XMLFile.import_type,
        db.func.count(XMLFile.id).label('count')
    ).group_by(XMLFile.import_type).all()
    
    xml_stats = {row.import_type: row.count for row in xml_breakdown}
    
    # Atividades recentes do sistema com dados do usuário
    recent_activities = UserActivity.query.join(User).order_by(UserActivity.created_at.desc()).limit(10).all()
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         total_usage=total_usage,
                         total_revenue=total_revenue,
                         total_xmls=total_xmls,
                         recent_users=recent_users,
                         recent_usage=recent_usage,
                         recent_activities=recent_activities,
                         monthly_new_users=monthly_new_users,
                         monthly_xmls=monthly_xmls,
                         monthly_revenue=monthly_revenue,
                         monthly_labels=monthly_labels,
                         xml_stats=xml_stats)

@app.route('/admin/users')
def admin_users():
    """Admin users management sem autenticação para demonstração"""
    from models import User, CreditBalance, Charge, XMLFile
    from credit_system_fixed import get_user_xml_balance
    
    # Buscar todos os usuários
    users = User.query.order_by(User.created_at.desc()).all()
    
    # Enriquecer dados dos usuários com informações reais
    users_with_data = []
    for user in users:
        try:
            # Calcular saldo real de créditos XML
            xml_balance = get_user_xml_balance(user.id)
            
            # Contar XMLs baixados pelo usuário
            total_xmls = XMLFile.query.filter_by(user_id=user.id).count()
            
            # Calcular valor total gasto (cobranças recebidas)
            total_spent = db.session.query(db.func.sum(Charge.amount)).filter(
                Charge.user_id == user.id,
                Charge.status == 'RECEIVED'
            ).scalar() or 0
            
            # Status do usuário
            status = 'Ativo'
            if hasattr(user, 'is_trial_active') and user.is_trial_active():
                status = 'Trial'
            elif xml_balance <= 0:
                status = 'Sem Créditos'
            
            user_data = {
                'user': user,
                'xml_balance': xml_balance,
                'total_xmls': total_xmls,
                'total_spent': total_spent,
                'status': status,
                'status_badge': {
                    'Ativo': 'success',
                    'Trial': 'warning', 
                    'Sem Créditos': 'danger'
                }.get(status, 'secondary')
            }
            users_with_data.append(user_data)
            
        except Exception as e:
            logger.error(f"Erro ao processar usuário {user.id}: {e}")
            # Adicionar dados básicos mesmo com erro
            user_data = {
                'user': user,
                'xml_balance': 0,
                'total_xmls': 0,
                'total_spent': 0,
                'status': 'Erro',
                'status_badge': 'secondary'
            }
            users_with_data.append(user_data)
    
    logger.info(f"Admin: Enviando {len(users_with_data)} usuários para template")
    
    return render_template('admin_users.html', 
                         users_with_data=users_with_data,
                         search='')

@app.route('/admin/users/<int:user_id>')
@login_required
def admin_user_detail(user_id):
    """Detalhes de um usuário específico"""
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard'))
    
    user = User.query.get_or_404(user_id)
    
    # Estatísticas do usuário
    user_stats = {
        'total_xmls': XMLFile.query.filter_by(user_id=user_id).count(),
        'total_spent': sum(
            usage.cost for usage in UsageRecord.query.filter_by(user_id=user_id).all()
        ),
        'total_danfes': UsageRecord.query.filter_by(user_id=user_id).count(),
        'total_labels': 0  # Será implementado quando houver dados de etiquetas
    }
    
    # Atividade recente
    recent_xmls = XMLFile.query.filter_by(user_id=user_id).order_by(
        XMLFile.imported_at.desc()
    ).limit(10).all()
    
    recent_charges = Charge.query.filter_by(user_id=user_id).order_by(
        Charge.created_at.desc()
    ).limit(5).all()
    
    return render_template('admin_user_detail.html',
                         user=user,
                         user_stats=user_stats,
                         recent_xmls=recent_xmls,
                         recent_charges=recent_charges)

@app.route('/admin/users/create', methods=['POST'])
@login_required
def admin_create_user():
    """Criar novo usuário"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Acesso negado'})
    
    try:
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        initial_balance = float(request.form.get('initial_balance', 0))
        is_admin = bool(request.form.get('is_admin'))
        
        # Verificar se email já existe
        if User.query.filter_by(email=email).first():
            return jsonify({'success': False, 'message': 'Email já cadastrado'})
        
        # Criar usuário
        user = User(
            name=name,
            email=email,
            is_admin=is_admin,
            active=True,
            current_balance=initial_balance
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Adicionar saldo inicial se especificado
        if initial_balance > 0:
            charge = Charge(
                user_id=user.id,
                amount=initial_balance,
                description='Saldo inicial',
                status='paid'
            )
            db.session.add(charge)
            db.session.commit()
        
        return jsonify({'success': True, 'message': 'Usuário criado com sucesso'})
        
    except Exception as e:
        logger.error(f"Erro ao criar usuário: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/users/edit', methods=['POST'])
@login_required
def admin_edit_user():
    """Editar usuário"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Acesso negado'})
    
    try:
        user_id = request.form.get('user_id')
        user = User.query.get_or_404(user_id)
        
        user.name = request.form.get('name', user.name)
        user.email = request.form.get('email', user.email)
        user.active = bool(request.form.get('active'))
        user.is_admin = bool(request.form.get('is_admin'))
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Usuário atualizado com sucesso'})
        
    except Exception as e:
        logger.error(f"Erro ao editar usuário: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/users/add-balance', methods=['POST'])
@login_required
def admin_add_balance():
    """Adicionar créditos a um usuário"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Acesso negado'})
    
    try:
        user_id = request.form.get('user_id')
        amount = float(request.form.get('amount'))
        description = request.form.get('description', 'Créditos adicionados pelo admin')
        
        user = User.query.get_or_404(user_id)
        
        # Criar cobrança
        charge = Charge(
            user_id=user_id,
            amount=amount,
            description=description,
            status='paid'
        )
        db.session.add(charge)
        
        # Atualizar saldo
        user.current_balance = (user.current_balance or 0) + amount
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Créditos adicionados com sucesso'})
        
    except Exception as e:
        logger.error(f"Erro ao adicionar créditos: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/users/<int:user_id>/toggle', methods=['POST'])
@login_required
def admin_toggle_user_status(user_id):
    """Ativar/desativar usuário"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Acesso negado'})
    
    try:
        user = User.query.get_or_404(user_id)
        user.active = request.json.get('active', not user.active)
        
        db.session.commit()
        
        status = 'ativado' if user.active else 'desativado'
        return jsonify({'success': True, 'message': f'Usuário {status} com sucesso'})
        
    except Exception as e:
        logger.error(f"Erro ao alterar status do usuário: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/charges')
@login_required
def admin_charges():
    """Gerenciar cobranças"""
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard'))
    
    # Filtros
    status_filter = request.args.get('status')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    page = int(request.args.get('page', 1))
    
    # Query base
    query = Charge.query.join(User)
    
    # Aplicar filtros
    if status_filter:
        query = query.filter(Charge.status == status_filter)
    if date_from:
        query = query.filter(Charge.created_at >= date_from)
    if date_to:
        query = query.filter(Charge.created_at <= date_to)
    
    # Paginação
    charges = query.order_by(Charge.created_at.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    
    # Estatísticas
    stats = {
        'total_revenue': db.session.query(db.func.sum(Charge.amount)).filter(
            Charge.status == 'paid', Charge.amount > 0
        ).scalar() or 0,
        'monthly_revenue': db.session.query(db.func.sum(Charge.amount)).filter(
            Charge.status == 'paid',
            Charge.amount > 0,
            Charge.created_at >= datetime.now().replace(day=1)
        ).scalar() or 0,
        'pending_charges': Charge.query.filter_by(status='pending').count(),
        'success_rate': 0
    }
    
    # Taxa de sucesso
    total_charges = Charge.query.count()
    if total_charges > 0:
        paid_charges = Charge.query.filter_by(status='paid').count()
        stats['success_rate'] = (paid_charges / total_charges) * 100
    
    # Lista de usuários para criação
    users = User.query.order_by(User.name).all()
    
    return render_template('admin_charges.html',
                         charges=charges.items,
                         stats=stats,
                         users=users,
                         pagination=charges)

@app.route('/admin/charges/create', methods=['POST'])
@login_required
def admin_create_charge():
    """Criar nova cobrança"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Acesso negado'})
    
    try:
        user_id = request.form.get('user_id')
        amount = float(request.form.get('amount'))
        description = request.form.get('description')
        status = request.form.get('status', 'pending')
        
        user = User.query.get_or_404(user_id)
        
        # Criar cobrança
        charge = Charge(
            user_id=user_id,
            amount=amount,
            description=description,
            status=status
        )
        db.session.add(charge)
        
        # Se paga, atualizar saldo
        if status == 'paid':
            user.current_balance = (user.current_balance or 0) + amount
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Cobrança criada com sucesso'})
        
    except Exception as e:
        logger.error(f"Erro ao criar cobrança: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/charges/<int:charge_id>')
@login_required
def admin_charge_detail(charge_id):
    """Detalhes de uma cobrança"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Acesso negado'})
    
    charge = Charge.query.get_or_404(charge_id)
    
    html = f"""
    <div class="row">
        <div class="col-md-6">
            <h6>Informações da Cobrança</h6>
            <p><strong>ID:</strong> {charge.id}</p>
            <p><strong>Usuário:</strong> {charge.user.name or charge.user.email}</p>
            <p><strong>Valor:</strong> R$ {charge.amount:.2f}</p>
            <p><strong>Status:</strong> {charge.status}</p>
            <p><strong>Descrição:</strong> {charge.description or 'N/A'}</p>
        </div>
        <div class="col-md-6">
            <h6>Detalhes Técnicos</h6>
            <p><strong>Criada em:</strong> {charge.created_at.strftime('%d/%m/%Y %H:%M') if charge.created_at else 'N/A'}</p>
            <p><strong>Stripe ID:</strong> {charge.stripe_charge_id or 'N/A'}</p>
            <p><strong>Asaas ID:</strong> {charge.asaas_charge_id or 'N/A'}</p>
        </div>
    </div>
    """
    
    return jsonify({'success': True, 'html': html})

@app.route('/admin/charges/<int:charge_id>/mark-paid', methods=['POST'])
@login_required
def admin_mark_charge_paid(charge_id):
    """Marcar cobrança como paga"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Acesso negado'})
    
    try:
        charge = Charge.query.get_or_404(charge_id)
        
        if charge.status != 'pending':
            return jsonify({'success': False, 'message': 'Cobrança não está pendente'})
        
        charge.status = 'paid'
        
        # Atualizar saldo se for positivo
        if charge.amount > 0:
            charge.user.current_balance = (charge.user.current_balance or 0) + charge.amount
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Cobrança marcada como paga'})
        
    except Exception as e:
        logger.error(f"Erro ao marcar cobrança como paga: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/charges/<int:charge_id>/refund', methods=['POST'])
@login_required
def admin_refund_charge(charge_id):
    """Reembolsar cobrança"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Acesso negado'})
    
    try:
        charge = Charge.query.get_or_404(charge_id)
        reason = request.json.get('reason', 'Reembolso administrativo')
        
        if charge.status != 'paid' or charge.amount <= 0:
            return jsonify({'success': False, 'message': 'Cobrança não pode ser reembolsada'})
        
        # Criar cobrança de reembolso
        refund_charge = Charge(
            user_id=charge.user_id,
            amount=-charge.amount,
            description=f'Reembolso: {reason}',
            status='paid'
        )
        db.session.add(refund_charge)
        
        # Atualizar saldo
        charge.user.current_balance = (charge.user.current_balance or 0) - charge.amount
        
        # Marcar original como reembolsada
        charge.status = 'refunded'
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Reembolso processado com sucesso'})
        
    except Exception as e:
        logger.error(f"Erro ao processar reembolso: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/charges/<int:charge_id>/delete', methods=['DELETE'])
@login_required
def admin_delete_charge(charge_id):
    """Excluir cobrança"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Acesso negado'})
    
    try:
        charge = Charge.query.get_or_404(charge_id)
        
        # Se era paga, reverter do saldo
        if charge.status == 'paid' and charge.amount != 0:
            charge.user.current_balance = (charge.user.current_balance or 0) - charge.amount
        
        db.session.delete(charge)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Cobrança excluída com sucesso'})
        
    except Exception as e:
        logger.error(f"Erro ao excluir cobrança: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/packages')
@login_required
@require_admin
def admin_packages():
    """Gerenciar pacotes e produtos Stripe"""
    products = StripeProduct.query.order_by(StripeProduct.created_at.desc()).all()
    
    # Estatísticas
    stats = {
        'total_products': StripeProduct.query.filter_by(active=True).count(),
        'active_subscriptions': UserSubscription.query.filter_by(status='active').count(),
        'monthly_revenue': db.session.query(db.func.sum(Charge.amount)).filter(
            Charge.status == 'paid',
            Charge.amount > 0,
            Charge.created_at >= datetime.now().replace(day=1)
        ).scalar() or 0,
        'conversion_rate': 0
    }
    
    # Taxa de conversão
    total_trials = UserSubscription.query.filter(
        UserSubscription.trial_expires_at.isnot(None)
    ).count()
    if total_trials > 0:
        converted_trials = UserSubscription.query.filter(
            UserSubscription.trial_expires_at.isnot(None),
            UserSubscription.status == 'active'
        ).count()
        stats['conversion_rate'] = (converted_trials / total_trials) * 100
    
    # Assinaturas recentes
    recent_subscriptions = UserSubscription.query.join(User).join(StripeProduct).order_by(
        UserSubscription.created_at.desc()
    ).limit(20).all()
    
    return render_template('admin_packages.html', 
                         products=products, 
                         stats=stats,
                         recent_subscriptions=recent_subscriptions)

@app.route('/admin/packages/sync-stripe', methods=['POST'])
@login_required
@require_admin
def admin_sync_stripe():
    """Sincronizar produtos do Stripe"""
    try:
        # Inicializar produtos padrão
        init_stripe_products()
        
        return jsonify({'success': True, 'message': 'Produtos sincronizados com sucesso'})
        
    except Exception as e:
        logger.error(f"Erro na sincronização: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/packages/create', methods=['POST'])
@login_required
@require_admin
def admin_create_package():
    """Criar novo pacote"""
    try:
        stripe_product_id = request.form.get('stripe_product_id')
        name = request.form.get('name')
        description = request.form.get('description')
        package_type = request.form.get('package_type')
        default_price_id = request.form.get('default_price_id')
        price_amount = request.form.get('price_amount')
        credits_amount = request.form.get('credits_amount')
        
        # Verificar se produto já existe
        if StripeProduct.query.filter_by(stripe_product_id=stripe_product_id).first():
            return jsonify({'success': False, 'message': 'Produto já existe'})
        
        # Criar produto
        product = StripeProduct(
            stripe_product_id=stripe_product_id,
            name=name,
            description=description,
            package_type=package_type,
            default_price_id=default_price_id,
            price_amount=int(price_amount) if price_amount else None,
            credits_amount=int(credits_amount) if credits_amount else 0,
            active=True
        )
        db.session.add(product)
        db.session.flush()  # Para obter o ID
        
        # Adicionar funcionalidades
        for key, value in request.form.items():
            if key.startswith('features[') and key.endswith('[key]'):
                feature_index = key.split('[')[1].split(']')[0]
                feature_key = value
                feature_name = request.form.get(f'features[{feature_index}][name]')
                feature_limit = request.form.get(f'features[{feature_index}][limit]')
                
                if feature_key and feature_name:
                    feature = PackageFeature(
                        product_id=product.id,
                        feature_key=feature_key,
                        feature_name=feature_name,
                        usage_limit=int(feature_limit) if feature_limit else -1,
                        enabled=True
                    )
                    db.session.add(feature)
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Pacote criado com sucesso'})
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar pacote: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/packages/<int:package_id>/toggle', methods=['POST'])
@login_required
@require_admin
def admin_toggle_package(package_id):
    """Ativar/desativar pacote"""
    try:
        product = StripeProduct.query.get_or_404(package_id)
        product.active = request.json.get('active', not product.active)
        
        db.session.commit()
        
        status = 'ativado' if product.active else 'desativado'
        return jsonify({'success': True, 'message': f'Pacote {status} com sucesso'})
        
    except Exception as e:
        logger.error(f"Erro ao alterar status do pacote: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/packages/<int:package_id>/edit')
@login_required
@require_admin
def admin_edit_package(package_id):
    """Editar pacote"""
    product = StripeProduct.query.get_or_404(package_id)
    return render_template('admin_edit_package.html', product=product)

@app.route('/admin/packages/<int:package_id>/subscriptions')
@login_required
@require_admin
def admin_package_subscriptions(package_id):
    """Ver assinantes de um pacote"""
    product = StripeProduct.query.get_or_404(package_id)
    subscriptions = UserSubscription.query.filter_by(product_id=package_id).join(User).order_by(
        UserSubscription.created_at.desc()
    ).all()
    
    return render_template('admin_package_subscriptions.html', 
                         product=product, 
                         subscriptions=subscriptions)

@app.route('/admin/subscriptions/<int:subscription_id>/cancel', methods=['POST'])
@login_required
@require_admin
def admin_cancel_subscription(subscription_id):
    """Cancelar assinatura"""
    try:
        subscription = UserSubscription.query.get_or_404(subscription_id)
        subscription.status = 'canceled'
        subscription.canceled_at = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Assinatura cancelada com sucesso'})
        
    except Exception as e:
        logger.error(f"Erro ao cancelar assinatura: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/subscriptions/<int:subscription_id>/add-credits', methods=['POST'])
@login_required
@require_admin
def admin_add_subscription_credits(subscription_id):
    """Adicionar créditos a uma assinatura"""
    try:
        subscription = UserSubscription.query.get_or_404(subscription_id)
        credits = int(request.json.get('credits', 0))
        
        subscription.credits_remaining += credits
        subscription.credits_total += credits
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': f'{credits} créditos adicionados'})
        
    except Exception as e:
        logger.error(f"Erro ao adicionar créditos: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/admin/features/usage')
@login_required
@require_admin
def admin_features_usage():
    """Relatório de uso de funcionalidades"""
    # Uso por funcionalidade nos últimos 30 dias
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    usage_stats = db.session.query(
        FeatureUsage.feature_key,
        db.func.count(FeatureUsage.id).label('usage_count'),
        db.func.count(db.func.distinct(FeatureUsage.user_id)).label('unique_users')
    ).filter(
        FeatureUsage.created_at >= thirty_days_ago
    ).group_by(FeatureUsage.feature_key).all()
    
    # Usuários mais ativos
    top_users = db.session.query(
        User.id,
        User.name,
        User.email,
        db.func.count(FeatureUsage.id).label('usage_count')
    ).join(FeatureUsage).filter(
        FeatureUsage.created_at >= thirty_days_ago
    ).group_by(User.id, User.name, User.email).order_by(
        db.func.count(FeatureUsage.id).desc()
    ).limit(10).all()
    
    return render_template('admin_features_usage.html',
                         usage_stats=usage_stats,
                         top_users=top_users)



@app.route('/api/pricing/calculate', methods=['POST'])
@login_required
def api_calculate_pricing():
    """API para calcular preço baseado na quantidade de XMLs"""
    try:
        xml_count = int(request.json.get('xml_count', 0))
        
        if xml_count <= 0:
            return jsonify({'error': 'Quantidade inválida'}), 400
        
        pricing = XMLPricingTiers.calculate_price(xml_count)
        
        return jsonify({
            'success': True,
            'pricing': pricing
        })
        
    except Exception as e:
        logger.error(f"Erro no cálculo de preços: {e}")
        return jsonify({'error': 'Erro interno'}), 500

@app.route('/webhook/stripe/purchase-success', methods=['POST'])
def stripe_purchase_success():
    """Webhook para processar compras bem-sucedidas do Stripe"""
    try:
        payload = request.get_data()
        sig_header = request.headers.get('Stripe-Signature')
        
        # Processar webhook do Stripe
        event = process_stripe_webhook(payload, sig_header)
        
        if event and event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            # Extrair dados da compra
            customer_email = session['customer_details']['email']
            metadata = session.get('metadata', {})
            xml_count = int(metadata.get('xml_count', 0))
            tier_name = metadata.get('tier_name', '')
            
            # Encontrar usuário
            user = User.query.filter_by(email=customer_email).first()
            if user and xml_count > 0:
                # Encontrar tier correspondente
                tier_data = None
                for tier in XMLPricingTiers.TIERS:
                    if tier['xml_count'] == xml_count:
                        tier_data = tier
                        break
                
                if tier_data:
                    # Criar assinatura de créditos
                    success = create_xml_credit_subscription(
                        user.id, 
                        tier_data, 
                        session['id']
                    )
                    
                    if success:
                        logger.info(f"Créditos XML adicionados para usuário {user.email}: {xml_count} créditos")
                    else:
                        logger.error(f"Falha ao adicionar créditos para {user.email}")
        
        return jsonify({'success': True})
        
    except Exception as e:
        logger.error(f"Erro no webhook de compra Stripe: {e}")
        return jsonify({'error': 'Erro interno'}), 500

@app.route('/admin/settings')
@login_required
def admin_settings():
    """Admin system settings"""
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard'))
    
    modules = ServiceModule.query.all()
    settings = SystemSettings.query.all()
    
    return render_template('admin_settings.html', modules=modules, settings=settings)

@app.route('/admin/update_module_cost', methods=['POST'])
@login_required
def update_module_cost():
    """Update module cost"""
    if not current_user.is_admin:
        return jsonify({'error': 'Acesso negado'}), 403
    
    module_id = request.form.get('module_id')
    new_cost = float(request.form.get('cost', 0))
    
    module = ServiceModule.query.get(module_id)
    if module:
        module.cost_per_use = new_cost
        db.session.commit()
        flash(f'Custo do módulo {module.name} atualizado para R$ {new_cost:.2f}', 'success')
    
    return redirect(url_for('admin_settings'))

# Webhook for Asaas payments
@app.route('/webhook/asaas', methods=['POST'])
def asaas_webhook():
    """Process Asaas payment webhook"""
    try:
        data = request.get_json()
        
        if process_webhook_payment(data):
            return jsonify({'status': 'ok'}), 200
        else:
            return jsonify({'error': 'Processing failed'}), 400
            
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({'error': 'Internal error'}), 500

# Background processing functions


def process_danfe_generation(job_id):
    """Generate DANFE for downloaded XMLs"""
    from simple_danfe import generate_simple_danfe
    
    with jobs_lock:
        job = download_jobs.get(job_id)
    
    if not job:
        return
    
    try:
        # Generate DANFE for each downloaded XML
        for xml_file in job.downloaded_files:
            if xml_file.endswith('.xml'):
                try:
                    # Read XML content
                    with open(xml_file, 'r', encoding='utf-8') as f:
                        xml_content = f.read()
                    
                    # Generate PDF
                    pdf_file = xml_file.replace('.xml', '.pdf')
                    success = generate_simple_danfe(xml_content, pdf_file)
                    
                    if success:
                        job.downloaded_files.append(pdf_file)
                        
                except Exception as e:
                    logger.error(f"Error generating DANFE for {xml_file}: {e}")
                    
    except Exception as e:
        logger.error(f"DANFE generation error: {str(e)}")

# API endpoints for job status
@app.route('/job_status/<job_id>')
@login_required
def job_status(job_id):
    """Get job status"""
    with jobs_lock:
        job = download_jobs.get(job_id)
        
        if not job or job.user_id != current_user.id:
            return jsonify({'error': 'Job not found'}), 404
        
        return jsonify(job.to_dict())

# Configurar timezone de São Paulo
SP_TZ = pytz.timezone('America/Sao_Paulo')

def to_sp_time(utc_time):
    """Converte UTC para horário de São Paulo"""
    if utc_time:
        if utc_time.tzinfo is None:
            utc_time = pytz.utc.localize(utc_time)
        return utc_time.astimezone(SP_TZ)
    return None

# Registrar filtro de template para timezone
@app.template_filter('sp_datetime')
def sp_datetime_filter(utc_time):
    """Filtro de template para converter para horário de São Paulo"""
    sp_time = to_sp_time(utc_time)
    if sp_time:
        return sp_time.strftime('%d/%m/%Y às %H:%M')
    return 'N/A'

# Rotas principais do sistema
@app.route('/meus-xmls')
@login_required
@rate_limit_check(max_requests=100, window_minutes=15)
def meus_xmls():
    """Lista apenas XMLs corretamente processados com dados completos - com isolamento de dados"""
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # Filtros com sanitização de entrada
    search_term = SecurityManager.sanitize_input(request.args.get('search', ''))
    date_from = SecurityManager.sanitize_input(request.args.get('date_from', ''))
    date_to = SecurityManager.sanitize_input(request.args.get('date_to', ''))
    uf_filter = SecurityManager.sanitize_input(request.args.get('uf', ''))
    cidade_filter = SecurityManager.sanitize_input(request.args.get('cidade', ''))
    
    # Buscar XMLs com isolamento de dados por usuário
    xmls_query = XMLFile.query.filter_by(user_id=current_user.id)
    xmls_query = DataIsolationManager.filter_user_xmls(xmls_query, current_user.id)
    all_xmls_list = xmls_query.all()
    
    # Aplicar filtros de busca
    if search_term:
        filtered_xmls = []
        for xml in all_xmls_list:
            if (search_term.lower() in (xml.invoice_key or '').lower() or
                search_term.lower() in (getattr(xml, 'nome_emitente', '') or '').lower() or
                search_term.lower() in (getattr(xml, 'destinatario_razao', '') or '').lower() or
                search_term.lower() in (getattr(xml, 'numero_nf', '') or '').lower()):
                filtered_xmls.append(xml)
        all_xmls_list = filtered_xmls
    
    # Aplicar filtros de data
    if date_from or date_to:
        filtered_xmls = []
        for xml in all_xmls_list:
            xml_date = getattr(xml, 'data_emissao', None) or xml.imported_at.date()
            
            include_xml = True
            if date_from:
                try:
                    date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
                    if xml_date < date_from_parsed:
                        include_xml = False
                except:
                    pass
            
            if date_to and include_xml:
                try:
                    date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
                    if xml_date > date_to_parsed:
                        include_xml = False
                except:
                    pass
            
            if include_xml:
                filtered_xmls.append(xml)
        all_xmls_list = filtered_xmls
    
    # Aplicar filtros de UF e cidade
    if uf_filter or cidade_filter:
        filtered_xmls = []
        for xml in all_xmls_list:
            include_xml = True
            
            if uf_filter:
                remetente_uf = getattr(xml, 'remetente_uf', None)
                destinatario_uf = getattr(xml, 'destinatario_uf', None)
                if not (remetente_uf == uf_filter or destinatario_uf == uf_filter):
                    include_xml = False
            
            if cidade_filter and include_xml:
                remetente_cidade = getattr(xml, 'remetente_cidade', None) or ''
                destinatario_cidade = getattr(xml, 'destinatario_cidade', None) or ''
                if not (cidade_filter.lower() in remetente_cidade.lower() or 
                       cidade_filter.lower() in destinatario_cidade.lower()):
                    include_xml = False
            
            if include_xml:
                filtered_xmls.append(xml)
        all_xmls_list = filtered_xmls
    
    # Ordenar por data de importação (mais recente primeiro)
    all_xmls_list.sort(key=lambda x: x.imported_at, reverse=True)
    
    # Paginação manual
    total_xmls = len(all_xmls_list)
    total_pages = (total_xmls + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    xmls = all_xmls_list[start:end]
    
    # Obter listas para filtros
    ufs = db.session.query(XMLFile.remetente_uf).filter(XMLFile.user_id == current_user.id, XMLFile.remetente_uf.isnot(None)).distinct().all()
    ufs_dest = db.session.query(XMLFile.destinatario_uf).filter(XMLFile.user_id == current_user.id, XMLFile.destinatario_uf.isnot(None)).distinct().all()
    all_ufs = list(set([uf[0] for uf in ufs] + [uf[0] for uf in ufs_dest if uf[0]]))
    
    cidades = db.session.query(XMLFile.remetente_cidade).filter(XMLFile.user_id == current_user.id, XMLFile.remetente_cidade.isnot(None)).distinct().all()
    cidades_dest = db.session.query(XMLFile.destinatario_cidade).filter(XMLFile.user_id == current_user.id, XMLFile.destinatario_cidade.isnot(None)).distinct().all()
    all_cidades = list(set([cidade[0] for cidade in cidades] + [cidade[0] for cidade in cidades_dest if cidade[0]]))
    
    return render_template('meus_xmls.html', 
                         xmls=xmls,
                         current_user=current_user,
                         page=page,
                         total_pages=total_pages,
                         total_xmls=total_xmls,
                         search_term=search_term,
                         date_from=date_from,
                         date_to=date_to,
                         uf_filter=uf_filter,
                         cidade_filter=cidade_filter,
                         all_ufs=sorted(all_ufs),
                         all_cidades=sorted(all_cidades))

@app.route('/download-xml/<xml_id>')
@login_required
def download_xml_file(xml_id):
    """Download arquivo XML específico"""
    # Buscar XML tanto em XMLFile quanto XMLFile
    xml = XMLFile.query.filter_by(id=xml_id, user_id=current_user.id).first()
    if not xml:
        xml = XMLFile.query.filter_by(id=xml_id, user_id=current_user.id).first()
    
    if not xml:
        flash('XML não encontrado.', 'error')
        return redirect(url_for('meus_xmls'))
    
    # Verificar se arquivo existe
    if hasattr(xml, 'file_path') and xml.file_path and os.path.exists(xml.file_path):
        return send_file(xml.file_path, as_attachment=True, download_name=f"{xml.invoice_key}.xml")
    
    # Se não tem arquivo físico, criar a partir do conteúdo
    if xml.xml_content:
        from flask import make_response
        response = make_response(xml.xml_content)
        response.headers['Content-Type'] = 'application/xml'
        response.headers['Content-Disposition'] = f'attachment; filename="{xml.invoice_key}.xml"'
        return response
    
    flash('Arquivo XML não disponível.', 'error')
    return redirect(url_for('meus_xmls'))

@app.route('/labels-module')
@login_required 
def labels_module():
    """Módulo de geração de etiquetas com filtros"""
    # Verificar se usuário tem acesso ao módulo de etiquetas
    labels_module = ServiceModule.query.filter_by(name='Etiquetas de Transporte').first()
    if not labels_module:
        flash('Módulo de etiquetas não disponível.', 'error')
        return redirect(url_for('dashboard'))
    
    # Verificar se usuário está em período de teste
    is_trial_active = current_user.trial_expires_at and current_user.trial_expires_at > datetime.now()
    
    # Verificar se usuário tem assinatura ativa do módulo
    from package_models import UserSubscription, StripeProduct
    active_subscription = UserSubscription.query.join(StripeProduct).filter(
        UserSubscription.user_id == current_user.id,
        StripeProduct.stripe_product_id == 'prod_SSVViDPzXYZHhO',  # Labels module product ID
        UserSubscription.status == 'active'
    ).first()
    
    # Se não tem acesso (nem trial nem assinatura), mostrar página de compra
    if not is_trial_active and not active_subscription:
        return render_template('labels_purchase.html', 
                             labels_module=labels_module,
                             user=current_user)
    
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # Filtros
    search_term = request.args.get('search', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    uf_filter = request.args.get('uf', '')
    cidade_filter = request.args.get('cidade', '')
    peso_min = request.args.get('peso_min', '')
    peso_max = request.args.get('peso_max', '')
    valor_min = request.args.get('valor_min', '')
    valor_max = request.args.get('valor_max', '')
    
    # Buscar XMLs da tabela unificada
    all_xmls_list = XMLFile.query.filter_by(user_id=current_user.id).all()
    
    # Aplicar filtros de busca
    if search_term:
        filtered_xmls = []
        for xml in all_xmls_list:
            if (search_term.lower() in (xml.invoice_key or '').lower() or
                search_term.lower() in (getattr(xml, 'nome_emitente', '') or '').lower() or
                search_term.lower() in (getattr(xml, 'destinatario_razao', '') or '').lower() or
                search_term.lower() in (getattr(xml, 'numero_nf', '') or '').lower() or
                search_term.lower() in (getattr(xml, 'remetente_cidade', '') or '').lower() or
                search_term.lower() in (getattr(xml, 'destinatario_cidade', '') or '').lower()):
                filtered_xmls.append(xml)
        all_xmls_list = filtered_xmls
    
    # Aplicar filtros de data
    if date_from or date_to:
        filtered_xmls = []
        for xml in all_xmls_list:
            xml_date = getattr(xml, 'data_emissao', None) or xml.imported_at.date()
            
            include_xml = True
            if date_from:
                try:
                    date_from_parsed = datetime.strptime(date_from, '%Y-%m-%d').date()
                    if xml_date < date_from_parsed:
                        include_xml = False
                except:
                    pass
            
            if date_to and include_xml:
                try:
                    date_to_parsed = datetime.strptime(date_to, '%Y-%m-%d').date()
                    if xml_date > date_to_parsed:
                        include_xml = False
                except:
                    pass
            
            if include_xml:
                filtered_xmls.append(xml)
        all_xmls_list = filtered_xmls
    
    # Aplicar filtros de UF e cidade
    if uf_filter or cidade_filter:
        filtered_xmls = []
        for xml in all_xmls_list:
            include_xml = True
            
            if uf_filter:
                remetente_uf = getattr(xml, 'remetente_uf', None)
                destinatario_uf = getattr(xml, 'destinatario_uf', None)
                if not (remetente_uf == uf_filter or destinatario_uf == uf_filter):
                    include_xml = False
            
            if cidade_filter and include_xml:
                remetente_cidade = getattr(xml, 'remetente_cidade', None) or ''
                destinatario_cidade = getattr(xml, 'destinatario_cidade', None) or ''
                if not (cidade_filter.lower() in remetente_cidade.lower() or 
                       cidade_filter.lower() in destinatario_cidade.lower()):
                    include_xml = False
            
            if include_xml:
                filtered_xmls.append(xml)
        all_xmls_list = filtered_xmls
    
    # Aplicar filtros de peso e valor
    if peso_min or peso_max or valor_min or valor_max:
        filtered_xmls = []
        for xml in all_xmls_list:
            include_xml = True
            
            if peso_min:
                try:
                    peso_min_val = float(peso_min)
                    xml_peso = getattr(xml, 'peso_bruto', None)
                    if xml_peso is None or float(xml_peso) < peso_min_val:
                        include_xml = False
                except:
                    pass
            
            if peso_max and include_xml:
                try:
                    peso_max_val = float(peso_max)
                    xml_peso = getattr(xml, 'peso_bruto', None)
                    if xml_peso is None or float(xml_peso) > peso_max_val:
                        include_xml = False
                except:
                    pass
            
            if valor_min and include_xml:
                try:
                    valor_min_val = float(valor_min)
                    xml_valor = getattr(xml, 'valor_total', None)
                    if xml_valor is None or float(xml_valor) < valor_min_val:
                        include_xml = False
                except:
                    pass
            
            if valor_max and include_xml:
                try:
                    valor_max_val = float(valor_max)
                    xml_valor = getattr(xml, 'valor_total', None)
                    if xml_valor is None or float(xml_valor) > valor_max_val:
                        include_xml = False
                except:
                    pass
            
            if include_xml:
                filtered_xmls.append(xml)
        all_xmls_list = filtered_xmls
    
    # Ordenar por data de importação (mais recente primeiro)
    all_xmls_list.sort(key=lambda x: x.imported_at, reverse=True)
    
    # Paginação manual
    total_xmls = len(all_xmls_list)
    total_pages = (total_xmls + per_page - 1) // per_page
    start = (page - 1) * per_page
    end = start + per_page
    xmls = all_xmls_list[start:end]
    
    # Obter listas para filtros
    ufs = db.session.query(XMLFile.remetente_uf).filter(XMLFile.user_id == current_user.id, XMLFile.remetente_uf.isnot(None)).distinct().all()
    ufs_dest = db.session.query(XMLFile.destinatario_uf).filter(XMLFile.user_id == current_user.id, XMLFile.destinatario_uf.isnot(None)).distinct().all()
    all_ufs = list(set([uf[0] for uf in ufs] + [uf[0] for uf in ufs_dest if uf[0]]))
    
    cidades = db.session.query(XMLFile.remetente_cidade).filter(XMLFile.user_id == current_user.id, XMLFile.remetente_cidade.isnot(None)).distinct().all()
    cidades_dest = db.session.query(XMLFile.destinatario_cidade).filter(XMLFile.user_id == current_user.id, XMLFile.destinatario_cidade.isnot(None)).distinct().all()
    all_cidades = list(set([cidade[0] for cidade in cidades] + [cidade[0] for cidade in cidades_dest if cidade[0]]))
    
    return render_template('labels.html', 
                         xmls=xmls,
                         current_user=current_user,
                         page=page,
                         total_pages=total_pages,
                         total_xmls=total_xmls,
                         search_term=search_term,
                         date_from=date_from,
                         date_to=date_to,
                         uf_filter=uf_filter,
                         cidade_filter=cidade_filter,
                         peso_min=peso_min,
                         peso_max=peso_max,
                         valor_min=valor_min,
                         valor_max=valor_max,
                         all_ufs=sorted(all_ufs),
                         all_cidades=sorted(all_cidades))

@app.route('/api-docs')
@login_required
@rate_limit_check(max_requests=30, window_minutes=10)
def api_docs():
    """Documentação da API com geração de credenciais"""
    # Obter saldo atual de créditos XML
    from simple_credit_system import get_user_xml_balance
    xml_balance = get_user_xml_balance(current_user.id)
    
    return render_template('api_docs.html', 
                         xml_balance=xml_balance,
                         has_api_credentials=current_user.has_api_credentials(),
                         api_key=current_user.api_key if current_user.has_api_credentials() else None)

@app.route('/generate-api-credentials', methods=['POST'])
@login_required
@rate_limit_check(max_requests=5, window_minutes=15)
def generate_api_credentials():
    """Gerar novas credenciais API para o usuário"""
    try:
        credentials = current_user.generate_api_credentials()
        flash('Credenciais API geradas com sucesso!', 'success')
        return jsonify({
            'success': True,
            'api_key': credentials['api_key'],
            'api_secret': credentials['api_secret']
        })
    except Exception as e:
        logger.error(f"Erro ao gerar credenciais API: {e}")
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500

@app.route('/revoke-api-credentials', methods=['POST'])
@login_required
@rate_limit_check(max_requests=5, window_minutes=15)
def revoke_api_credentials():
    """Revogar credenciais API do usuário"""
    try:
        current_user.revoke_api_credentials()
        flash('Credenciais API revogadas com sucesso!', 'info')
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Erro ao revogar credenciais API: {e}")
        return jsonify({'success': False, 'error': 'Erro interno do servidor'}), 500

@app.route('/upload-xml', methods=['GET', 'POST'])
@login_required
@rate_limit_check(max_requests=20, window_minutes=10)
def upload_xml():
    """Upload manual de arquivos XML"""
    if request.method == 'GET':
        # Get recent uploads for display (all import types)
        recent_uploads = XMLFile.query.filter_by(
            user_id=current_user.id
        ).order_by(XMLFile.created_at.desc()).limit(5).all()
        
        return render_template('upload_xml_redesigned.html', recent_uploads=recent_uploads)
    
    try:
        # Verificar se arquivos foram enviados
        if 'xml_files' not in request.files:
            flash('Nenhum arquivo foi selecionado.', 'error')
            return redirect(url_for('upload_xml'))
        
        files = request.files.getlist('xml_files')
        if not files or files[0].filename == '':
            flash('Nenhum arquivo foi selecionado.', 'error')
            return redirect(url_for('upload_xml'))
        
        uploaded_count = 0
        error_count = 0
        errors = []
        
        for file in files:
            if file and file.filename:
                # Verificar se é arquivo XML
                if not file.filename.lower().endswith('.xml'):
                    errors.append(f"{file.filename}: Não é um arquivo XML")
                    error_count += 1
                    continue
                
                try:
                    # Ler conteúdo do arquivo
                    xml_content = file.read().decode('utf-8')
                    
                    # Processar e salvar XML usando a mesma função do email processor
                    result = process_and_save_uploaded_xml(
                        user_id=current_user.id,
                        xml_content=xml_content,
                        filename=file.filename
                    )
                    
                    if result and result['success']:
                        if result['is_new']:
                            uploaded_count += 1
                            logger.info(f"XML uploadado com sucesso: {file.filename} - Chave: {result['xml_file'].invoice_key}")
                        else:
                            errors.append(f"{file.filename}: XML já existe no sistema")
                            error_count += 1
                    else:
                        errors.append(f"{file.filename}: Erro ao processar XML")
                        error_count += 1
                    
                except Exception as e:
                    logger.error(f"Erro ao processar {file.filename}: {e}")
                    errors.append(f"{file.filename}: {str(e)}")
                    error_count += 1
        
        # Mostrar resultados
        if uploaded_count > 0:
            flash(f'{uploaded_count} XML(s) importado(s) com sucesso!', 'success')
        
        if error_count > 0:
            flash(f'{error_count} arquivo(s) com erro. Detalhes: {"; ".join(errors[:3])}', 'warning')
        
        return redirect(url_for('meus_xmls'))
        
    except Exception as e:
        logger.error(f"Erro no upload de XMLs: {e}")
        flash('Erro interno do servidor.', 'error')
        return redirect(url_for('upload_xml'))

def process_and_save_uploaded_xml(user_id, xml_content, filename):
    """
    Processa e salva XML uploadado no banco de dados
    Usa a mesma lógica de parsing do EmailXMLProcessor
    """
    try:
        # Parse do XML
        root = ET.fromstring(xml_content)
        
        # Namespaces da NFe
        namespaces = {
            'nfe': 'http://www.portalfiscal.inf.br/nfe'
        }
        
        # Inicializar dados extraídos
        xml_data = {
            'filename': filename,
            'numero_nf': 'N/A',
            'serie_nf': 'N/A',
            'chave_nf': 'N/A',
            'data_emissao': None,
            'valor_total': 0.0,
            'peso_bruto': 0.0,
            'peso_liquido': 0.0,
            'quantidade_volumes': 1,
            'nome_emitente': 'N/A',
            'cnpj_emitente': 'N/A',
            'cidade_emitente': 'N/A',
            'uf_emitente': 'N/A',
            'cep_emitente': 'N/A',
            'endereco_emitente': 'N/A',
            'nome_destinatario': 'N/A',
            'destinatario_cnpj_cpf': 'N/A',
            'cidade_destinatario': 'N/A',
            'uf_destinatario': 'N/A',
            'cep_destinatario': 'N/A',
            'endereco_destinatario': 'N/A',
            'nome_transportadora': 'N/A',
            'transportadora_cnpj': 'N/A'
        }
        
        # Buscar elemento principal da NFe
        inf_nfe = root.find('.//nfe:infNFe', namespaces)
        if inf_nfe is None:
            # Tentar sem namespace
            inf_nfe = root.find('.//infNFe')
        
        if inf_nfe is not None:
            # Chave da NFe
            chave = inf_nfe.get('Id', '')
            if chave.startswith('NFe'):
                xml_data['chave_nf'] = chave[3:]  # Remove 'NFe' do início
            else:
                xml_data['chave_nf'] = chave
            
            # Dados da identificação
            ide = inf_nfe.find('nfe:ide', namespaces) or inf_nfe.find('ide')
            if ide is not None:
                xml_data['numero_nf'] = ide.findtext('nfe:nNF', xml_data['numero_nf'], namespaces) or ide.findtext('nNF', xml_data['numero_nf'])
                xml_data['serie_nf'] = ide.findtext('nfe:serie', xml_data['serie_nf'], namespaces) or ide.findtext('serie', xml_data['serie_nf'])
                
                # Data de emissão
                data_emissao = ide.findtext('nfe:dhEmi', '', namespaces) or ide.findtext('dhEmi', '') or ide.findtext('nfe:dEmi', '', namespaces) or ide.findtext('dEmi', '')
                if data_emissao:
                    try:
                        if 'T' in data_emissao:
                            xml_data['data_emissao'] = datetime.fromisoformat(data_emissao.replace('Z', '+00:00'))
                        else:
                            xml_data['data_emissao'] = datetime.strptime(data_emissao, '%Y-%m-%d')
                    except:
                        pass
            
            # Dados do emitente
            emit = inf_nfe.find('nfe:emit', namespaces) or inf_nfe.find('emit')
            if emit is not None:
                xml_data['nome_emitente'] = emit.findtext('nfe:xNome', xml_data['nome_emitente'], namespaces) or emit.findtext('xNome', xml_data['nome_emitente'])
                xml_data['cnpj_emitente'] = emit.findtext('nfe:CNPJ', xml_data['cnpj_emitente'], namespaces) or emit.findtext('CNPJ', xml_data['cnpj_emitente'])
                
                # Endereço do emitente
                enderemit = emit.find('nfe:enderEmit', namespaces) or emit.find('enderEmit')
                if enderemit is not None:
                    xml_data['cidade_emitente'] = enderemit.findtext('nfe:xMun', xml_data['cidade_emitente'], namespaces) or enderemit.findtext('xMun', xml_data['cidade_emitente'])
                    xml_data['uf_emitente'] = enderemit.findtext('nfe:UF', xml_data['uf_emitente'], namespaces) or enderemit.findtext('UF', xml_data['uf_emitente'])
                    xml_data['cep_emitente'] = enderemit.findtext('nfe:CEP', xml_data['cep_emitente'], namespaces) or enderemit.findtext('CEP', xml_data['cep_emitente'])
                    
                    # Endereço completo
                    logradouro = enderemit.findtext('nfe:xLgr', '', namespaces) or enderemit.findtext('xLgr', '')
                    numero = enderemit.findtext('nfe:nro', '', namespaces) or enderemit.findtext('nro', '')
                    bairro = enderemit.findtext('nfe:xBairro', '', namespaces) or enderemit.findtext('xBairro', '')
                    xml_data['endereco_emitente'] = f"{logradouro}, {numero}, {bairro}".strip(', ')
            
            # Dados do destinatário
            dest = inf_nfe.find('nfe:dest', namespaces) or inf_nfe.find('dest')
            if dest is not None:
                xml_data['nome_destinatario'] = dest.findtext('nfe:xNome', xml_data['nome_destinatario'], namespaces) or dest.findtext('xNome', xml_data['nome_destinatario'])
                
                # CNPJ ou CPF do destinatário
                cnpj_dest = dest.findtext('nfe:CNPJ', None, namespaces) or dest.findtext('CNPJ')
                cpf_dest = dest.findtext('nfe:CPF', None, namespaces) or dest.findtext('CPF')
                xml_data['destinatario_cnpj_cpf'] = cnpj_dest if cnpj_dest else (cpf_dest if cpf_dest else xml_data['destinatario_cnpj_cpf'])
                
                # Endereço do destinatário
                enderdest = dest.find('nfe:enderDest', namespaces) or dest.find('enderDest')
                if enderdest is not None:
                    xml_data['cidade_destinatario'] = enderdest.findtext('nfe:xMun', xml_data['cidade_destinatario'], namespaces) or enderdest.findtext('xMun', xml_data['cidade_destinatario'])
                    xml_data['uf_destinatario'] = enderdest.findtext('nfe:UF', xml_data['uf_destinatario'], namespaces) or enderdest.findtext('UF', xml_data['uf_destinatario'])
                    xml_data['cep_destinatario'] = enderdest.findtext('nfe:CEP', xml_data['cep_destinatario'], namespaces) or enderdest.findtext('CEP', xml_data['cep_destinatario'])
                    
                    # Endereço completo
                    logradouro = enderdest.findtext('nfe:xLgr', '', namespaces) or enderdest.findtext('xLgr', '')
                    numero = enderdest.findtext('nfe:nro', '', namespaces) or enderdest.findtext('nro', '')
                    bairro = enderdest.findtext('nfe:xBairro', '', namespaces) or enderdest.findtext('xBairro', '')
                    xml_data['endereco_destinatario'] = f"{logradouro}, {numero}, {bairro}".strip(', ')
            
            # Dados da transportadora
            transp = inf_nfe.find('nfe:transp', namespaces) or inf_nfe.find('transp')
            if transp is not None:
                transporta = transp.find('nfe:transporta', namespaces) or transp.find('transporta')
                if transporta is not None:
                    xml_data['nome_transportadora'] = transporta.findtext('nfe:xNome', xml_data['nome_transportadora'], namespaces) or transporta.findtext('xNome', xml_data['nome_transportadora'])
                    xml_data['transportadora_cnpj'] = transporta.findtext('nfe:CNPJ', xml_data['transportadora_cnpj'], namespaces) or transporta.findtext('CNPJ', xml_data['transportadora_cnpj'])
            
            # Totais da NFe
            total = inf_nfe.find('nfe:total/nfe:ICMSTot', namespaces) or inf_nfe.find('total/ICMSTot')
            if total is not None:
                valor_total_str = total.findtext('nfe:vNF', '0', namespaces) or total.findtext('vNF', '0')
                try:
                    xml_data['valor_total'] = float(valor_total_str.replace(',', '.'))
                except:
                    xml_data['valor_total'] = 0.0
            
            # Dados de transporte - volumes
            vol_elements = inf_nfe.findall('.//nfe:vol', namespaces) or inf_nfe.findall('.//vol')
            if vol_elements:
                xml_data['quantidade_volumes'] = len(vol_elements)
                
                # Peso dos volumes
                peso_bruto_total = 0.0
                peso_liquido_total = 0.0
                
                for vol in vol_elements:
                    try:
                        peso_bruto = vol.findtext('nfe:pesoB', '0', namespaces) or vol.findtext('pesoB', '0')
                        peso_liquido = vol.findtext('nfe:pesoL', '0', namespaces) or vol.findtext('pesoL', '0')
                        peso_bruto_total += float(peso_bruto.replace(',', '.'))
                        peso_liquido_total += float(peso_liquido.replace(',', '.'))
                    except:
                        pass
                
                xml_data['peso_bruto'] = peso_bruto_total
                xml_data['peso_liquido'] = peso_liquido_total
        
        # Verificar se já existe um XML com a mesma chave para marcar como duplicata
        is_duplicate = False
        if xml_data['chave_nf'] != 'N/A':
            existing_xml = XMLFile.query.filter_by(
                user_id=user_id,
                invoice_key=xml_data['chave_nf']
            ).first()
            
            if existing_xml:
                is_duplicate = True
                logger.info(f"XML duplicado detectado - será gravado como duplicata: {xml_data['chave_nf']}")
        
        # Registrar atividade de upload
        log_user_activity(
            user_id=user_id,
            activity_type='xml_uploaded',
            description=f"XML uploadado: {xml_data.get('numero_nf', 'N/A')} - {xml_data.get('nome_emitente', 'N/A')[:50]}",
            details={
                'filename': xml_data['filename'],
                'invoice_key': xml_data['chave_nf'],
                'numero_nf': xml_data.get('numero_nf'),
                'is_duplicate': is_duplicate
            }
        )
        
        # Criar novo registro no banco usando os nomes corretos dos campos do modelo XMLFile
        xml_file = XMLFile(
            user_id=user_id,
            filename=xml_data['filename'],
            invoice_key=xml_data['chave_nf'],
            file_path=f"uploads/{xml_data['filename']}",
            xml_content=xml_content,
            import_type='upload',
            is_duplicate=is_duplicate,
            
            # Dados básicos da NFe
            cnpj_emitente=xml_data.get('cnpj_emitente', 'N/A')[:14] if xml_data.get('cnpj_emitente') != 'N/A' else None,
            nome_emitente=xml_data.get('nome_emitente', 'N/A')[:255] if xml_data.get('nome_emitente') != 'N/A' else None,
            numero_nf=xml_data.get('numero_nf', 'N/A')[:50] if xml_data.get('numero_nf') != 'N/A' else None,
            serie_nf=xml_data.get('serie_nf', 'N/A')[:10] if xml_data.get('serie_nf') != 'N/A' else None,
            data_emissao=xml_data.get('data_emissao'),
            valor_total=xml_data.get('valor_total'),
            
            # Informações de transporte
            peso_bruto=xml_data.get('peso_bruto'),
            quantidade_volumes=xml_data.get('quantidade_volumes'),
            
            # Dados do remetente (emitente)
            remetente_razao=xml_data.get('nome_emitente', 'N/A')[:255] if xml_data.get('nome_emitente') != 'N/A' else None,
            remetente_cidade=xml_data.get('cidade_emitente', 'N/A')[:100] if xml_data.get('cidade_emitente') != 'N/A' else None,
            remetente_uf=xml_data.get('uf_emitente', 'N/A')[:2] if xml_data.get('uf_emitente') != 'N/A' else None,
            remetente_endereco=xml_data.get('endereco_emitente', 'N/A')[:500] if xml_data.get('endereco_emitente') != 'N/A' else None,
            remetente_cep=xml_data.get('cep_emitente', 'N/A')[:8] if xml_data.get('cep_emitente') != 'N/A' else None,
            
            # Dados do destinatário  
            destinatario_cnpj_cpf=xml_data.get('destinatario_cnpj_cpf', 'N/A')[:14] if xml_data.get('destinatario_cnpj_cpf') != 'N/A' else None,
            destinatario_razao=xml_data.get('nome_destinatario', 'N/A')[:255] if xml_data.get('nome_destinatario') != 'N/A' else None,
            destinatario_cidade=xml_data.get('cidade_destinatario', 'N/A')[:100] if xml_data.get('cidade_destinatario') != 'N/A' else None,
            destinatario_uf=xml_data.get('uf_destinatario', 'N/A')[:2] if xml_data.get('uf_destinatario') != 'N/A' else None,
            destinatario_endereco=xml_data.get('endereco_destinatario', 'N/A')[:500] if xml_data.get('endereco_destinatario') != 'N/A' else None,
            destinatario_cep=xml_data.get('cep_destinatario', 'N/A')[:8] if xml_data.get('cep_destinatario') != 'N/A' else None
        )
        
        db.session.add(xml_file)
        db.session.commit()
        
        return {
            'success': True,
            'is_new': True,
            'xml_file': xml_file,
            'message': 'XML salvo com sucesso'
        }
        
    except Exception as e:
        logger.error(f"Erro ao processar XML {filename}: {e}")
        db.session.rollback()
        return {
            'success': False,
            'is_new': False,
            'xml_file': None,
            'message': f'Erro ao processar XML: {str(e)}'
        }

@app.route('/email-import')
@login_required
@rate_limit_check(max_requests=10, window_minutes=10)
def email_import():
    """Página de configuração para importação via email"""
    return render_template('email_import_redesigned.html',
                         current_user=current_user)

@app.route('/save-email-credentials', methods=['POST'])
@login_required
@rate_limit_check(max_requests=5, window_minutes=10)
def save_email_credentials():
    """Salva as credenciais de email do usuário"""
    try:
        email = request.form.get('email')
        password = request.form.get('password')
        server = request.form.get('server')
        custom_server = request.form.get('custom_server')
        port = int(request.form.get('port', 993))
        ssl = 'ssl' in request.form
        check_interval = int(request.form.get('check_interval', 60))
        
        # Use custom server if specified
        if server == 'custom' and custom_server:
            server = custom_server
        
        # Validate inputs
        if not email or not password or not server:
            flash('Todos os campos obrigatórios devem ser preenchidos', 'error')
            return redirect(url_for('email_import'))
        
        # Test connection before saving
        import imaplib
        
        try:
            if ssl:
                imap = imaplib.IMAP4_SSL(server, port)
            else:
                imap = imaplib.IMAP4(server, port)
            
            imap.login(email, password)
            imap.select('INBOX')
            imap.close()
            imap.logout()
            
        except Exception as e:
            flash(f'Erro ao conectar com o servidor de email: {str(e)}', 'error')
            return redirect(url_for('email_import'))
        
        # Save credentials
        current_user.set_email_credentials(email, password, server, port, ssl)
        current_user.import_email_check_interval = check_interval
        db.session.commit()
        flash('Credenciais de email salvas com sucesso! Importação automática ativa.', 'success')
        
    except Exception as e:
        flash(f'Erro ao salvar credenciais: {str(e)}', 'error')
    
    return redirect(url_for('email_import'))

# Função removida - definição duplicada movida para seção unificada

@app.route('/view-smtp-credentials')
@login_required
def view_smtp_credentials():
    """Visualiza as credenciais SMTP cadastradas"""
    # Se for admin, mostra todos os usuários, senão apenas o próprio
    if current_user.is_admin or current_user.is_super_admin:
        users_with_smtp = User.query.filter(User.smtp_configured == True).all()
    else:
        users_with_smtp = [current_user] if current_user.smtp_configured else []
    
    return render_template('smtp_credentials_view.html', users=users_with_smtp)

# Código limpo - rotas duplicadas resolvidas

@app.route('/view-pop3-credentials')
@login_required
def view_pop3_credentials():
    """Visualiza as credenciais POP3 cadastradas"""
    # Se for admin, mostra todos os usuários, senão apenas o próprio
    if current_user.is_admin or current_user.is_super_admin:
        users_with_pop3 = User.query.filter(User.pop3_configured == True).all()
    else:
        users_with_pop3 = [current_user] if current_user.pop3_configured else []
    
    return render_template('pop3_credentials_view.html', users=users_with_pop3)

@app.route('/test-pop3-connection', methods=['POST'])
@login_required
@rate_limit_check(max_requests=5, window_minutes=10)
def test_pop3_connection():
    """Testa conexão POP3 com as credenciais armazenadas do usuário"""
    try:
        # Verificar se usuário tem POP3 configurado
        if not current_user.has_pop3_configured():
            return jsonify({'success': False, 'message': 'POP3 não configurado. Salve as credenciais primeiro.'})
        
        # Usar credenciais armazenadas do usuário
        email = current_user.pop3_email
        server = current_user.pop3_server
        port = current_user.pop3_port
        use_ssl = current_user.pop3_ssl
        
        # Descriptografar a senha armazenada
        encrypted_password = current_user.pop3_password_hash
        if not encrypted_password:
            return jsonify({'success': False, 'message': 'Senha POP3 não encontrada'})
        
        password = decrypt_email_password(encrypted_password)
        if not password:
            return jsonify({'success': False, 'message': 'Erro ao descriptografar senha POP3'})
        
        if not all([email, server]):
            return jsonify({'success': False, 'message': 'Configurações POP3 incompletas'})
        
        import poplib
        
        # Conectar ao servidor POP3
        logger.info(f"Testando conexão POP3 {server}:{port}")
        
        if use_ssl:
            pop3 = poplib.POP3_SSL(server, port)
        else:
            pop3 = poplib.POP3(server, port)
        
        # Autenticar
        pop3.user(email)
        pop3.pass_(password)
        
        # Obter informações da caixa de entrada
        messages_info = pop3.list()
        messages_count = len(messages_info[1])
        
        if messages_count > 0:
            total_size = sum([int(msg.split()[1]) for msg in messages_info[1]])
        else:
            total_size = 0
        
        pop3.quit()
        
        return jsonify({
            'success': True,
            'message': 'Conexão POP3 realizada com sucesso!',
            'messages_count': messages_count,
            'total_size': total_size,
            'server': f"{server}:{port}",
            'ssl': use_ssl
        })
        
    except Exception as e:
        logger.error(f"Erro ao testar conexão POP3: {e}")
        error_msg = str(e)
        
        # Tratar erros específicos
        if 'authentication failed' in error_msg.lower():
            error_msg = 'Falha na autenticação. Verifique email e senha.'
        elif 'connection refused' in error_msg.lower():
            error_msg = 'Conexão recusada. Verifique servidor e porta.'
        elif 'timeout' in error_msg.lower():
            error_msg = 'Timeout na conexão. Verifique servidor e conectividade.'
        
        return jsonify({'success': False, 'message': error_msg})

# Clean email import system restored

@app.route('/update-pop3-config', methods=['POST'])
@login_required
@rate_limit_check(max_requests=5, window_minutes=10)
def update_pop3_config():
    """Atualiza configurações POP3 do usuário"""
    try:
        data = request.get_json()
        
        # Atualizar configurações POP3
        current_user.pop3_email = data.get('pop3_email')
        current_user.pop3_server = data.get('pop3_server')
        current_user.pop3_port = int(data.get('pop3_port', 995))
        current_user.pop3_ssl = data.get('pop3_ssl', True)
        
        db.session.commit()
        
        return jsonify({
            'success': True, 
            'message': 'Configurações POP3 atualizadas com sucesso'
        })
        
    except Exception as e:
        logger.error(f"Erro ao atualizar configurações POP3: {e}")
        return jsonify({'success': False, 'message': f'Erro: {str(e)}'})

@app.route('/pop3-troubleshoot')
@login_required
def pop3_troubleshoot():
    """Página de resolução de problemas POP3"""
    return render_template('pop3_troubleshoot.html')

@app.route('/save_pop3_credentials', methods=['POST'])
@login_required
@rate_limit_check(max_requests=5, window_minutes=10)  
def save_pop3_credentials():
    """Salva credenciais POP3 do usuário"""
    try:
        password = request.form.get('pop3_password')
        logger.info(f"Password received: {'Yes' if password else 'No'}, Length: {len(password) if password else 0}")
        
        if not password:
            flash('Senha é obrigatória', 'error')
            return redirect(url_for('email_import'))
            
        current_user.pop3_email = request.form.get('pop3_email')
        current_user.pop3_password_hash = encrypt_email_password(password)
        current_user.pop3_server = request.form.get('pop3_server')
        current_user.pop3_port = int(request.form.get('pop3_port', 995))
        current_user.pop3_ssl = 'pop3_ssl' in request.form
        current_user.pop3_configured = True
        
        logger.info(f"Before commit - POP3 configured: {current_user.pop3_configured}")
        logger.info(f"Before commit - Password hash length: {len(current_user.pop3_password) if current_user.pop3_password else 0}")
        
        db.session.commit()
        
        logger.info(f"After commit - POP3 configured: {current_user.pop3_configured}")
        flash('Configurações POP3 salvas com sucesso!', 'success')
        
    except Exception as e:
        logger.error(f"Erro ao salvar credenciais POP3: {e}")
        db.session.rollback()
        flash(f'Erro ao salvar configurações POP3: {str(e)}', 'error')
    
    return redirect(url_for('email_import'))

@app.route('/save_imap_credentials', methods=['POST'])
@login_required
@rate_limit_check(max_requests=5, window_minutes=10)
def save_imap_credentials():
    """Salva credenciais IMAP do usuário"""
    try:
        password = request.form.get('imap_password')
        if not password:
            flash('Senha é obrigatória', 'error')
            return redirect(url_for('email_import'))
            
        current_user.imap_email = request.form.get('imap_email')
        current_user.imap_password = generate_password_hash(password)
        current_user.imap_server = request.form.get('imap_server')
        current_user.imap_port = int(request.form.get('imap_port', 993))
        current_user.imap_ssl = 'imap_ssl' in request.form
        current_user.imap_configured = True
        
        db.session.commit()
        flash('Configurações IMAP salvas com sucesso!', 'success')
        
    except Exception as e:
        logger.error(f"Erro ao salvar credenciais IMAP: {e}")
        flash(f'Erro ao salvar configurações IMAP: {str(e)}', 'error')
    
    return redirect(url_for('email_import'))

@app.route('/save_smtp_credentials', methods=['POST'])
@login_required
@rate_limit_check(max_requests=5, window_minutes=10)
def save_smtp_credentials():
    """Salva credenciais SMTP do usuário"""
    try:
        password = request.form.get('smtp_password')
        if not password:
            flash('Senha é obrigatória', 'error')
            return redirect(url_for('email_import'))
            
        current_user.smtp_email = request.form.get('smtp_email')
        current_user.smtp_password = generate_password_hash(password)
        current_user.smtp_server = request.form.get('smtp_server')
        current_user.smtp_port = int(request.form.get('smtp_port', 587))
        current_user.smtp_ssl = 'smtp_ssl' in request.form
        current_user.smtp_configured = True
        
        db.session.commit()
        flash('Configurações SMTP salvas com sucesso!', 'success')
        
    except Exception as e:
        logger.error(f"Erro ao salvar credenciais SMTP: {e}")
        flash(f'Erro ao salvar configurações SMTP: {str(e)}', 'error')
    
    return redirect(url_for('email_import'))

@app.route('/test-imap-connection', methods=['POST'])
@login_required
@rate_limit_check(max_requests=10, window_minutes=10)
def test_imap_connection():
    """Testa conexão IMAP"""
    try:
        import imaplib
        data = request.get_json()
        
        server = data['server']
        port = int(data['port'])
        email = data['email']
        password = data['password']
        use_ssl = data['ssl']
        
        if use_ssl:
            mail = imaplib.IMAP4_SSL(server, port)
        else:
            mail = imaplib.IMAP4(server, port)
            
        mail.login(email, password)
        mail.select('inbox')
        mail.logout()
        
        return jsonify({'success': True, 'message': 'Conexão IMAP bem-sucedida'})
        
    except Exception as e:
        logger.error(f"Erro ao testar conexão IMAP: {e}")
        return jsonify({'success': False, 'message': str(e)})



@app.route('/test-smtp-connection', methods=['POST'])
@login_required
@rate_limit_check(max_requests=10, window_minutes=10)
def test_smtp_connection():
    """Testa conexão SMTP"""
    try:
        import smtplib
        data = request.get_json()
        
        server = data['server']
        port = int(data['port'])
        email = data['email']
        password = data['password']
        use_ssl = data['ssl']
        
        if use_ssl:
            smtp = smtplib.SMTP_SSL(server, port)
        else:
            smtp = smtplib.SMTP(server, port)
            smtp.starttls()
            
        smtp.login(email, password)
        smtp.quit()
        
        return jsonify({'success': True, 'message': 'Conexão SMTP bem-sucedida'})
        
    except Exception as e:
        logger.error(f"Erro ao testar conexão SMTP: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/check-emails-now', methods=['POST'])
@login_required
@rate_limit_check(max_requests=5, window_minutes=10)
def check_emails_now():
    """Verifica emails manualmente agora"""
    try:
        from email_xml_processor import EmailXMLProcessor
        processor = EmailXMLProcessor(current_user)
        result = processor.process_user_emails()
        
        if result['success']:
            return jsonify({
                'success': True, 
                'message': f"Verificação concluída: {result.get('processed', 0)} emails processados"
            })
        else:
            return jsonify({
                'success': False,
                'message': result.get('message', 'Erro na verificação')
            })
            
    except Exception as e:
        logger.error(f"Erro ao verificar emails: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'})

# Clean email import system - all corrupted route fragments removed


@app.route('/process-email-xmls', methods=['POST'])
@login_required
@rate_limit_check(max_requests=3, window_minutes=10)
def process_email_xmls():
    """Processa XMLs recebidos via email POP3"""
    try:
        if not current_user.has_pop3_configured():
            return jsonify({'success': False, 'message': 'POP3 não configurado'})
        
        # Obter senha do formulário (necessária para autenticação POP3)
        password = request.json.get('password')
        if not password:
            return jsonify({'success': False, 'message': 'Senha necessária para acessar emails'})
        
        from email_xml_processor import EmailXMLProcessor
        
        processor = EmailXMLProcessor(current_user)
        result = processor.process_email_xmls(password)
        
        if result['success']:
            logger.info(f"Processados {result['processed_count']} XMLs via email para usuário {current_user.id}")
            
            return jsonify({
                'success': True,
                'message': f"Processados {result['processed_count']} XMLs com sucesso",
                'processed_count': result['processed_count'],
                'processed_xmls': result['processed_xmls'],
                'total_messages': result['total_messages']
            })
        else:
            error_msg = result['error']
            
            # Tratar erros específicos
            if 'AuthenticationError' in error_msg or 'authentication' in error_msg.lower():
                return jsonify({
                    'success': False, 
                    'message': 'Erro de autenticação: Verifique se a senha do email está correta',
                    'error_type': 'authentication'
                })
            elif 'P_LIST not allowed' in error_msg:
                return jsonify({
                    'success': False, 
                    'message': 'Servidor POP3 temporariamente indisponível. Tente novamente em alguns minutos.',
                    'error_type': 'protocol'
                })
            else:
                return jsonify({'success': False, 'message': error_msg})
            
    except Exception as e:
        logger.error(f"Erro ao processar emails XML: {e}")
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'})

@app.route('/process-xmls-from-email', methods=['POST'])
@login_required
@rate_limit_check(max_requests=5, window_minutes=10)
def process_xmls_from_email():
    """Verifica emails imediatamente e processa XMLs encontrados"""
    try:
        if not current_user.has_pop3_configured():
            return jsonify({'success': False, 'message': 'POP3 não configurado'})
        
        # Obter senha do formulário
        password = request.json.get('password')
        if not password:
            return jsonify({'success': False, 'message': 'Senha necessária para verificar emails'})
        
        from email_xml_processor import EmailXMLProcessor
        
        processor = EmailXMLProcessor(current_user)
        result = processor.process_email_xmls(password)
        
        if result['success']:
            message = f"✅ Verificação concluída!\n\n"
            message += f"📧 Mensagens verificadas: {result.get('total_messages', 0)}\n"
            message += f"📄 XMLs processados: {result['processed_count']}\n"
            
            if result['processed_xmls']:
                message += f"\n📋 XMLs importados:\n"
                for xml in result['processed_xmls'][:5]:  # Mostrar até 5 XMLs
                    message += f"• {xml['filename']} (NF {xml['numero_nf']})\n"
                if len(result['processed_xmls']) > 5:
                    message += f"... e mais {len(result['processed_xmls']) - 5} XMLs"
            
            return jsonify({
                'success': True,
                'message': message,
                'processed_count': result['processed_count'],
                'total_messages': result.get('total_messages', 0)
            })
        else:
            return jsonify({'success': False, 'message': f"❌ Erro: {result['error']}"})
            
    except Exception as e:
        logger.error(f"Erro ao verificar emails: {e}")
        return jsonify({'success': False, 'message': f'❌ Erro interno: {str(e)}'})

@app.route('/remove-pop3-config', methods=['POST'])
@login_required
@rate_limit_check(max_requests=5, window_minutes=10)
def remove_pop3_config():
    """Remove POP3 configuration"""
    try:
        current_user.pop3_server = None
        current_user.pop3_port = 995
        current_user.pop3_email = None
        current_user.pop3_password = None
        current_user.pop3_ssl = True
        current_user.pop3_configured = False
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Configuração POP3 removida com sucesso'})
        
    except Exception as e:
        logger.error(f"Erro ao remover configuração POP3: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'})

@app.route('/remove-smtp-config', methods=['POST'])
@login_required
@rate_limit_check(max_requests=5, window_minutes=10)
def remove_smtp_config():
    """Remove SMTP configuration"""
    try:
        current_user.smtp_server = None
        current_user.smtp_port = 587
        current_user.smtp_email = None
        current_user.smtp_password = None
        current_user.smtp_ssl = True
        current_user.smtp_configured = False
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Configuração SMTP removida com sucesso'})
        
    except Exception as e:
        logger.error(f"Erro ao remover configuração SMTP: {e}")
        return jsonify({'success': False, 'message': 'Erro interno do servidor'})



@app.route('/remove-email-config', methods=['POST'])
@login_required
@rate_limit_check(max_requests=5, window_minutes=10)
def remove_email_config():
    """Remove configuração de email"""
    try:
        current_user.import_email = None
        current_user.import_email_password = None
        current_user.import_email_server = None
        current_user.import_email_port = None
        current_user.import_email_ssl = True
        current_user.import_email_configured = False
        current_user.import_email_last_check = None
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Configuração removida'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/process-email-xml', methods=['POST'])
@rate_limit_check(max_requests=100, window_minutes=60)
def process_email_xml():
    """Processa XMLs recebidos via email (webhook)"""
    try:
        from xml_processor import save_xml_to_database
        
        # Verificar autenticação básica do webhook
        auth_header = request.headers.get('Authorization')
        if not auth_header or auth_header != f"Bearer {os.environ.get('EMAIL_WEBHOOK_SECRET', 'default_secret')}":
            return jsonify({'error': 'Unauthorized'}), 401
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Extrair dados do email
        user_id = data.get('user_id')
        sender_email = data.get('sender')
        attachments = data.get('attachments', [])
        
        if not user_id:
            return jsonify({'error': 'user_id required'}), 400
        
        # Verificar se usuário existe
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        processed_count = 0
        error_count = 0
        
        for attachment in attachments:
            filename = attachment.get('filename', '')
            content = attachment.get('content', '')
            
            # Verificar se é arquivo XML
            if not filename.lower().endswith('.xml'):
                continue
            
            try:
                # Decodificar conteúdo base64
                import base64
                xml_content = base64.b64decode(content).decode('utf-8')
                
                # Salvar no banco
                xml_file = save_xml_to_database(
                    user_id=user_id,
                    xml_content=xml_content,
                    filename=filename,
                    import_type='EMAIL'
                )
                
                processed_count += 1
                logger.info(f"XML recebido via email: {filename} - Usuário: {user_id}")
                
            except Exception as e:
                logger.error(f"Erro ao processar XML via email {filename}: {e}")
                error_count += 1
        
        return jsonify({
            'status': 'success',
            'processed': processed_count,
            'errors': error_count
        })
        
    except Exception as e:
        logger.error(f"Erro no webhook de email: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/pricing')
@rate_limit_check(max_requests=30, window_minutes=10)
def pricing():
    """Página de preços"""
    pricing_data = {
        'xml_price': 'R$ 0,10',
        'danfe_price': 'Grátis',
        'labels_price': 'R$ 49,90',
        'minimum_charge': 'R$ 19,90'
    }
    return render_template('pricing.html', **pricing_data)

@app.route('/test-automation')
@login_required
def test_automation():
    """Testar conexão do sistema de automação"""
    try:
        from automation_fixed import InvoiceDownloader
        
        downloader = InvoiceDownloader()
        result = downloader.test_connection()
        
        if result.get('success'):
            flash('Conexão testada com sucesso! Sistema funcionando normalmente.', 'success')
        else:
            flash(f'Erro na conexão: {result.get("error", "Erro desconhecido")}', 'error')
            
    except Exception as e:
        logger.error(f"Error testing automation: {str(e)}")
        flash(f'Erro ao testar sistema: {str(e)}', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/downloads/<filename>')
@login_required  
def serve_download_file(filename):
    """Serve arquivos baixados"""
    try:
        downloads_dir = os.path.join(os.getcwd(), 'downloads')
        return send_from_directory(downloads_dir, filename, as_attachment=True)
    except Exception as e:
        logger.error(f"Error serving file {filename}: {str(e)}")
        flash('Arquivo não encontrado.', 'error')
        return redirect(url_for('meus_xmls'))

@app.route('/generate-danfe/<filename>')
@login_required
def generate_danfe_simple(filename):
    """Gera DANFE diretamente do arquivo baixado via GET"""
    try:
        logger.info(f"DANFE request - filename: {filename}")
        
        if not filename:
            logger.error("Nome do arquivo não fornecido")
            flash('Nome do arquivo não fornecido.', 'error')
            return redirect(url_for('xml_download'))
        
        # Caminho do arquivo XML
        xml_path = os.path.join(os.getcwd(), 'downloads', filename)
        logger.info(f"XML path: {xml_path}")
        logger.info(f"XML exists: {os.path.exists(xml_path)}")
        
        if not os.path.exists(xml_path):
            logger.error(f"Arquivo XML não encontrado: {xml_path}")
            flash('Arquivo XML não encontrado.', 'error')
            return redirect(url_for('xml_download'))
        
        # Gerar DANFE com layout SEFAZ oficial
        logger.info("Iniciando geração DANFE SEFAZ...")
        from danfe_sefaz import generate_sefaz_danfe_from_file
        danfe_path = generate_sefaz_danfe_from_file(xml_path)
        logger.info(f"DANFE path resultado: {danfe_path}")
        
        if danfe_path and os.path.exists(danfe_path):
            logger.info(f"DANFE gerado com sucesso: {danfe_path}")
            return send_from_directory(
                os.path.dirname(danfe_path), 
                os.path.basename(danfe_path), 
                as_attachment=True,
                download_name=f"DANFE_{filename.replace('.xml', '.pdf')}"
            )
        else:
            logger.error(f"Falha na geração DANFE - path: {danfe_path}")
            flash('Erro ao gerar DANFE. Verifique se o XML é válido.', 'error')
            return redirect(url_for('xml_download'))
            
    except Exception as e:
        logger.error(f"Error generating DANFE: {str(e)}", exc_info=True)
        flash(f'Erro ao gerar DANFE: {str(e)}', 'error')
        return redirect(url_for('xml_download'))

@app.route('/download-xml/<int:xml_id>')
@login_required
@rate_limit_check(max_requests=200, window_minutes=15)
def download_xml(xml_id):
    """Download arquivo XML específico com isolamento de dados"""
    from flask import send_file
    import io
    
    # Validar acesso ao XML com isolamento de dados
    xml_query = XMLFile.query.filter_by(id=xml_id, user_id=current_user.id)
    xml_query = DataIsolationManager.filter_user_xmls(xml_query, current_user.id)
    xml_record = xml_query.first()
    
    if not xml_record:
        SecurityManager.log_security_event("UNAUTHORIZED_XML_ACCESS", current_user.id, f"XML ID: {xml_id}")
        flash('XML não encontrado.', 'error')
        return redirect(url_for('meus_xmls'))
    
    # Validar acesso do usuário ao XML
    if not SecurityManager.validate_xml_access(xml_record):
        SecurityManager.log_security_event("XML_ACCESS_DENIED", current_user.id, f"XML ID: {xml_id}")
        abort(403)
    
    # Criar arquivo em memória
    xml_io = io.BytesIO(xml_record.xml_content.encode('utf-8'))
    xml_io.seek(0)
    
    return send_file(
        xml_io,
        as_attachment=True,
        download_name=f"{xml_record.invoice_key}.xml",
        mimetype='application/xml'
    )

@app.route('/generate-danfe/<int:xml_id>')
@login_required
def generate_danfe_route(xml_id):
    """Gera e baixa DANFE para um XML específico"""
    # XMLFile removido - usando XMLFile
    from danfe_generator import DANFEGenerator
    from flask import send_file
    import io
    
    xml_record = XMLFile.query.filter_by(id=xml_id, user_id=current_user.id).first()
    
    if not xml_record:
        flash('XML não encontrado.', 'error')
        return redirect(url_for('meus_xmls'))
    
    try:
        # Gerar DANFE
        danfe_generator = DANFEGenerator()
        
        # Criar um arquivo temporário para o DANFE
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_file:
            temp_path = temp_file.name
        
        if danfe_generator.generate_danfe(xml_record.xml_content, temp_path):
            # Ler o arquivo gerado
            with open(temp_path, 'rb') as f:
                pdf_data = f.read()
            
            # Remover arquivo temporário
            import os
            os.unlink(temp_path)
            
            pdf_io = io.BytesIO(pdf_data)
            pdf_io.seek(0)
            
            return send_file(
                pdf_io,
                as_attachment=True,
                download_name=f"DANFE_{xml_record.invoice_key}.pdf",
                mimetype='application/pdf'
            )
        else:
            flash('Erro ao gerar DANFE.', 'error')
            
    except Exception as e:
        logger.error(f"Error generating DANFE: {str(e)}")
        flash('Erro ao gerar DANFE.', 'error')
    
    return redirect(url_for('meus_xmls'))

@app.route('/generate-label/<int:xml_id>')
@login_required
@rate_limit_check(max_requests=50, window_minutes=15)
def generate_label_route(xml_id):
    """Gera e baixa etiqueta de transporte para um XML específico com isolamento de dados"""
    try:
        # Validar acesso ao XML com isolamento de dados
        xml_query = XMLFile.query.filter_by(id=xml_id, user_id=current_user.id)
        xml_query = DataIsolationManager.filter_user_xmls(xml_query, current_user.id)
        xml_record = xml_query.first()
        
        if not xml_record:
            SecurityManager.log_security_event("UNAUTHORIZED_LABEL_ACCESS", current_user.id, f"XML ID: {xml_id}")
            flash('XML não encontrado.', 'error')
            return redirect(url_for('meus_xmls'))
        
        # Validar acesso do usuário ao XML
        if not SecurityManager.validate_xml_access(xml_record):
            SecurityManager.log_security_event("LABEL_ACCESS_DENIED", current_user.id, f"XML ID: {xml_id}")
            abort(403)
        
        # Usar dados do XML encontrado
        xml_content = xml_record.xml_content
        invoice_key = xml_record.invoice_key
        
        # Verificar acesso ao módulo de etiquetas
        if not current_user.has_labels_access():
            SecurityManager.log_security_event("LABELS_ACCESS_DENIED", current_user.id, f"Trial active: {current_user.is_labels_trial_active()}, Subscription active: {current_user.labels_subscription_active}")
            flash('Você precisa adquirir o módulo de etiquetas para acessar esta funcionalidade.', 'warning')
            return redirect(url_for('labels_module'))
        
        # Verificar módulo de etiquetas para cobrança
        labels_module = ServiceModule.query.filter_by(name='Etiquetas de Transporte').first()
        if not labels_module:
            SecurityManager.log_security_event("LABELS_MODULE_NOT_FOUND", current_user.id)
            flash('Módulo de etiquetas não disponível.', 'error')
            return redirect(url_for('meus_xmls'))
        
        # Gerar etiqueta personalizada
        pedido_number = request.args.get('pedido', invoice_key[:5])
        area_code = request.args.get('area', '01')
        company_name = request.args.get('empresa', 'SUA EMPRESA')
        
        # Extrair dados do XML primeiro
        from xml_processor import extract_xml_data
        xml_data = extract_xml_data(xml_content)
        
        # Usar configurações do usuário para personalização
        company_name = current_user.company_name or 'SUA EMPRESA'
        if xml_record:
            # Usar nome do emitente se usuário não configurou empresa
            if not current_user.company_name:
                company_name = xml_data.get('nome_emitente', company_name)
        
        # Usar configurações salvas do usuário
        area_code = current_user.default_area_code or '01'
        logo_path = current_user.company_logo_path
        
        # Verificar quantidade de volumes (já extraído acima)
        volumes_qty = xml_data.get('quantidade_volumes', 1)
        
        # Obter configurações de papel do usuário (padrão: 100x150mm)
        paper_width = getattr(current_user, 'paper_width_mm', 100)
        paper_height = getattr(current_user, 'paper_height_mm', 150)
        
        # Verificar se precisa gerar múltiplas etiquetas (mais de 1 volume)
        if volumes_qty > 1:
            # Gerar etiquetas multi-volume
            from responsive_label_generator import generate_multiple_responsive_labels_from_volumes, merge_labels_into_single_pdf
            
            # Criar configuração de volumes baseada na quantidade real
            volumes_config = []
            peso_total = xml_data.get('peso_bruto', 0.0)
            peso_por_volume = peso_total / volumes_qty if volumes_qty > 0 else 0.0
            
            for i in range(1, volumes_qty + 1):
                volumes_config.append({
                    'peso': peso_por_volume,
                    'pedido': f'{pedido_number}-{i}'
                })
            
            labels = generate_multiple_responsive_labels_from_volumes(
                xml_record=xml_record,
                volumes_config=volumes_config,
                company_name=company_name,
                company_logo_path=logo_path,
                paper_width_mm=paper_width,
                paper_height_mm=paper_height,
                area_code=area_code
            )
            
            # Filtrar labels válidos
            valid_labels = [l for l in labels if l.get('pdf_buffer') is not None]
            
            if not valid_labels:
                raise Exception(f"Nenhuma etiqueta válida gerada para {volumes_qty} volumes")
            
            # Mesclar em PDF único
            label_buffer = merge_labels_into_single_pdf(valid_labels)
            filename = f"etiquetas_transporte_{invoice_key}_{volumes_qty}volumes.pdf"
            
        else:
            # Gerar etiqueta única
            from responsive_label_generator import generate_responsive_label_from_database_xml
            
            label_buffer = generate_responsive_label_from_database_xml(
                xml_record=xml_record,
                pedido_number=pedido_number,
                area_code=area_code,
                company_name=company_name,
                company_logo_path=logo_path,
                paper_width_mm=paper_width,
                paper_height_mm=paper_height
            )
            filename = f"etiqueta_transporte_{invoice_key}.pdf"
        
        # Registrar uso do módulo de etiquetas (sem cobrança adicional - incluído na assinatura)
        if labels_module:
            usage_record = UsageRecord(
                user_id=current_user.id,
                module_id=labels_module.id,
                quantity=volumes_qty,  # Registrar quantidade real de volumes
                cost=0.0,  # Incluído na assinatura mensal
                description=f"Etiquetas geradas para XML {invoice_key[:10]}... ({volumes_qty} volumes)"
            )
            
            db.session.add(usage_record)
            db.session.commit()
        
        # Marcar como etiqueta gerada
        if xml_record:
            xml_record.label_generated = True
            db.session.commit()
        
        # Retornar arquivo para impressão no navegador
        response = make_response(label_buffer.getvalue())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'inline; filename="{filename}"'
        response.headers['X-Frame-Options'] = 'ALLOWALL'
        return response
        
    except Exception as e:
        logger.error(f"Erro ao gerar etiqueta: {e}")
        flash('Erro ao gerar etiqueta. Tente novamente.', 'error')
        return redirect(url_for('meus_xmls'))

@app.route('/bulk-generate-labels', methods=['POST'])
@login_required
def bulk_generate_labels_route():
    """Gera etiquetas em lote"""
    # Verificar se usuário tem saldo para acessar módulos premium
    if current_user.current_balance < 49.90 and current_user.trial_expires_at < datetime.now():
        flash('Você precisa adquirir o módulo de etiquetas para acessar esta funcionalidade.', 'warning')
        return redirect(url_for('labels_module'))
    
    xml_ids = request.form.getlist('xml_ids')
    
    if not xml_ids:
        flash('Selecione pelo menos um XML para gerar etiquetas.', 'warning')
        return redirect(url_for('labels_module'))
    
    try:
        from label_generator import bulk_generate_labels
        
        xml_ids = [int(xml_id) for xml_id in xml_ids]
        result = bulk_generate_labels(xml_ids)
        
        if result.get('success'):
            flash(f'Etiquetas geradas com sucesso! {result.get("count", 0)} etiquetas criadas.', 'success')
            return redirect(result.get('download_url', url_for('labels_module')))
        else:
            flash(f'Erro ao gerar etiquetas: {result.get("error")}', 'error')
            
    except Exception as e:
        logger.error(f"Error bulk generating labels: {str(e)}")
        flash('Erro ao gerar etiquetas em lote.', 'error')
    
    return redirect(url_for('labels_module'))

# ==================== ROTAS DE PAGAMENTO STRIPE ====================

@app.route('/creditos-xml')
@login_required
def creditos_xml():
    """Dashboard completo de créditos XML do usuário"""
    try:
        from stripe_pricing_system import get_user_xml_credits, get_xml_usage_stats
        from package_models import FeatureUsage, StripeTransaction
        from datetime import datetime, timedelta
        from sqlalchemy import desc, extract, func
        
        # Obter créditos atuais
        current_credits = get_user_xml_credits(current_user.id)
        
        # Obter estatísticas de uso
        stats = get_xml_usage_stats(current_user.id)
        
        # Histórico de compras (últimas 20 transações)
        purchase_history = db.session.query(StripeTransaction)\
            .filter_by(user_id=current_user.id, status='paid')\
            .order_by(desc(StripeTransaction.created_at))\
            .limit(20).all()
        
        # Histórico de uso (últimos 50 downloads)
        usage_history = db.session.query(FeatureUsage)\
            .filter_by(user_id=current_user.id, feature_key='xml_download')\
            .order_by(desc(FeatureUsage.created_at))\
            .limit(50).all()
        
        # Relatório mensal dos últimos 12 meses
        monthly_summary = []
        current_date = datetime.now()
        
        for i in range(12):
            month_date = current_date - timedelta(days=30*i)
            month_start = month_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            if month_date.month == 12:
                next_month = month_date.replace(year=month_date.year + 1, month=1, day=1)
            else:
                next_month = month_date.replace(month=month_date.month + 1, day=1)
            
            # Compras do mês
            purchased = db.session.query(func.sum(StripeTransaction.credits_added))\
                .filter(
                    StripeTransaction.user_id == current_user.id,
                    StripeTransaction.status == 'paid',
                    StripeTransaction.created_at >= month_start,
                    StripeTransaction.created_at < next_month
                ).scalar() or 0
            
            # Uso do mês
            used = db.session.query(func.sum(FeatureUsage.credits_consumed))\
                .filter(
                    FeatureUsage.user_id == current_user.id,
                    FeatureUsage.feature_key == 'xml_download',
                    FeatureUsage.created_at >= month_start,
                    FeatureUsage.created_at < next_month
                ).scalar() or 0
            
            monthly_summary.append({
                'month_name': month_date.strftime('%B %Y'),
                'purchased': int(purchased),
                'used': int(used)
            })
        
        return render_template('creditos_xml.html',
                             current_credits=current_credits,
                             stats=stats,
                             purchase_history=purchase_history,
                             usage_history=usage_history,
                             monthly_summary=monthly_summary)
    
    except Exception as e:
        logger.error(f"Erro ao carregar dashboard de créditos XML: {str(e)}")
        flash('Erro ao carregar informações de créditos.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/extrato-creditos')
@login_required  
@rate_limit_check(max_requests=60, window_minutes=15)
def extrato_creditos():
    """Página de histórico de créditos com extrato bancário detalhado"""
    try:
        from stripe_pricing_system import get_user_xml_credits
        from package_models import FeatureUsage
        from datetime import datetime, timedelta
        from sqlalchemy import desc, func, or_
        
        # Obter saldo atual
        current_credits = get_user_xml_credits(current_user.id)
        
        # Obter transações Stripe (compras) dos últimos 90 dias
        ninety_days_ago = datetime.utcnow() - timedelta(days=90)
        stripe_transactions = db.session.query(StripeTransaction.id, StripeTransaction.user_id, 
                                             StripeTransaction.amount_brl, StripeTransaction.credits_purchased,
                                             StripeTransaction.status, StripeTransaction.created_at,
                                             StripeTransaction.completed_at)\
            .filter(StripeTransaction.user_id == current_user.id)\
            .filter(StripeTransaction.created_at >= ninety_days_ago)\
            .filter(or_(
                StripeTransaction.status == 'paid',
                StripeTransaction.status == 'completed'
            ))\
            .order_by(desc(StripeTransaction.created_at))\
            .all()
        
        # Obter histórico de uso dos últimos 90 dias
        usage_transactions = db.session.query(FeatureUsage)\
            .filter(FeatureUsage.user_id == current_user.id)\
            .filter(FeatureUsage.feature_key == 'xml_download')\
            .filter(FeatureUsage.created_at >= ninety_days_ago)\
            .order_by(desc(FeatureUsage.created_at))\
            .all()
        
        # Calcular totais (dados agora são tuplas)
        total_purchased = sum([t[3] or 0 for t in stripe_transactions])  # credits_purchased é o 4º campo
        total_used = sum([u.credits_consumed or 0 for u in usage_transactions])
        
        # Obter dados dos últimos 30 dias para resumo mensal
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        monthly_purchased = sum([
            t[3] or 0 for t in stripe_transactions 
            if t[5] >= thirty_days_ago  # created_at é o 6º campo
        ])
        monthly_used = sum([
            u.credits_consumed or 0 for u in usage_transactions 
            if u.created_at >= thirty_days_ago
        ])
        
        # Renderizar template com dados do extrato bancário
        return render_template('extrato_creditos_bancario.html',
                             current_user=current_user,
                             purchase_transactions=stripe_transactions,
                             usage_transactions=usage_transactions,
                             total_purchased=int(total_purchased),
                             total_used=int(total_used),
                             monthly_purchased=int(monthly_purchased),
                             monthly_used=int(monthly_used))
        
    except Exception as e:
        logger.error(f"Erro ao carregar extrato de créditos: {str(e)}")
        flash('Erro ao carregar extrato de créditos.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/comprar-creditos-xml')
@login_required
def comprar_creditos_xml():
    """Página para compra de créditos XML com integração Stripe"""
    try:
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        
        # Obter saldo atual do usuário
        from credit_system_fixed import get_user_xml_balance
        xml_balance = get_user_xml_balance(current_user.id)
        
        # Usar produtos oficiais do Stripe configurados diretamente
        xml_products = [
            {
                'id': 'starter',
                'name': 'Starter - 100 Créditos XML',
                'description': 'Ideal para uso ocasional',
                'amount': 10.00,
                'currency': 'BRL',
                'credits': 100,
                'price_id': 'price_1RcB6ZKpjVGFiyHCqBx0uFom',
                'popular': False
            },
            {
                'id': 'professional', 
                'name': 'Professional - 500 Créditos XML',
                'description': 'Para empresas de médio porte',
                'amount': 40.00,
                'currency': 'BRL',
                'credits': 500,
                'price_id': 'price_1RcB6aKpjVGFiyHCnzyt2Gkg',
                'popular': True
            },
            {
                'id': 'enterprise',
                'name': 'Enterprise - 1000 Créditos XML',
                'description': 'Para grandes volumes',
                'amount': 70.00,
                'currency': 'BRL',
                'credits': 1000,
                'price_id': 'price_1RcB6aKpjVGFiyHCsOIWwjsH',
                'popular': False
            },
            {
                'id': 'corporate',
                'name': 'Corporate - 2000 Créditos XML',
                'description': 'Para operações em larga escala',
                'amount': 120.00,
                'currency': 'BRL',
                'credits': 2000,
                'price_id': 'price_1RcB6aKpjVGFiyHCjEAUSie0',
                'popular': False
            }
        ]
        
        # Log dos produtos configurados para debug
        logger.info(f"Produtos XML configurados: {len(xml_products)} pacotes")
        

        
        return render_template('comprar_creditos_xml.html',
                             xml_balance=xml_balance,
                             xml_products=xml_products)
        
    except Exception as e:
        logger.error(f"Erro na página de compra de créditos: {e}")
        flash('Erro ao carregar página de compra de créditos', 'error')
        return redirect(url_for('dashboard'))

@app.route('/create-xml-checkout-session', methods=['POST'])
@login_required
@rate_limit_check(max_requests=10, window_minutes=5)
def create_xml_checkout_session():
    """Criar sessão de checkout Stripe para compra de créditos XML"""
    try:
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        
        # Obter dados do formulário
        product_type = request.form.get('product_type', 'xml_credits')
        product_id = request.form.get('product_id')
        amount = float(request.form.get('amount', 0))
        credits = int(request.form.get('credits', 0))
        price_id = request.form.get('price_id')
        
        if amount <= 0 or credits <= 0:
            flash('Dados inválidos para compra', 'error')
            return redirect(url_for('comprar_creditos_xml'))
        
        # Criar sessão de checkout
        if price_id:
            # Usar price_id existente do Stripe
            line_items = [{
                'price': price_id,
                'quantity': 1,
            }]
        else:
            # Criar price dinâmico
            line_items = [{
                'price_data': {
                    'currency': 'brl',
                    'product_data': {
                        'name': f'Pacote {credits} Créditos XML',
                        'description': f'{credits} downloads XML para CROSS XML Downloader PRO',
                    },
                    'unit_amount': int(amount * 100),  # Converter para centavos
                },
                'quantity': 1,
            }]
        
        session = stripe.checkout.Session.create(
            customer_email=current_user.email,
            payment_method_types=['card'],
            mode='payment',
            line_items=line_items,
            success_url=url_for('purchase_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('comprar_creditos_xml', _external=True),
            metadata={
                'user_id': str(current_user.id),
                'product_type': product_type,
                'product_id': product_id,
                'credits': str(credits),
                'amount': str(amount)
            }
        )
        
        logger.info(f"Sessão de checkout criada para usuário {current_user.id}: {session.id}")
        return redirect(session.url)
        
    except stripe.error.StripeError as e:
        logger.error(f"Erro do Stripe: {e}")
        flash('Erro ao processar pagamento. Tente novamente.', 'error')
        return redirect(url_for('comprar_creditos_xml'))
    except Exception as e:
        logger.error(f"Erro ao criar checkout: {e}")
        flash('Erro interno. Tente novamente.', 'error')
        return redirect(url_for('comprar_creditos_xml'))

@app.route('/purchase-success')
@login_required
def purchase_success():
    """Página de sucesso após compra"""
    session_id = request.args.get('session_id')
    if not session_id:
        flash('Sessão inválida', 'error')
        return redirect(url_for('dashboard'))
    
    try:
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        
        # Recuperar sessão do Stripe
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            credits = int(session.metadata.get('credits', 0))
            amount = float(session.metadata.get('amount', 0))
            
            # Adicionar créditos ao usuário
            from credit_system_fixed import get_user_xml_balance
            
            # Criar registro de crédito manualmente
            from models import CreditBalance
            try:
                credit_record = CreditBalance(
                    user_id=current_user.id,
                    amount=credits,
                    transaction_type='purchase',
                    description=f'Compra via Stripe - {credits} créditos XML',
                    transaction_id=session_id
                )
                db.session.add(credit_record)
                db.session.commit()
                success = True
            except Exception as e:
                logger.error(f"Erro ao adicionar créditos: {e}")
                success = False
            
            if success:
                flash(f'Compra realizada com sucesso! {credits} créditos XML adicionados à sua conta.', 'success')
                
                # Log da atividade
                log_user_activity(
                    user_id=current_user.id,
                    activity_type='credits_purchased',
                    description=f'Compra de {credits} créditos XML - R$ {amount:.2f}'
                )
                
                return render_template('purchase_success.html', 
                                     credits=credits, 
                                     amount=amount,
                                     session_id=session_id)
            else:
                flash('Erro ao processar créditos. Entre em contato com o suporte.', 'error')
        else:
            flash('Pagamento não confirmado', 'warning')
            
    except Exception as e:
        logger.error(f"Erro ao processar sucesso da compra: {e}")
        flash('Erro ao confirmar compra. Entre em contato com o suporte.', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/create-labels-subscription', methods=['POST'])
@login_required
@rate_limit_check(max_requests=5, window_minutes=10)
def create_labels_subscription():
    """Criar assinatura do módulo de etiquetas via Stripe"""
    try:
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        
        # Criar ou obter produto para etiquetas de transporte
        try:
            # Tentar obter produto existente
            product = stripe.Product.retrieve('prod_SSVViDPzXYZHhO')
        except stripe.error.InvalidRequestError:
            # Criar produto se não existir
            product = stripe.Product.create(
                id='prod_SSVViDPzXYZHhO',
                name='Etiquetas de Transporte Integrada',
                description='Módulo mensal para geração ilimitada de etiquetas de transporte profissionais',
                type='service'
            )
        
        # Buscar preços existentes para o produto oficial
        try:
            prices = stripe.Price.list(
                product='prod_SSVViDPzXYZHhO',
                active=True,
                type='recurring'
            )
            
            if prices.data:
                # Usar o primeiro preço ativo encontrado
                price_id = prices.data[0].id
                logger.info(f"Usando preço existente para produto oficial: {price_id}")
            else:
                # Criar novo preço se não existir
                price = stripe.Price.create(
                    product='prod_SSVViDPzXYZHhO',
                    unit_amount=4990,  # R$ 49,90 em centavos
                    currency='brl',
                    recurring={'interval': 'month'},
                    nickname='Etiquetas de Transporte - Mensal'
                )
                price_id = price.id
                logger.info(f"Novo preço criado para produto oficial: {price_id}")
                
        except stripe.error.StripeError as e:
            logger.error(f"Erro ao buscar/criar preço: {e}")
            # Usar preço padrão como fallback
            price_id = 'price_1RcCXgKpjVGFiyHCHKZY8Uth'
        
        # Criar sessão de checkout Stripe para assinatura
        session = stripe.checkout.Session.create(
            customer_email=current_user.email,
            payment_method_types=['card'],
            mode='subscription',
            line_items=[{
                'price': price_id,
                'quantity': 1,
            }],
            success_url=url_for('labels_subscription_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('labels_module', _external=True),
            metadata={
                'user_id': str(current_user.id),
                'product_type': 'labels_subscription',
                'feature': 'transport_labels'
            },
            subscription_data={
                'metadata': {
                    'user_id': str(current_user.id),
                    'feature': 'transport_labels'
                }
            }
        )
        
        app.logger.info(f"Sessão de checkout criada: {session.id} para usuário {current_user.id}")
        return redirect(session.url, code=303)
        
    except Exception as e:
        app.logger.error(f"Erro ao criar assinatura Stripe: {str(e)}")
        flash('Erro ao processar pagamento. Tente novamente.', 'error')
        return redirect(url_for('labels_module'))

@app.route('/create-checkout-session', methods=['POST'])
@login_required
@rate_limit_check(max_requests=10, window_minutes=5)
def create_checkout_session():
    """Criar sessão de checkout Stripe usando produtos reais da API"""
    try:
        # Obter dados do request (aceitar JSON ou form data)
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        package_id = data.get('package_id')
        
        if not package_id:
            return jsonify({'error': 'Package ID é obrigatório'}), 400
        
        # Mapear pacotes para produtos Stripe reais com preços atualizados
        stripe_products = {
            'starter': {
                'price_id': 'price_1RcB6ZKpjVGFiyHCqBx0uFom',  # 100 créditos XML - R$ 10,00
                'credits': 100,
                'name': 'Pacote Starter - 100 Créditos XML'
            },
            'professional': {
                'price_id': 'price_1RcB6aKpjVGFiyHCnzyt2Gkg',  # 500 créditos XML - R$ 40,00
                'credits': 500,
                'name': 'Pacote Professional - 500 Créditos XML'
            },
            'enterprise': {
                'price_id': 'price_1RcB6aKpjVGFiyHCsOIWwjsH',  # 1000 créditos XML - R$ 70,00
                'credits': 1000,
                'name': 'Pacote Enterprise - 1000 Créditos XML'
            },
            'corporate': {
                'price_id': 'price_1RcB6aKpjVGFiyHCjEAUSie0',  # 2000 créditos XML - R$ 120,00
                'credits': 2000,
                'name': 'Pacote Corporate - 2000 Créditos XML'
            }
        }
        
        product = stripe_products.get(package_id)
        if not product:
            return jsonify({'error': 'Pacote inválido'}), 400
        
        # Criar sessão de checkout usando produto Stripe real
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        
        success_url = url_for('payment_success_simple', _external=True) + '?session_id={CHECKOUT_SESSION_ID}'
        cancel_url = url_for('comprar_creditos_simple', _external=True)
        
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price': product['price_id'],
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=current_user.email,
            metadata={
                'user_id': str(current_user.id),
                'package_id': package_id,
                'credits': str(product['credits'])
            }
        )
        
        return jsonify({'checkout_url': checkout_session.url})
            
    except Exception as e:
        logger.error(f"Erro ao criar sessão de checkout: {str(e)}")
        return jsonify({'error': 'Erro interno do servidor'}), 500

@app.route('/payment-success-simple')
@login_required
def payment_success_simple():
    """Página simplificada de sucesso do pagamento"""
    session_id = request.args.get('session_id')
    
    if not session_id:
        flash('Sessão de pagamento não encontrada.', 'error')
        return redirect(url_for('dashboard'))
    
    # Verificar sessão no Stripe
    try:
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid':
            # Extrair créditos dos metadados
            credits = int(session.metadata.get('credits', 0))
            
            if credits > 0:
                # Adicionar créditos ao usuário usando sistema simplificado
                from simple_credit_system import add_xml_credits
                
                success = add_xml_credits(
                    current_user.id, 
                    credits, 
                    f"Compra via Stripe - {credits} créditos XML"
                )
                
                if success:
                    flash(f'Pagamento realizado com sucesso! {credits} créditos XML foram adicionados ao seu saldo.', 'success')
                else:
                    flash('Pagamento processado, mas houve erro ao adicionar créditos. Contate o suporte.', 'warning')
            else:
                flash('Pagamento processado com sucesso!', 'success')
        else:
            flash('Pagamento ainda não foi processado.', 'warning')
            
    except Exception as e:
        logger.error(f"Erro ao verificar pagamento: {e}")
        flash('Erro ao verificar status do pagamento.', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/comprar-creditos-simple')
@login_required
def comprar_creditos_simple():
    """Página simplificada para compra de créditos XML"""
    try:
        # Obter saldo atual usando sistema simplificado
        from simple_credit_system import get_user_xml_balance
        xml_balance = get_user_xml_balance(current_user.id)
        
        return render_template('comprar_creditos_simple.html',
                             xml_balance=xml_balance)
        
    except Exception as e:
        logger.error(f"Erro na página de compra de créditos: {e}")
        flash('Erro ao carregar página de compra de créditos', 'error')
        return redirect(url_for('dashboard'))

@app.route('/labels-subscription-success')
@login_required
@rate_limit_check(max_requests=10, window_minutes=5)
def labels_subscription_success():
    """Página de sucesso da assinatura do módulo de etiquetas"""
    try:
        session_id = request.args.get('session_id')
        if not session_id:
            flash('Sessão de pagamento não encontrada.', 'error')
            return redirect(url_for('labels_module'))
        
        # Verificar sessão no Stripe
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        session = stripe.checkout.Session.retrieve(session_id)
        
        if session.payment_status == 'paid' and session.metadata.get('product_type') == 'labels_subscription':
            from package_models import UserSubscription
            
            # Verificar se já existe assinatura ativa
            existing_subscription = UserSubscription.query.filter_by(
                user_id=current_user.id,
                status='active'
            ).filter(
                UserSubscription.feature_key.like('%labels%')
            ).first()
            
            if not existing_subscription:
                # Criar nova assinatura no banco de dados
                subscription = UserSubscription()
                subscription.user_id = current_user.id
                subscription.stripe_subscription_id = session.subscription
                subscription.feature_key = 'transport_labels'
                subscription.status = 'active'
                subscription.starts_at = datetime.utcnow()
                subscription.expires_at = datetime.utcnow() + timedelta(days=30)  # 30 dias
                subscription.auto_renew = True
                
                db.session.add(subscription)
                db.session.commit()
                
                app.logger.info(f"Assinatura de etiquetas criada para usuário {current_user.id}")
                flash('Assinatura do módulo de etiquetas ativada com sucesso! Agora você pode gerar etiquetas ilimitadas.', 'success')
            else:
                flash('Você já possui uma assinatura ativa do módulo de etiquetas.', 'info')
        else:
            flash('Pagamento não confirmado. Tente novamente ou contate o suporte.', 'error')
            
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        app.logger.error(f"Erro no sucesso da assinatura: {str(e)}")
        flash('Erro ao processar confirmação de pagamento.', 'error')
        return redirect(url_for('labels_module'))

# Webhook já existe em outra parte do código - removido para evitar duplicação

@app.route('/payment-success')
@login_required
@rate_limit_check(max_requests=20, window_minutes=10)
def payment_success():
    """Página de sucesso do pagamento com isolamento de dados"""
    session_id = request.args.get('session_id')
    
    # Sanitizar entrada de dados
    session_id = SecurityManager.sanitize_input(session_id) if session_id else None
    
    if not session_id:
        SecurityManager.log_security_event("PAYMENT_SUCCESS_NO_SESSION", current_user.id)
        flash('Sessão de pagamento não encontrada.', 'error')
        return redirect(url_for('dashboard'))
    
    # Buscar transação com isolamento de dados por usuário
    transaction_query = StripeTransaction.query.filter_by(
        stripe_session_id=session_id,
        user_id=current_user.id
    )
    transaction = transaction_query.first()
    
    if not transaction:
        SecurityManager.log_security_event("UNAUTHORIZED_PAYMENT_ACCESS", current_user.id, f"Session: {session_id}")
        flash('Transação não encontrada.', 'error')
        return redirect(url_for('dashboard'))
    
    # Validar que o usuário é o proprietário da transação
    if transaction.user_id != current_user.id:
        SecurityManager.log_security_event("PAYMENT_OWNERSHIP_VIOLATION", current_user.id, f"Transaction: {transaction.id}")
        abort(403)
    
    # Verificar status no Stripe
    stripe_manager = StripePaymentManager()
    result = stripe_manager.retrieve_checkout_session(session_id)
    
    if result['success'] and result['session'].payment_status == 'paid':
        # Processar pagamento se ainda não foi processado
        if transaction.status == 'pending':
            credits_added = CreditManager.add_credits(
                user_id=current_user.id,
                amount=transaction.credits_purchased,
                description=f"Compra: {transaction.package_id}",
                payment_method="stripe",
                transaction_id=session_id
            )
            
            if credits_added:
                transaction.status = 'completed'
                transaction.completed_at = datetime.utcnow()
                db.session.commit()
                
                flash(f'Pagamento realizado com sucesso! R$ {transaction.credits_purchased:.2f} em créditos adicionados.', 'success')
            else:
                flash('Erro ao processar créditos. Entre em contato com o suporte.', 'error')
        else:
            flash('Créditos já foram adicionados anteriormente.', 'info')
    else:
        flash('Pagamento não confirmado. Tente novamente.', 'error')
    
    return redirect(url_for('dashboard'))

@app.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    """Webhook para processar eventos do Stripe incluindo assinaturas recorrentes"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    if not endpoint_secret:
        logger.error("STRIPE_WEBHOOK_SECRET not configured")
        return '', 400
    
    try:
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        
        # Verificar assinatura do webhook
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
        
        app.logger.info(f"Webhook recebido: {event['type']}")
        
        # Processar eventos de checkout completado (primeira compra/assinatura)
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            process_checkout_session(session)
            
        # Processar eventos de fatura paga (pagamentos recorrentes)
        elif event['type'] == 'invoice.payment_succeeded':
            invoice = event['data']['object']
            process_subscription_payment(invoice)
            
        # Processar eventos de assinatura ativa
        elif event['type'] == 'customer.subscription.created':
            subscription = event['data']['object']
            process_subscription_created(subscription)
            
        # Processar eventos de assinatura cancelada
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            process_subscription_cancelled(subscription)
            
        else:
            app.logger.info(f"Evento não processado: {event['type']}")
        
        return '', 200
            
    except ValueError as e:
        app.logger.error(f"Payload inválido: {str(e)}")
        return '', 400
    except stripe.error.SignatureVerificationError as e:
        app.logger.error(f"Assinatura inválida: {str(e)}")
        return '', 400
    except Exception as e:
        app.logger.error(f"Webhook error: {str(e)}")
        return '', 400

def process_checkout_session(session):
    """Processar sessão de checkout completada (primeira compra)"""
    try:
        from package_models import UserSubscription
        
        metadata = session.get('metadata', {})
        user_id = metadata.get('user_id')
        product_type = metadata.get('product_type')
        
        if product_type == 'labels_subscription' and user_id:
            # Verificar se já existe assinatura
            existing_subscription = UserSubscription.query.filter_by(
                user_id=int(user_id),
                stripe_subscription_id=session.subscription,
                status='active'
            ).first()
            
            if not existing_subscription:
                # Criar nova assinatura
                subscription = UserSubscription()
                subscription.user_id = int(user_id)
                subscription.stripe_subscription_id = session.subscription
                subscription.status = 'active'
                subscription.starts_at = datetime.utcnow()
                subscription.expires_at = datetime.utcnow() + timedelta(days=30)
                subscription.auto_renew = True
                
                db.session.add(subscription)
                db.session.commit()
                
                app.logger.info(f"Assinatura de etiquetas criada via webhook para usuário {user_id}")
        
    except Exception as e:
        app.logger.error(f"Erro ao processar checkout session: {str(e)}")

def process_subscription_payment(invoice):
    """Processar pagamento recorrente de assinatura (faturas pagas)"""
    try:
        from package_models import UserSubscription
        import stripe
        stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
        
        # Obter dados da assinatura
        subscription_id = invoice.get('subscription')
        if not subscription_id:
            return
        
        # Buscar assinatura local
        local_subscription = UserSubscription.query.filter_by(
            stripe_subscription_id=subscription_id
        ).first()
        
        if local_subscription:
            # Renovar assinatura por mais 30 dias
            local_subscription.expires_at = datetime.utcnow() + timedelta(days=30)
            local_subscription.status = 'active'
            db.session.commit()
            
            app.logger.info(f"Assinatura renovada para usuário {local_subscription.user_id} - pagamento recorrente processado")
        else:
            # Buscar assinatura no Stripe para obter metadados
            stripe_subscription = stripe.Subscription.retrieve(subscription_id)
            metadata = stripe_subscription.get('metadata', {})
            user_id = metadata.get('user_id')
            
            if user_id:
                # Criar assinatura se não existir
                subscription = UserSubscription()
                subscription.user_id = int(user_id)
                subscription.stripe_subscription_id = subscription_id
                subscription.status = 'active'
                subscription.starts_at = datetime.utcnow()
                subscription.expires_at = datetime.utcnow() + timedelta(days=30)
                subscription.auto_renew = True
                
                db.session.add(subscription)
                db.session.commit()
                
                app.logger.info(f"Assinatura criada via pagamento recorrente para usuário {user_id}")
        
    except Exception as e:
        app.logger.error(f"Erro ao processar pagamento recorrente: {str(e)}")

def process_subscription_created(subscription):
    """Processar criação de assinatura"""
    try:
        from package_models import UserSubscription
        
        metadata = subscription.get('metadata', {})
        user_id = metadata.get('user_id')
        
        if user_id:
            # Verificar se já existe
            existing = UserSubscription.query.filter_by(
                stripe_subscription_id=subscription['id']
            ).first()
            
            if not existing:
                # Criar nova assinatura
                new_subscription = UserSubscription()
                new_subscription.user_id = int(user_id)
                new_subscription.stripe_subscription_id = subscription['id']
                new_subscription.status = 'active'
                new_subscription.starts_at = datetime.utcnow()
                new_subscription.expires_at = datetime.utcnow() + timedelta(days=30)
                new_subscription.auto_renew = True
                
                db.session.add(new_subscription)
                db.session.commit()
                
                app.logger.info(f"Assinatura criada via evento subscription.created para usuário {user_id}")
        
    except Exception as e:
        app.logger.error(f"Erro ao processar criação de assinatura: {str(e)}")

def process_subscription_cancelled(subscription):
    """Processar cancelamento de assinatura"""
    try:
        from package_models import UserSubscription
        
        # Buscar assinatura local
        local_subscription = UserSubscription.query.filter_by(
            stripe_subscription_id=subscription['id']
        ).first()
        
        if local_subscription:
            # Cancelar assinatura
            local_subscription.status = 'cancelled'
            local_subscription.cancelled_at = datetime.utcnow()
            local_subscription.auto_renew = False
            
            db.session.commit()
            
            app.logger.info(f"Assinatura cancelada para usuário {local_subscription.user_id}")
        
    except Exception as e:
        app.logger.error(f"Erro ao processar cancelamento de assinatura: {str(e)}")

def check_labels_subscription_status(user_id):
    """Verificar se o usuário tem assinatura ativa do módulo de etiquetas"""
    try:
        from package_models import UserSubscription
        
        active_subscription = UserSubscription.query.filter_by(
            user_id=user_id,
            status='active'
        ).filter(
            UserSubscription.expires_at > datetime.utcnow()
        ).first()
        
        if active_subscription:
            return {
                'has_subscription': True,
                'subscription_id': active_subscription.id,
                'expires_at': active_subscription.expires_at,
                'stripe_subscription_id': active_subscription.stripe_subscription_id,
                'auto_renew': active_subscription.auto_renew
            }
        else:
            return {
                'has_subscription': False,
                'subscription_id': None,
                'expires_at': None,
                'stripe_subscription_id': None,
                'auto_renew': False
            }
    except Exception as e:
        app.logger.error(f"Erro ao verificar status da assinatura: {str(e)}")
        return {
            'has_subscription': False,
            'subscription_id': None,
            'expires_at': None,
            'stripe_subscription_id': None,
            'auto_renew': False
        }

# Função removida - substituída por extrato_creditos

@app.route('/api/user/balance')
@login_required
@rate_limit_check(max_requests=100, window_minutes=10)
def api_user_balance():
    """API para obter saldo atual do usuário com isolamento de dados"""
    # Validar acesso do usuário aos próprios dados
    if not SecurityManager.validate_user_access(current_user.id):
        SecurityManager.log_security_event("UNAUTHORIZED_BALANCE_ACCESS", current_user.id)
        abort(403)
    
    # Registrar acesso à API
    SecurityManager.log_security_event("BALANCE_API_ACCESS", current_user.id)
    
    return jsonify({
        'balance': current_user.current_balance or 0.0,
        'is_trial': current_user.is_trial_active(),
        'trial_expires': current_user.trial_expires_at.isoformat() if current_user.trial_expires_at else None
    })

# Modificar função de dedução de créditos para XML downloads
def charge_for_xml_download(user_id: int, invoice_key: str) -> bool:
    """Cobra pelo download de XML usando sistema simplificado de créditos"""
    from simple_credit_system import consume_xml_credit
    
    return consume_xml_credit(
        user_id=user_id,
        description=f"Download XML: {invoice_key[:10]}..."
    )

@app.route('/configurar-etiquetas', methods=['GET', 'POST'])
@login_required
@rate_limit_check(max_requests=30, window_minutes=10)
def configurar_etiquetas():
    """Configurar etiquetas personalizadas com isolamento de dados"""
    # Validar acesso do usuário aos próprios dados
    if not SecurityManager.validate_user_access(current_user.id):
        SecurityManager.log_security_event("UNAUTHORIZED_CONFIG_ACCESS", current_user.id)
        abort(403)
    
    if request.method == 'POST':
        try:
            # Verificar se é uma requisição AJAX
            if request.is_json or request.headers.get('Content-Type', '').startswith('application/json'):
                return jsonify({'error': 'JSON não suportado para upload de arquivos'}), 400
            
            # Sanitizar e validar dados de entrada
            company_name = SecurityManager.sanitize_input(request.form.get('company_name', '').strip())
            company_subtitle = SecurityManager.sanitize_input(request.form.get('company_subtitle', '').strip())
            area_code = SecurityManager.sanitize_input(request.form.get('area_code', '01').strip())
            layout_style = SecurityManager.sanitize_input(request.form.get('layout_style', 'layout1').strip())
            
            # Atualizar dados da empresa com validação
            current_user.company_name = company_name[:200] if company_name else None
            current_user.company_subtitle = company_subtitle[:100] if company_subtitle else None
            current_user.default_area_code = area_code[:5] if area_code else '01'
            current_user.preferred_layout = layout_style[:20] if layout_style else 'layout1'
            
            # Verificar se deve remover logo
            remove_logo = request.form.get('remove_logo', 'false').lower() == 'true'
            if remove_logo and current_user.company_logo_path:
                # Remover arquivo físico se existir
                try:
                    if os.path.exists(current_user.company_logo_path):
                        os.remove(current_user.company_logo_path)
                except Exception as e:
                    logger.warning(f"Erro ao remover arquivo de logo: {e}")
                
                # Limpar caminho no banco
                current_user.company_logo_path = None
                flash('Logo removida com sucesso!', 'success')
            
            # Processar upload de logo (trocar ou adicionar nova)
            elif 'company_logo' in request.files:
                logo_file = request.files['company_logo']
                if logo_file and logo_file.filename:
                    # Validar tipo de arquivo
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                    file_extension = logo_file.filename.rsplit('.', 1)[1].lower()
                    
                    if file_extension in allowed_extensions:
                        # Remover logo anterior se existir
                        if current_user.company_logo_path and os.path.exists(current_user.company_logo_path):
                            try:
                                os.remove(current_user.company_logo_path)
                            except Exception as e:
                                logger.warning(f"Erro ao remover logo anterior: {e}")
                        
                        # Criar diretório se não existir
                        logo_dir = os.path.join('static', 'uploads', 'logos')
                        os.makedirs(logo_dir, exist_ok=True)
                        
                        # Gerar nome único para o arquivo
                        import uuid
                        unique_filename = f"{current_user.id}_{uuid.uuid4().hex[:8]}.{file_extension}"
                        logo_path = os.path.join(logo_dir, unique_filename)
                        
                        # Salvar arquivo
                        logo_file.save(logo_path)
                        
                        # Atualizar caminho no banco
                        current_user.company_logo_path = logo_path
                        
                        flash('Logo atualizada com sucesso!', 'success')
                    else:
                        flash('Formato de arquivo não suportado. Use PNG, JPG, JPEG ou GIF.', 'error')
            
            db.session.commit()
            flash('Configurações de etiquetas salvas com sucesso!', 'success')
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao salvar configurações: {e}")
            flash('Erro ao salvar configurações. Tente novamente.', 'error')
    
    return render_template('configurar_etiquetas.html')

@app.route('/historico-creditos')
@login_required
@rate_limit_check(max_requests=50, window_minutes=10)
def credit_history():
    """Histórico detalhado de uso de créditos com isolamento de dados"""
    # Validar acesso do usuário aos próprios dados
    if not SecurityManager.validate_user_access(current_user.id):
        SecurityManager.log_security_event("UNAUTHORIZED_HISTORY_ACCESS", current_user.id)
        abort(403)
    
    # Paginação com sanitização
    page = max(1, request.args.get('page', 1, type=int))
    per_page = min(50, max(10, request.args.get('per_page', 20, type=int)))
    
    # Filtros com sanitização
    module_filter = SecurityManager.sanitize_input(request.args.get('module', ''))
    date_from = SecurityManager.sanitize_input(request.args.get('date_from', ''))
    date_to = SecurityManager.sanitize_input(request.args.get('date_to', ''))
    
    # Query base com isolamento de dados e tratamento de erro
    try:
        base_query = db.session.query(UsageRecord, ServiceModule.name.label('module_name'))\
            .outerjoin(ServiceModule, UsageRecord.module_id == ServiceModule.id)\
            .filter(UsageRecord.user_id == current_user.id)
        
        # Aplicar isolamento de dados por usuário
        query = DataIsolationManager.filter_user_usage(base_query, current_user.id)
        
        # Aplicar filtros
        if module_filter:
            query = query.filter(ServiceModule.name == module_filter)
        
        if date_from:
            try:
                from_date = datetime.strptime(date_from, '%Y-%m-%d')
                query = query.filter(UsageRecord.created_at >= from_date)
            except ValueError:
                pass
        
        if date_to:
            try:
                to_date = datetime.strptime(date_to, '%Y-%m-%d')
                to_date = to_date.replace(hour=23, minute=59, second=59)
                query = query.filter(UsageRecord.created_at <= to_date)
            except ValueError:
                pass
        
        # Ordenar por data (mais recente primeiro)
        query = query.order_by(UsageRecord.created_at.desc())
        
        # Paginação
        records = query.paginate(page=page, per_page=per_page, error_out=False)
        
        # Estatísticas
        total_spent = db.session.query(db.func.sum(UsageRecord.cost))\
            .filter(UsageRecord.user_id == current_user.id).scalar() or 0
        
        this_month_spent = db.session.query(db.func.sum(UsageRecord.cost))\
            .filter(
                UsageRecord.user_id == current_user.id,
                UsageRecord.created_at >= datetime.now().replace(day=1, hour=0, minute=0, second=0)
            ).scalar() or 0
        
        # Estatísticas por módulo
        module_stats = db.session.query(
            ServiceModule.name,
            db.func.sum(UsageRecord.cost).label('total_cost'),
            db.func.count(UsageRecord.id).label('usage_count')
        ).outerjoin(ServiceModule, UsageRecord.module_id == ServiceModule.id)\
         .filter(UsageRecord.user_id == current_user.id)\
         .group_by(ServiceModule.name).all()
        
        # Módulos disponíveis para filtro
        available_modules = db.session.query(ServiceModule.name).distinct().all()
        
    except Exception as e:
        logger.error(f"Erro ao buscar histórico de créditos: {e}")
        db.session.rollback()
        records = None
        total_spent = 0
        this_month_spent = 0
        module_stats = []
        available_modules = []
    
    return render_template('credit_history.html',
                         records=records,
                         total_spent=total_spent,
                         this_month_spent=this_month_spent,
                         module_stats=module_stats,
                         available_modules=available_modules,
                         current_filters={
                             'module': module_filter,
                             'date_from': date_from,
                             'date_to': date_to
                         })

def save_company_logo(logo_file, user_id):
    """Salvar logo da empresa"""
    try:
        from werkzeug.utils import secure_filename
        
        # Criar diretório se não existir
        upload_dir = os.path.join('static', 'uploads', 'logos')
        os.makedirs(upload_dir, exist_ok=True)
        
        # Gerar nome do arquivo
        filename = secure_filename(logo_file.filename)
        if not filename:
            filename = f'logo_{user_id}.png'
        
        # Adicionar timestamp para evitar cache
        name, ext = os.path.splitext(filename)
        filename = f'{name}_{user_id}_{int(datetime.now().timestamp())}{ext}'
        
        # Salvar arquivo
        filepath = os.path.join(upload_dir, filename)
        logo_file.save(filepath)
        
        return filename
        
    except Exception as e:
        logger.error(f"Erro ao salvar logo: {e}")
        return None

@app.route('/static/uploads/logos/<filename>')
@rate_limit_check(max_requests=100, window_minutes=10)
def serve_logo(filename):
    """Servir logos das empresas com validação de segurança"""
    # Sanitizar nome do arquivo
    filename = SecurityManager.sanitize_input(filename)
    
    # Validar formato do nome do arquivo para prevenir path traversal
    if not filename or '..' in filename or '/' in filename or '\\' in filename:
        SecurityManager.log_security_event("INVALID_LOGO_ACCESS", None, f"Filename: {filename}")
        abort(400)
    
    # Verificar se arquivo existe e é seguro
    logo_path = os.path.join('static', 'uploads', 'logos', filename)
    if not os.path.exists(logo_path) or not os.path.isfile(logo_path):
        abort(404)
    
    # Validar que é um arquivo de imagem válido
    allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif', '.svg'}
    if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
        SecurityManager.log_security_event("INVALID_LOGO_FORMAT", None, f"Filename: {filename}")
        abort(400)
    
    return send_from_directory(os.path.join('static', 'uploads', 'logos'), filename)

# API endpoint para salvar configurações via AJAX
@app.route('/api/save-label-config', methods=['POST'])
@login_required
@rate_limit_check(max_requests=20, window_minutes=10)
def save_label_config():
    """Salvar configurações de etiquetas via AJAX com isolamento de dados"""
    # Validar acesso do usuário aos próprios dados
    if not SecurityManager.validate_user_access(current_user.id):
        SecurityManager.log_security_event("UNAUTHORIZED_CONFIG_API_ACCESS", current_user.id)
        return jsonify({'success': False, 'error': 'Acesso negado'}), 403
    
    try:
        # Sanitizar e validar dados de entrada
        company_name = SecurityManager.sanitize_input(request.form.get('company_name', '').strip())
        company_subtitle = SecurityManager.sanitize_input(request.form.get('company_subtitle', '').strip())
        area_code = SecurityManager.sanitize_input(request.form.get('area_code', '01').strip())
        
        # Atualizar dados da empresa com validação
        current_user.company_name = company_name[:200] if company_name else None
        current_user.company_subtitle = company_subtitle[:100] if company_subtitle else None
        current_user.default_area_code = area_code[:5] if area_code else '01'
        
        # Processar upload de logo se enviado
        if 'company_logo' in request.files:
            logo_file = request.files['company_logo']
            if logo_file and logo_file.filename:
                logo_path = save_company_logo(logo_file, current_user.id)
                current_user.company_logo_path = logo_path
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Configurações salvas com sucesso!'})
        
    except Exception as e:
        logger.error(f"Erro ao salvar configurações: {e}")
        return jsonify({'success': False, 'message': f'Erro ao salvar configurações: {str(e)}'})

@app.route('/download_generated_label/<int:xml_id>')
@login_required
def download_generated_label(xml_id):
    """Download de etiqueta já gerada"""
    xml_data = XMLFile.query.filter_by(id=xml_id, user_id=current_user.id).first()
    if not xml_data:
        flash('XML não encontrado.', 'error')
        return redirect(url_for('my_xmls'))
    
    if not xml_data.label_generated:
        flash('Etiqueta ainda não foi gerada para este XML.', 'error')
        return redirect(url_for('label_generator', xml_id=xml_id))
    
    # Re-gerar etiqueta com configurações salvas do usuário
    try:
        # Usar layout preferido do usuário
        layout_style = current_user.preferred_layout or 'layout1'
        
        # Configuração padrão para re-geração
        paper_config = {
            'size': '10x15cm',
            'total_volumes': xml_data.quantidade_volumes or 1,
            'volume_weights': [xml_data.peso_bruto or 0.0] * (xml_data.quantidade_volumes or 1)
        }
        
        labels = generate_improved_label_with_guaranteed_borders(
            xml_id=xml_id,
            user=current_user,
            paper_config=paper_config,
            layout_style=layout_style
        )
        
        if not labels:
            flash('Erro ao re-gerar etiqueta.', 'error')
            return redirect(url_for('label_generator', xml_id=xml_id))
        
        # Retornar PDF
        if len(labels) == 1:
            label = labels[0]
            pdf_buffer = label.get('pdf_buffer') or label.get('buffer')
            response = make_response(pdf_buffer.getvalue())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'inline; filename="{label["filename"]}"'
            response.headers['X-Frame-Options'] = 'ALLOWALL'
            return response
        else:
            from responsive_label_generator import merge_labels_into_single_pdf
            merged_pdf = merge_labels_into_single_pdf(labels)
            nf_number = getattr(xml_data, "numero_nf", xml_id)
            
            response = make_response(merged_pdf.getvalue())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'inline; filename="etiquetas_nf_{nf_number}_multipaginas.pdf"'
            response.headers['X-Frame-Options'] = 'ALLOWALL'
            return response
            
    except Exception as e:
        logger.error(f"Erro ao baixar etiqueta gerada: {e}")
        flash('Erro ao baixar etiqueta. Gerando nova...', 'error')
        return redirect(url_for('label_generator', xml_id=xml_id))

# Enhanced Label Generation Routes
@app.route('/configurar-etiquetas/<int:xml_id>')
@login_required
def label_generator(xml_id):
    """Página de configuração avançada de etiquetas"""
    try:
        # Buscar XML nas duas tabelas
        xml_record = XMLFile.query.filter_by(id=xml_id, user_id=current_user.id).first()
        xml_file = None
        
        if not xml_record:
            xml_file = XMLFile.query.filter_by(id=xml_id, user_id=current_user.id).first()
        
        if not xml_record and not xml_file:
            flash('XML não encontrado.', 'error')
            return redirect(url_for('meus_xmls'))
        
        # Verificar módulo de etiquetas
        labels_module = ServiceModule.query.filter_by(name='Etiquetas de Transporte').first()
        if not labels_module:
            flash('Módulo de etiquetas não disponível.', 'error')
            return redirect(url_for('meus_xmls'))
        
        # Verificar acesso ao módulo de etiquetas
        if not current_user.has_labels_access():
            flash('Você precisa adquirir o módulo de etiquetas para acessar esta funcionalidade.', 'warning')
            return redirect(url_for('labels_module'))
        
        # Usar dados da tabela encontrada
        xml_data = xml_record if xml_record else xml_file
        
        return render_template('label_generator.html', xml_data=xml_data)
        
    except Exception as e:
        logger.error(f"Erro ao configurar etiquetas: {e}")
        flash('Erro ao carregar configuração de etiquetas.', 'error')
        return redirect(url_for('meus_xmls'))


@app.route('/gerar-etiquetas-personalizadas/<int:xml_id>', methods=['POST'])
@login_required
def generate_custom_labels(xml_id):
    """Gera etiquetas personalizadas com volumes configuráveis"""
    try:
        # Buscar XML
        xml_record = XMLFile.query.filter_by(id=xml_id, user_id=current_user.id).first()
        xml_file = None
        
        if not xml_record:
            xml_file = XMLFile.query.filter_by(id=xml_id, user_id=current_user.id).first()
        
        if not xml_record and not xml_file:
            flash('XML não encontrado.', 'error')
            return redirect(url_for('meus_xmls'))
        
        xml_data = xml_record if xml_record else xml_file
        
        # Verificar módulo de etiquetas
        labels_module = ServiceModule.query.filter_by(name='Etiquetas de Transporte').first()
        if not labels_module:
            flash('Módulo de etiquetas não disponível.', 'error')
            return redirect(url_for('meus_xmls'))
        
        # Verificar acesso (trial ou saldo)
        is_trial_active = current_user.trial_expires_at and current_user.trial_expires_at > datetime.now()
        
        # Obter configurações do formulário
        form_volumes = int(request.form.get('total_volumes', 1))
        
        # Detectar quantidade real de volumes da NFe
        xml_content = getattr(xml_data, 'xml_content', None) or getattr(xml_data, 'content', '')
        if xml_content:
            from xml_processor import extract_xml_data
            extracted_data = extract_xml_data(xml_content)
            nfe_volumes = int(extracted_data.get('quantidade_volumes', '1'))
            # Usar o maior valor entre formulário e NFe
            total_volumes = max(form_volumes, nfe_volumes)
            logger.info(f"NFe detectada com {nfe_volumes} volumes, formulário configurou {form_volumes}, usando {total_volumes}")
        else:
            total_volumes = form_volumes
            
        company_name = request.form.get('company_name', current_user.company_name or 'SUA EMPRESA')
        company_subtitle = request.form.get('company_subtitle', current_user.company_subtitle or 'TRANSPORTE')
        area_code = request.form.get('area_code', current_user.default_area_code or '01')
        layout_style = request.form.get('layout_style', current_user.preferred_layout or 'transul')
        paper_size = request.form.get('paper_size', '10x15')
        paper_width_mm = int(request.form.get('paper_width_mm', 100))
        paper_height_mm = int(request.form.get('paper_height_mm', 150))
        
        # Verificar saldo antes de gerar
        total_cost = total_volumes * labels_module.cost_per_use
        if not is_trial_active and current_user.current_balance < total_cost:
            flash(f'Saldo insuficiente. Necessário: R$ {total_cost:.2f}', 'warning')
            return redirect(url_for('comprar_creditos'))
        
        # Processar logo se enviado
        logo_path = current_user.company_logo_path
        if 'company_logo' in request.files:
            logo_file = request.files['company_logo']
            if logo_file and logo_file.filename:
                logo_path = save_company_logo(logo_file, current_user.id)
                current_user.company_logo_path = logo_path
                db.session.commit()
        
        # Construir caminho completo da logo se existe
        full_logo_path = None
        if logo_path:
            if os.path.exists(logo_path):
                full_logo_path = logo_path
            else:
                # Construir caminho completo se apenas filename foi armazenado
                full_path = os.path.join('static', 'uploads', 'logos', logo_path)
                if os.path.exists(full_path):
                    full_logo_path = full_path
        
        # Atualizar configurações do usuário
        current_user.company_name = company_name
        current_user.company_subtitle = company_subtitle
        current_user.default_area_code = area_code
        db.session.commit()
        
        # Construir configuração de volumes
        volumes_config = []
        logger.info(f"Configurando {total_volumes} volumes para geração de etiquetas")
        for i in range(1, total_volumes + 1):
            peso = float(request.form.get(f'peso_volume_{i}', 0))
            pedido = request.form.get(f'pedido_volume_{i}', f'PED{getattr(xml_data, "numero_nf", "00000")}-{i}')
            volumes_config.append({
                'peso': peso,
                'pedido': pedido
            })
            logger.info(f"Volume {i}: peso={peso}, pedido={pedido}")
        
        logger.info(f"Total de volumes configurados: {len(volumes_config)}")
        
        # Gerar etiquetas usando sistema de processamento em lotes
        from responsive_label_generator import generate_multiple_responsive_labels_from_volumes
        
        # Obter registro XML e dados da empresa
        xml_record = XMLFile.query.filter_by(id=xml_id, user_id=current_user.id).first()
        if not xml_record:
            flash('XML não encontrado.', 'error')
            return redirect(url_for('label_generator', xml_id=xml_id))
        
        # Configurações da empresa (usando configurações do formulário)
        company_name = request.form.get('company_name', current_user.company_name or "SUA EMPRESA")
        company_subtitle = request.form.get('company_subtitle', current_user.company_subtitle or "TRANSPORTE")
        company_logo_path = full_logo_path  # Usar caminho completo corrigido
        area_code = request.form.get('area_code', current_user.default_area_code or "01")
        layout_style = request.form.get('layout_style', current_user.preferred_layout or 'transul')
        
        # Gerar etiquetas com sistema melhorado com bordas garantidas
        labels = generate_improved_labels_with_guaranteed_borders(
            xml_record=xml_record,
            volumes_config=volumes_config,
            company_name=company_name,
            company_logo_path=company_logo_path,
            paper_width_mm=paper_width_mm,
            paper_height_mm=paper_height_mm,
            area_code=area_code,
            company_subtitle=company_subtitle,
            layout_style=layout_style
        )
        
        if not labels:
            flash('Erro ao gerar etiquetas.', 'error')
            return redirect(url_for('label_generator', xml_id=xml_id))
        
        # Cobrar pelo serviço se não estiver em trial
        if not is_trial_active:
            # Cobrar por cada etiqueta gerada
            total_cost = len(labels) * labels_module.cost_per_use
            current_user.current_balance -= total_cost
            
            # Registrar uso para cada etiqueta
            for i, label_info in enumerate(labels):
                usage_record = UsageRecord(
                    user_id=current_user.id,
                    service_module_id=labels_module.id,
                    cost=labels_module.cost_per_use,
                    description=f"Etiqueta de transporte - Volume {label_info['volume']} - {label_info['pedido']}",
                    created_at=datetime.now()
                )
                db.session.add(usage_record)
            
            db.session.commit()
        
        # Sempre gerar um PDF único (uma ou múltiplas páginas)
        if len(labels) == 1:
            # Uma etiqueta - PDF direto
            label = labels[0]
            pdf_buffer = label.get('pdf_buffer') or label.get('buffer')
            response = make_response(pdf_buffer.getvalue())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'inline; filename="{label["filename"]}"'
            response.headers['X-Frame-Options'] = 'ALLOWALL'
            return response
        else:
            # Múltiplas etiquetas - PDF único com múltiplas páginas
            from responsive_label_generator import merge_labels_into_single_pdf
            
            merged_pdf = merge_labels_into_single_pdf(labels)
            nf_number = getattr(xml_data, "numero_nf", xml_id)
            
            response = make_response(merged_pdf.getvalue())
            response.headers['Content-Type'] = 'application/pdf'
            response.headers['Content-Disposition'] = f'inline; filename="etiquetas_nf_{nf_number}_multipaginas.pdf"'
            response.headers['X-Frame-Options'] = 'ALLOWALL'
        
        # Registrar atividade de geração de etiqueta
        log_user_activity(
            user_id=current_user.id,
            activity_type='label_generated',
            description=f"Etiqueta gerada: NF {xml_data.numero_nf or xml_id} - {len(labels)} volume{'s' if len(labels) > 1 else ''}",
            details={
                'xml_id': xml_id,
                'numero_nf': xml_data.numero_nf,
                'empresa': xml_data.nome_emitente[:50] if xml_data.nome_emitente else 'N/A',
                'volumes': len(labels),
                'layout_style': request.args.get('layout', 'transul')
            }
        )
        
        # Marcar etiqueta como gerada e salvar o caminho do arquivo
        xml_data.label_generated = True
        if len(labels) == 1:
            xml_data.label_file_path = f"etiquetas/nf_{xml_data.numero_nf or xml_id}_{labels[0]['filename']}"
        else:
            xml_data.label_file_path = f"etiquetas/nf_{xml_data.numero_nf or xml_id}_multipaginas.pdf"
        db.session.commit()
        
        flash(f'{len(labels)} etiquetas geradas com sucesso!', 'success')
        return response
        
    except Exception as e:
        logger.error(f"Erro ao gerar etiquetas personalizadas: {e}")
        flash('Erro ao gerar etiquetas personalizadas.', 'error')
        return redirect(url_for('label_generator', xml_id=xml_id))


# Comentar admin panel temporariamente para evitar conflito de rotas
# try:
#     from admin_panel import init_admin_panel
#     init_admin_panel(app)
# except ImportError:
#     logger.warning("Admin panel not available")

# ROTINAS REAIS PARA BOTÕES DE AÇÃO DA ADMINISTRAÇÃO DE USUÁRIOS

# Rota VER - Detalhes completos do usuário
@app.route('/admin/users/<int:user_id>/view')
def admin_user_view(user_id):
    """Ver detalhes completos de um usuário específico"""
    from models import User, XMLFile, UsageRecord, Charge, UserActivity
    from credit_system_fixed import get_user_xml_balance
    
    user = User.query.get_or_404(user_id)
    
    # Calcular estatísticas reais
    xml_balance = get_user_xml_balance(user.id)
    total_xmls = XMLFile.query.filter_by(user_id=user_id).count()
    total_spent = db.session.query(db.func.sum(Charge.amount)).filter(
        Charge.user_id == user_id,
        Charge.status == 'RECEIVED'
    ).scalar() or 0
    
    # XMLs recentes do usuário
    recent_xmls = XMLFile.query.filter_by(user_id=user_id).order_by(
        XMLFile.imported_at.desc()
    ).limit(10).all()
    
    # Histórico de atividades
    recent_activities = UserActivity.query.filter_by(user_id=user_id).order_by(
        UserActivity.created_at.desc()
    ).limit(15).all()
    
    # Histórico de cobranças
    charges = Charge.query.filter_by(user_id=user_id).order_by(
        Charge.created_at.desc()
    ).limit(10).all()
    
    user_data = {
        'user': user,
        'xml_balance': xml_balance,
        'total_xmls': total_xmls,
        'total_spent': total_spent,
        'recent_xmls': recent_xmls,
        'recent_activities': recent_activities,
        'charges': charges
    }
    
    return render_template('admin_user_view.html', **user_data)

# Rota EDITAR - Formulário de edição do usuário
@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
def admin_user_edit(user_id):
    """Editar dados de um usuário específico"""
    from models import User
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        try:
            # Atualizar dados básicos
            user.email = request.form.get('email', user.email)
            user.first_name = request.form.get('first_name', user.first_name)
            user.last_name = request.form.get('last_name', user.last_name)
            
            # Atualizar configurações administrativas
            if 'is_admin' in request.form:
                user.is_admin = request.form.get('is_admin') == 'on'
            
            if 'is_active' in request.form:
                user.is_active = request.form.get('is_active') == 'on'
            else:
                user.is_active = True  # Default ativo
            
            # Configurações de trial
            trial_end_date = request.form.get('trial_end_date')
            if trial_end_date:
                from datetime import datetime
                user.trial_end_date = datetime.strptime(trial_end_date, '%Y-%m-%d')
            
            db.session.commit()
            flash(f'Usuário {user.email} atualizado com sucesso!', 'success')
            return redirect(url_for('admin_users'))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao atualizar usuário {user_id}: {e}")
            flash('Erro ao atualizar usuário. Tente novamente.', 'error')
    
    return render_template('admin_user_edit.html', user=user)

# Rota CRÉDITOS - Gerenciar créditos do usuário
@app.route('/admin/users/<int:user_id>/credits', methods=['GET', 'POST'])
def admin_user_credits(user_id):
    """Gerenciar créditos XML de um usuário específico"""
    from models import User, CreditBalance, Charge
    from credit_system_fixed import get_user_xml_balance, add_xml_credits
    
    user = User.query.get_or_404(user_id)
    current_balance = get_user_xml_balance(user.id)
    
    if request.method == 'POST':
        try:
            action = request.form.get('action')
            amount = float(request.form.get('amount', 0))
            description = request.form.get('description', '')
            
            if action == 'add_credits':
                # Adicionar créditos XML
                success = add_xml_credits(user.id, int(amount), description or f'Créditos adicionados pelo admin')
                if success:
                    flash(f'{int(amount)} créditos XML adicionados para {user.email}!', 'success')
                else:
                    flash('Erro ao adicionar créditos.', 'error')
                    
            elif action == 'create_charge':
                # Criar cobrança manual
                charge = Charge(
                    user_id=user.id,
                    amount=amount,
                    description=description or f'Cobrança manual - Admin',
                    status='PENDING',
                    payment_method='PIX'
                )
                db.session.add(charge)
                db.session.commit()
                flash(f'Cobrança de R$ {amount:.2f} criada para {user.email}!', 'success')
            
            return redirect(url_for('admin_user_credits', user_id=user_id))
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao gerenciar créditos do usuário {user_id}: {e}")
            flash('Erro ao processar operação. Tente novamente.', 'error')
    
    # Histórico de créditos e cobranças
    credit_history = CreditBalance.query.filter_by(user_id=user_id).order_by(
        CreditBalance.created_at.desc()
    ).limit(20).all()
    
    charges_history = Charge.query.filter_by(user_id=user_id).order_by(
        Charge.created_at.desc()
    ).limit(10).all()
    
    return render_template('admin_user_credits.html', 
                         user=user,
                         current_balance=current_balance,
                         credit_history=credit_history,
                         charges_history=charges_history)

# Rota DESATIVAR/ATIVAR - Toggle status do usuário
@app.route('/admin/users/<int:user_id>/toggle-status', methods=['POST'])
def admin_user_toggle_status(user_id):
    """Ativar/Desativar usuário"""
    from models import User
    
    user = User.query.get_or_404(user_id)
    
    try:
        # Toggle status ativo
        user.is_active = not getattr(user, 'is_active', True)
        
        # Log da ação
        action = 'ativado' if user.is_active else 'desativado'
        log_user_activity(
            user_id=user.id,
            activity_type='account_status_changed',
            description=f'Conta {action} pelo administrador'
        )
        
        db.session.commit()
        
        status_msg = 'ativado' if user.is_active else 'desativado'
        flash(f'Usuário {user.email} foi {status_msg} com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao alterar status do usuário {user_id}: {e}")
        flash('Erro ao alterar status do usuário.', 'error')
    
    return redirect(url_for('admin_users'))

# Import simple admin route
try:
    import simple_admin
    logger.info("Simple admin route loaded")
except ImportError:
    logger.warning("Simple admin not available")

# Google OAuth Routes (defined after all other routes)
@app.route("/google_login")
def google_login():
    """Initiate Google OAuth login"""
    if not client:
        flash("Google OAuth não está configurado.", "error")
        return redirect(url_for("login"))
    
    try:
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        authorization_endpoint = google_provider_cfg["authorization_endpoint"]
        
        redirect_uri = get_google_redirect_url()
        
        request_uri = client.prepare_request_uri(
            authorization_endpoint,
            redirect_uri=redirect_uri,
            scope=["openid", "email", "profile"],
            prompt="select_account consent",
            access_type="offline",
            include_granted_scopes="true"
        )
        return redirect(request_uri)
    except Exception as e:
        flash(f"Erro ao iniciar login com Google: {str(e)}", "error")
        return redirect(url_for("login"))

@app.route("/google_login/callback")
def google_callback():
    """Handle Google OAuth callback"""
    if not client:
        flash("Google OAuth não está configurado.", "error")
        return redirect(url_for("login"))
    
    try:
        code = request.args.get("code")
        if not code:
            flash("Código de autorização não recebido do Google.", "error")
            return redirect(url_for("login"))
        
        google_provider_cfg = requests.get(GOOGLE_DISCOVERY_URL).json()
        token_endpoint = google_provider_cfg["token_endpoint"]
        
        redirect_uri = get_google_redirect_url()
        
        token_url, headers, body = client.prepare_token_request(
            token_endpoint,
            authorization_response=request.url.replace("http://", "https://"),
            redirect_url=redirect_uri,
            code=code,
        )
        
        token_response = requests.post(
            token_url,
            headers=headers,
            data=body,
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),
        )
        
        # Verificar se a resposta do token é válida
        if token_response.status_code != 200:
            flash("Erro na autenticação com Google. Tente novamente.", "error")
            return redirect(url_for("login"))
        
        token_data = token_response.json()
        if 'error' in token_data:
            flash(f"Erro de autenticação: {token_data.get('error_description', 'Token inválido')}", "error")
            return redirect(url_for("login"))
        
        client.parse_request_body_response(json.dumps(token_data))
        
        userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
        uri, headers, body = client.add_token(userinfo_endpoint)
        userinfo_response = requests.get(uri, headers=headers, data=body)
        
        # Verificar se a resposta do userinfo é válida
        if userinfo_response.status_code != 200:
            flash("Erro ao obter informações do usuário Google.", "error")
            return redirect(url_for("login"))
        
        userinfo = userinfo_response.json()
        
        # Validações de segurança rigorosas
        if not userinfo.get("email_verified", False):
            flash("Email não verificado pelo Google. Verifique seu email e tente novamente.", "error")
            return redirect(url_for("login"))
        
        if not userinfo.get("email"):
            flash("Email não fornecido pelo Google. Tente novamente.", "error")
            return redirect(url_for("login"))
        
        # Verificar se o sub (user ID) está presente
        if not userinfo.get("sub"):
            flash("Identificação de usuário inválida. Tente novamente.", "error")
            return redirect(url_for("login"))
        
        users_email = userinfo["email"]
        users_name = userinfo.get("given_name", "User")
        users_picture = userinfo.get("picture")
        google_user_id = userinfo["sub"]
        
        # Logs de segurança para auditoria OAuth
        logger.info(f"OAUTH_ATTEMPT: Google ID: {google_user_id[:8]}..., Email: {users_email}, Host: {request.host}")
        
        # Verificações de segurança rigorosas para encontrar/criar usuário
        # Primeiro verificar se já existe usuário com este Google ID
        user_by_google_id = User.query.filter_by(google_user_id=google_user_id).first()
        user_by_email = User.query.filter_by(email=users_email).first()
        
        # Verificar inconsistências de segurança
        if user_by_google_id and user_by_email and user_by_google_id.id != user_by_email.id:
            logger.warning(f"SECURITY_VIOLATION: Conflito de identificação - Google ID vinculado ao usuário {user_by_google_id.id}, mas email {users_email} pertence ao usuário {user_by_email.id}")
            flash("Erro de segurança: Conflito de identificação detectado. Entre em contato com o suporte.", "error")
            return redirect(url_for("login"))
        
        # Se existe usuário por Google ID, usar ele
        if user_by_google_id:
            user = user_by_google_id
            logger.info(f"OAUTH_EXISTING_GOOGLE: Usuário {user.id} encontrado pelo Google ID")
            # Verificar se o email mudou no Google
            if user.email != users_email:
                logger.warning(f"SECURITY_VIOLATION: Email mudou no Google - Usuário {user.id}, email anterior: {user.email}, novo email: {users_email}")
                flash("Erro de segurança: Email inconsistente com conta registrada. Entre em contato com o suporte.", "error")
                return redirect(url_for("login"))
        # Se existe usuário por email mas sem Google ID, vincular
        elif user_by_email:
            user = user_by_email
            logger.info(f"OAUTH_LINKING: Vinculando Google ID ao usuário existente {user.id}")
            # Verificar se não é conta local com senha
            if user.provider == 'local' and user.password_hash:
                logger.warning(f"OAUTH_CONFLICT: Tentativa de vincular Google a conta local com senha - Usuário {user.id}")
                flash("Este email já está registrado com senha. Use o login tradicional ou redefina sua senha.", "error")
                return redirect(url_for("login"))
            # Vincular conta Google
            user.google_user_id = google_user_id
            user.provider = 'google'
            logger.info(f"OAUTH_LINKED: Google ID vinculado com sucesso ao usuário {user.id}")
        # Criar novo usuário
        else:
            logger.info(f"OAUTH_NEW_USER: Criando novo usuário para email {users_email}")
            user = User()
            user.email = users_email
            user.name = users_name
            user.provider = 'google'
            user.google_user_id = google_user_id
            user.trial_start_date = datetime.utcnow()
            user.trial_end_date = datetime.utcnow() + timedelta(days=7)
            user.is_trial_active = True
            user.profile_picture = users_picture
            user.active = True
            
            db.session.add(user)
            db.session.commit()
            
            logger.info(f"OAUTH_USER_CREATED: Novo usuário {user.id} criado via Google OAuth")
            flash(f"Bem-vindo ao CROSS XML, {users_name}! Você tem 7 dias de teste grátis.", "success")
            log_user_activity(user.id, 'registration', f'Novo usuário registrado via Google OAuth ({request.host})')
            
            login_user(user)
            log_user_activity(user.id, 'login', f'Login via Google OAuth ({request.host})')
            return redirect(url_for("dashboard"))
        
        # Atualizar informações do usuário existente
        if not user.name or user.name != users_name:
            user.name = users_name
        if users_picture and (not user.profile_picture or user.profile_picture != users_picture):
            user.profile_picture = users_picture
        
        # Verificar se conta está ativa
        if not user.active:
            flash("Sua conta está desativada. Entre em contato com o suporte.", "error")
            return redirect(url_for("login"))
        
        db.session.commit()
        flash(f"Bem-vindo de volta, {user.name}!", "success")
        
        login_user(user)
        log_user_activity(user.id, 'login', f'Login via Google OAuth ({request.host})')
        
        # Log de segurança para auditoria de login bem-sucedido
        logger.info(f"OAUTH_LOGIN_SUCCESS: Usuário {user.id} autenticado via Google OAuth, IP: {request.remote_addr}")
        
        return redirect(url_for("dashboard"))
        
    except Exception as e:
        logger.error(f"OAUTH_ERROR: Erro durante autenticação Google - {str(e)}, IP: {request.remote_addr}")
        flash(f"Erro durante autenticação com Google: {str(e)}", "error")
        return redirect(url_for("login"))

@app.route("/google_logout")
@login_required
def google_logout():
    """Google OAuth logout"""
    logout_user()
    flash("Logout realizado com sucesso.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)