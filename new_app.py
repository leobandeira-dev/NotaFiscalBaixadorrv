"""
Sistema completo de XML Downloader com autenticação e cobrança
"""

import os
import json
import uuid
import logging
import secrets
import pytz
from datetime import datetime, timedelta
from threading import Thread, Lock
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory, send_file, make_response
from io import BytesIO
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from werkzeug.middleware.proxy_fix import ProxyFix
from itsdangerous import URLSafeTimedSerializer
from authlib.integrations.flask_client import OAuth
from models import db, User, ServiceModule, UsageRecord, Charge, SystemSettings, StripeTransaction, CreditBalance, XMLFile, init_default_data
from asaas_integration import AsaasAPI, create_minimum_charge, process_webhook_payment
from stripe_integration import StripePaymentManager, CreditManager, PricingManager, process_stripe_webhook
from transport_label_generator import TransportLabelGenerator, generate_label_from_database_xml
from transport_label_generator_v2 import CustomTransportLabelGenerator, generate_custom_label_from_database_xml
from xml_processor import extract_xml_data
from download_service import DownloadService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

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

# OAuth configuration
app.config['GOOGLE_CLIENT_ID'] = os.environ.get('GOOGLE_CLIENT_ID', '')
app.config['GOOGLE_CLIENT_SECRET'] = os.environ.get('GOOGLE_CLIENT_SECRET', '')

# Initialize database
db.init_app(app)

# Initialize Flask-Mail
mail = Mail(app)

# Initialize OAuth
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=app.config['GOOGLE_CLIENT_ID'],
    client_secret=app.config['GOOGLE_CLIENT_SECRET'],
    server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Faça login para acessar esta página.'
login_manager.login_message_category = 'info'

# Initialize password reset serializer
serializer = URLSafeTimedSerializer(app.secret_key)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Job management (similar to previous system)
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
        self.status = "starting"
        self.files = []  # Changed from downloaded_files to files for template compatibility
        self.errors = []
        self.start_time = datetime.now()
        self.end_time = None

    @property
    def progress_percentage(self):
        """Calculate progress percentage"""
        if self.total_keys == 0:
            return 0
        return round((self.processed / self.total_keys) * 100, 2)

    def to_dict(self):
        return {
            'job_id': self.job_id,
            'total_keys': self.total_keys,
            'processed': self.processed,
            'successful': self.successful,
            'failed': self.failed,
            'status': self.status,
            'files': self.files,
            'errors': self.errors,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'progress_percentage': self.progress_percentage
        }

# Create tables and initialize data
with app.app_context():
    db.create_all()
    init_default_data()
    
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

@app.route('/auth/google')
def google_login():
    """Google OAuth login"""
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/auth/google/callback')
def google_callback():
    """Google OAuth callback"""
    try:
        token = google.authorize_access_token()
        user_info = token.get('userinfo')
        
        if user_info:
            email = user_info.get('email')
            name = user_info.get('name', email.split('@')[0])
            
            # Check if user exists
            user = User.query.filter_by(email=email).first()
            
            if not user:
                # Create new user
                user = User(name=name, email=email)
                # Set a random password for OAuth users
                user.set_password(secrets.token_urlsafe(32))
                db.session.add(user)
                db.session.commit()
                flash('Conta criada com sucesso via Google!', 'success')
            
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Erro ao obter informações do Google.', 'error')
            
    except Exception as e:
        logger.error(f"Erro no login Google: {e}")
        flash('Erro no login com Google. Tente novamente.', 'error')
    
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    from download_service import DownloadService
    
    # Get user XML statistics
    user_xmls = DownloadService.get_user_xmls(current_user.id)
    xml_count = len(user_xmls)
    
    # Get usage statistics
    total_usage = UsageRecord.query.filter_by(user_id=current_user.id).count()
    this_month_usage = UsageRecord.query.filter(
        UsageRecord.user_id == current_user.id,
        UsageRecord.created_at >= datetime.now().replace(day=1)
    ).count()
    
    # Get recent activities from UsageRecord
    recent_activities = UsageRecord.query.filter_by(user_id=current_user.id)\
        .filter(UsageRecord.created_at >= datetime.now() - timedelta(days=7))\
        .order_by(UsageRecord.created_at.desc())\
        .limit(10).all()
    
    # Get pending charges
    pending_charges = Charge.query.filter_by(
        user_id=current_user.id,
        status='PENDING'
    ).all()
    
    return render_template('dashboard.html', 
                         xml_count=xml_count,
                         danfe_count=xml_count,  # DANFE is free for each XML
                         total_usage=total_usage,
                         this_month_usage=this_month_usage,
                         recent_activities=recent_activities,
                         pending_charges=pending_charges)

@app.route('/xml-download')
@login_required
def xml_download():
    """XML download page - only shows after XMLs are downloaded"""
    return render_template('xml_download.html')

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
        
        # Check if user can use service using Stripe credit system
        from stripe_integration import PricingManager, CreditManager
        
        xml_price = PricingManager.get_service_price('xml_download')
        total_cost = len(valid_keys) * xml_price
        
        # Check if user has sufficient credits (skip for trial users)
        if not current_user.is_trial_active():
            if current_user.current_balance < total_cost:
                flash(f'Saldo insuficiente. Você precisa de R$ {total_cost:.2f} para processar {len(valid_keys)} chaves. Saldo atual: R$ {current_user.current_balance:.2f}', 'warning')
                return redirect(url_for('comprar_creditos'))
        
        # Create download job
        job_id = str(uuid.uuid4())
        job = DownloadJob(job_id, valid_keys, current_user.id)
        
        with jobs_lock:
            download_jobs[job_id] = job
        
        # Note: Credits will be deducted per successful download in automation_fixed.py
        
        # Record usage
        xml_module = ServiceModule.query.filter_by(name='xml_download').first()
        if xml_module:
            usage = UsageRecord(
                user_id=current_user.id,
                module_id=xml_module.id,
                quantity=len(valid_keys),
                cost=total_cost if not current_user.is_trial_active() else 0.0,
                description=f"Download de {len(valid_keys)} XMLs",
                invoice_keys=json.dumps(valid_keys),
                job_id=job_id
            )
            db.session.add(usage)
            db.session.commit()
        
        # Start download process in background
        thread = Thread(target=process_download_job, args=(job_id,))
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
    
    # Get statistics
    total_users = User.query.count()
    active_users = User.query.filter_by(active=True).count()
    total_usage = UsageRecord.query.count()
    total_revenue = db.session.query(db.func.sum(UsageRecord.cost)).scalar() or 0
    
    # Recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    
    # Recent usage
    recent_usage = UsageRecord.query.order_by(UsageRecord.created_at.desc()).limit(10).all()
    
    return render_template('admin_dashboard.html',
                         total_users=total_users,
                         active_users=active_users,
                         total_usage=total_usage,
                         total_revenue=total_revenue,
                         recent_users=recent_users,
                         recent_usage=recent_usage)

@app.route('/admin/users')
@login_required
def admin_users():
    """Admin users management"""
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_users.html', users=users)

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
def process_download_job(job_id):
    """Process download job in background with proper Flask context"""
    with app.app_context():  # Essential: Flask context for database operations
        from automation_fixed import InvoiceDownloader
        
        with jobs_lock:
            job = download_jobs.get(job_id)
        
        if not job:
            return
        
        try:
            job.status = "running"
            
            for i, invoice_key in enumerate(job.invoice_keys):
                downloader = None
                try:
                    # Create fresh downloader instance
                    downloader = InvoiceDownloader()
                    
                    # Download XML with user_id for database saving and charging
                    result = downloader.download_invoice_xml(invoice_key, job_id, 'xml', job.user_id)
                    
                    # Update job progress immediately
                    with jobs_lock:
                        job.processed += 1
                        logger.info(f"[Job {job_id}] Processed {job.processed}/{len(job.invoice_keys)} keys")
                    
                    if result.get('success'):
                        with jobs_lock:
                            job.successful += 1
                        
                        # Process successful download with proper database handling
                        if 'file_path' in result and os.path.exists(result['file_path']):
                            try:
                                # Read XML content from file
                                with open(result['file_path'], 'r', encoding='utf-8') as f:
                                    xml_content = f.read()
                                
                                # Use DownloadService to properly save to database with charging
                                download_success = DownloadService.process_successful_download(
                                    user_id=job.user_id,
                                    invoice_key=invoice_key,
                                    xml_content=xml_content,
                                    file_path=result['file_path'],
                                    job_id=job_id
                                )
                                
                                if download_success:
                                    filename = os.path.basename(result['file_path'])
                                    with jobs_lock:
                                        job.files.append(filename)
                                    logger.info(f"[Job {job_id}] Successfully processed and saved to database: {filename}")
                                else:
                                    logger.error(f"[Job {job_id}] Failed to save to database: {invoice_key}")
                                    
                            except Exception as db_error:
                                logger.error(f"[Job {job_id}] Database error for {invoice_key}: {db_error}")
                                # Still track the file even if database save fails
                                filename = os.path.basename(result['file_path'])
                                with jobs_lock:
                                    job.files.append(filename)
                        
                        # Fallback for file tracking
                        elif 'file_path' in result:
                            filename = os.path.basename(result['file_path'])
                            with jobs_lock:
                                job.files.append(filename)
                            logger.info(f"[Job {job_id}] Successfully downloaded: {filename}")
                        else:
                            logger.warning(f"[Job {job_id}] Success but no file_path in result")
                    else:
                        with jobs_lock:
                            job.failed += 1
                            error_msg = result.get('error', 'Unknown error')
                            job.errors.append({
                                'invoice_key': invoice_key,
                                'error': error_msg
                            })
                        logger.error(f"[Job {job_id}] Failed to download {invoice_key}: {error_msg}")
                            
                except Exception as e:
                    with jobs_lock:
                        job.processed += 1
                        job.failed += 1
                        error_msg = str(e)
                        job.errors.append({
                            'invoice_key': invoice_key,
                            'error': error_msg
                        })
                    logger.error(f"[Job {job_id}] Exception for {invoice_key}: {error_msg}")
                finally:
                    # Cleanup only after all attempts
                    if downloader:
                        try:
                            downloader.cleanup()
                        except:
                            pass
            
            with jobs_lock:
                job.status = "completed"
                job.completed_at = datetime.now()
            
            logger.info(f"[Job {job_id}] Completed - Successful: {job.successful}, Failed: {job.failed}")
            
        except Exception as e:
            logger.error(f"[Job {job_id}] Job error: {str(e)}")
            with jobs_lock:
                job.status = "failed"
                job.completed_at = datetime.now()

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
def meus_xmls():
    """Lista apenas XMLs corretamente processados com dados completos"""
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    # Filtros
    search_term = request.args.get('search', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    uf_filter = request.args.get('uf', '')
    cidade_filter = request.args.get('cidade', '')
    
    # Buscar XMLs da tabela unificada
    all_xmls_list = XMLFile.query.filter_by(user_id=current_user.id).all()
    
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
    # Verificar se usuário tem saldo para acessar módulos premium
    # Por enquanto, permitir acesso se usuário tem saldo ou está no período trial
    if current_user.current_balance < 49.90 and current_user.trial_expires_at < datetime.now():
        flash('Você precisa adquirir o módulo de etiquetas para acessar esta funcionalidade.', 'warning')
        return redirect(url_for('dashboard'))
    
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
def api_docs():
    """Documentação da API"""
    return render_template('api_docs.html', current_user=current_user)

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
def download_xml(xml_id):
    """Download arquivo XML específico"""
    # XMLFile removido - usando XMLFile
    from flask import send_file
    import io
    
    xml_record = XMLFile.query.filter_by(id=xml_id, user_id=current_user.id).first()
    
    if not xml_record:
        flash('XML não encontrado.', 'error')
        return redirect(url_for('meus_xmls'))
    
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
def generate_label_route(xml_id):
    """Gera e baixa etiqueta de transporte para um XML específico"""
    try:
        # Buscar XML primeiro na XMLFile (dados completos), depois XMLFile
        xml_record = XMLFile.query.filter_by(id=xml_id, user_id=current_user.id).first()
        xml_file = None
        
        if not xml_record:
            xml_file = XMLFile.query.filter_by(id=xml_id, user_id=current_user.id).first()
        
        if not xml_record and not xml_file:
            flash('XML não encontrado.', 'error')
            return redirect(url_for('meus_xmls'))
        
        # Usar dados da tabela encontrada
        xml_content = xml_record.xml_content if xml_record else xml_file.xml_content
        invoice_key = xml_record.invoice_key if xml_record else xml_file.invoice_key
        
        # Verificar módulo de etiquetas
        labels_module = ServiceModule.query.filter_by(name='Etiquetas de Transporte').first()
        if not labels_module:
            flash('Módulo de etiquetas não disponível.', 'error')
            return redirect(url_for('meus_xmls'))
        
        # Verificar se usuário pode usar o serviço (trial ou saldo)
        is_trial_active = current_user.trial_expires_at and current_user.trial_expires_at > datetime.now()
        if not is_trial_active and current_user.current_balance < labels_module.cost_per_use:
            flash('Você precisa adquirir o módulo de etiquetas para acessar esta funcionalidade.', 'warning')
            return redirect(url_for('comprar_creditos'))
        
        # Gerar etiqueta personalizada
        pedido_number = request.args.get('pedido', invoice_key[:5])
        area_code = request.args.get('area', '01')
        company_name = request.args.get('empresa', 'SUA EMPRESA')
        
        # Usar configurações do usuário para personalização
        company_name = current_user.company_name or 'SUA EMPRESA'
        if xml_record:
            extracted_data = extract_xml_data(xml_content)
            # Usar nome do emitente se usuário não configurou empresa
            if not current_user.company_name:
                company_name = extracted_data.get('nome_emitente', company_name)
        
        # Usar configurações salvas do usuário
        area_code = current_user.default_area_code or '01'
        logo_path = current_user.company_logo_path
        
        # Gerar etiqueta responsiva
        from responsive_label_generator import generate_responsive_label_from_database_xml
        
        # Obter configurações de papel do usuário (padrão: 100x150mm)
        paper_width = getattr(current_user, 'paper_width_mm', 100)
        paper_height = getattr(current_user, 'paper_height_mm', 150)
        
        label_buffer = generate_responsive_label_from_database_xml(
            xml_record=xml_record,
            pedido_number=pedido_number,
            area_code=area_code,
            company_name=company_name,
            company_logo_path=logo_path,
            paper_width_mm=paper_width,
            paper_height_mm=paper_height
        )
        
        # Cobrar pelo serviço apenas se não estiver em trial
        if not is_trial_active:
            current_user.deduct_balance(
                labels_module.cost_per_use,
                f"Geração de etiqueta para XML {invoice_key[:10]}..."
            )
            
            # Registrar uso
            usage_record = UsageRecord(
                user_id=current_user.id,
                module_id=labels_module.id,
                quantity=1,
                cost=labels_module.cost_per_use,
                description=f"Etiqueta gerada para XML {invoice_key[:10]}..."
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
        response.headers['Content-Disposition'] = f'inline; filename="etiqueta_transporte_{invoice_key}.pdf"'
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

@app.route('/comprar-creditos')
@login_required
def comprar_creditos():
    """Página para compra de créditos"""
    packages = PricingManager.CREDIT_PACKAGES
    
    # Calcular economia para cada pacote
    packages_with_savings = {}
    for package_id, package_data in packages.items():
        savings = PricingManager.calculate_xml_package_savings(package_id)
        packages_with_savings[package_id] = {
            **package_data,
            'savings': savings
        }
    
    return render_template('comprar_creditos.html', 
                         packages=packages_with_savings,
                         current_user=current_user)

@app.route('/create-checkout-session', methods=['POST'])
@login_required 
def create_checkout_session():
    """Criar sessão de checkout Stripe"""
    try:
        data = request.get_json()
        package_id = data.get('package_id')
        
        if not package_id:
            return jsonify({'error': 'Package ID is required'}), 400
        
        package = PricingManager.get_credit_package(package_id)
        if not package:
            return jsonify({'error': 'Invalid package'}), 400
        
        # Inicializar gerenciador Stripe
        stripe_manager = StripePaymentManager()
        
        # Criar sessão de checkout
        success_url = url_for('payment_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}'
        cancel_url = url_for('comprar_creditos', _external=True)
        
        price_data = {
            'currency': 'brl',
            'product_data': {
                'name': package['name'],
                'description': package['description']
            },
            'unit_amount': package['price_brl']
        }
        
        metadata = {
            'user_id': str(current_user.id),
            'package_id': package_id,
            'credits': str(package['credits'])
        }
        
        result = stripe_manager.create_checkout_session(
            price_data=price_data,
            success_url=success_url,
            cancel_url=cancel_url,
            customer_email=current_user.email,
            metadata=metadata
        )
        
        if result['success']:
            # Registrar transação como pendente
            transaction = StripeTransaction(
                user_id=current_user.id,
                stripe_session_id=result['session_id'],
                amount_brl=package['price_brl'] / 100,  # Converter centavos para reais
                credits_purchased=package['credits'],
                package_id=package_id,
                status='pending'
            )
            
            db.session.add(transaction)
            db.session.commit()
            
            return jsonify({'checkout_url': result['checkout_url']})
        else:
            return jsonify({'error': result['error']}), 500
            
    except Exception as e:
        logger.error(f"Error creating checkout session: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/payment-success')
@login_required
def payment_success():
    """Página de sucesso do pagamento"""
    session_id = request.args.get('session_id')
    
    if not session_id:
        flash('Sessão de pagamento não encontrada.', 'error')
        return redirect(url_for('dashboard'))
    
    # Buscar transação no banco
    transaction = StripeTransaction.query.filter_by(
        stripe_session_id=session_id,
        user_id=current_user.id
    ).first()
    
    if not transaction:
        flash('Transação não encontrada.', 'error')
        return redirect(url_for('dashboard'))
    
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
    """Webhook para processar eventos do Stripe"""
    payload = request.get_data()
    sig_header = request.headers.get('Stripe-Signature')
    endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    if not endpoint_secret:
        logger.error("STRIPE_WEBHOOK_SECRET not configured")
        return '', 400
    
    try:
        result = process_stripe_webhook(payload, sig_header, endpoint_secret)
        
        if result['success']:
            return '', 200
        else:
            logger.error(f"Webhook processing failed: {result.get('error')}")
            return '', 400
            
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return '', 400

@app.route('/historico-creditos')
@login_required
def historico_creditos():
    """Histórico de uso de créditos"""
    usage_history = CreditManager.get_usage_history(current_user.id, days=30)
    
    # Buscar transações Stripe
    stripe_transactions = StripeTransaction.query.filter_by(
        user_id=current_user.id
    ).order_by(StripeTransaction.created_at.desc()).limit(20).all()
    
    return render_template('historico_creditos_simple.html',
                         usage_history=usage_history,
                         stripe_transactions=stripe_transactions,
                         current_user=current_user)

@app.route('/api/user/balance')
@login_required
def api_user_balance():
    """API para obter saldo atual do usuário"""
    return jsonify({
        'balance': current_user.current_balance or 0.0,
        'is_trial': current_user.is_trial_active(),
        'trial_expires': current_user.trial_expires_at.isoformat() if current_user.trial_expires_at else None
    })

# Modificar função de dedução de créditos para XML downloads
def charge_for_xml_download(user_id: int, invoice_key: str) -> bool:
    """Cobra pelo download de XML se não estiver em período de teste"""
    price = PricingManager.get_service_price('xml_download')
    
    return CreditManager.deduct_credits(
        user_id=user_id,
        amount=price,
        description=f"Download XML: {invoice_key[:10]}...",
        service_type="xml_download"
    )

@app.route('/configurar-etiquetas', methods=['GET', 'POST'])
@login_required
def configurar_etiquetas():
    """Configurar etiquetas personalizadas"""
    if request.method == 'POST':
        try:
            # Verificar se é uma requisição AJAX
            if request.is_json or request.headers.get('Content-Type', '').startswith('application/json'):
                return jsonify({'error': 'JSON não suportado para upload de arquivos'}), 400
            
            # Atualizar dados da empresa
            current_user.company_name = request.form.get('company_name', '').strip()
            current_user.company_subtitle = request.form.get('company_subtitle', '').strip()
            current_user.default_area_code = request.form.get('area_code', '01').strip()
            
            # Processar upload de logo
            if 'company_logo' in request.files:
                logo_file = request.files['company_logo']
                if logo_file and logo_file.filename:
                    # Validar tipo de arquivo
                    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
                    file_extension = logo_file.filename.rsplit('.', 1)[1].lower()
                    
                    if file_extension in allowed_extensions:
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
                        
                        flash('Logo enviado com sucesso!', 'success')
                    else:
                        flash('Formato de arquivo não suportado. Use PNG, JPG, JPEG ou GIF.', 'error')
            
            db.session.commit()
            flash('Configurações de etiquetas salvas com sucesso!', 'success')
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Erro ao salvar configurações: {e}")
            flash('Erro ao salvar configurações. Tente novamente.', 'error')
    
    return render_template('configurar_etiquetas.html')

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
def serve_logo(filename):
    """Servir logos das empresas"""
    return send_from_directory(os.path.join('static', 'uploads', 'logos'), filename)

# API endpoint para salvar configurações via AJAX
@app.route('/api/save-label-config', methods=['POST'])
@login_required
def save_label_config():
    """Salvar configurações de etiquetas via AJAX"""
    try:
        # Atualizar dados da empresa
        current_user.company_name = request.form.get('company_name', '').strip()
        current_user.company_subtitle = request.form.get('company_subtitle', '').strip()
        current_user.default_area_code = request.form.get('area_code', '01').strip()
        
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
        
        # Verificar se usuário pode usar o serviço (trial ou saldo)
        is_trial_active = current_user.trial_expires_at and current_user.trial_expires_at > datetime.now()
        if not is_trial_active and current_user.current_balance < labels_module.cost_per_use:
            flash('Você precisa adquirir o módulo de etiquetas para acessar esta funcionalidade.', 'warning')
            return redirect(url_for('comprar_creditos'))
        
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
        
        # Gerar etiquetas múltiplas responsivas
        from responsive_label_generator import generate_multiple_responsive_labels_from_volumes
        
        labels = generate_multiple_responsive_labels_from_volumes(
            xml_record=xml_data,
            volumes_config=volumes_config,
            company_name=company_name,
            company_logo_path=logo_path,
            paper_width_mm=paper_width_mm,
            paper_height_mm=paper_height_mm,
            area_code=area_code
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
        
        flash(f'{len(labels)} etiquetas geradas com sucesso!', 'success')
        return response
        
    except Exception as e:
        logger.error(f"Erro ao gerar etiquetas personalizadas: {e}")
        flash('Erro ao gerar etiquetas personalizadas.', 'error')
        return redirect(url_for('label_generator', xml_id=xml_id))


# Importar admin panel
try:
    from admin_panel import init_admin_panel
    init_admin_panel(app)
except ImportError:
    logger.warning("Admin panel not available")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)