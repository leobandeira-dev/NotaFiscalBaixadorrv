"""
Sistema completo de XML Downloader com autenticação e cobrança
"""

import os
import json
import uuid
import logging
from datetime import datetime, timedelta
from threading import Thread, Lock
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.middleware.proxy_fix import ProxyFix
from models import db, User, ServiceModule, UsageRecord, Charge, SystemSettings, init_default_data
from asaas_integration import AsaasAPI, create_minimum_charge, process_webhook_payment

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

# Initialize database
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Faça login para acessar esta página.'
login_manager.login_message_category = 'info'

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
        self.downloaded_files = []
        self.errors = []
        self.start_time = datetime.now()
        self.end_time = None

    def to_dict(self):
        return {
            'job_id': self.job_id,
            'total_keys': self.total_keys,
            'processed': self.processed,
            'successful': self.successful,
            'failed': self.failed,
            'status': self.status,
            'downloaded_files': self.downloaded_files,
            'errors': self.errors,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'progress_percentage': round((self.processed / self.total_keys) * 100, 2) if self.total_keys > 0 else 0
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
    return render_template('landing.html')

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

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    # Get user usage statistics
    total_usage = UsageRecord.query.filter_by(user_id=current_user.id).count()
    this_month_usage = UsageRecord.query.filter(
        UsageRecord.user_id == current_user.id,
        UsageRecord.created_at >= datetime.now().replace(day=1)
    ).count()
    
    # Get recent usage
    recent_usage = UsageRecord.query.filter_by(user_id=current_user.id).order_by(
        UsageRecord.created_at.desc()
    ).limit(10).all()
    
    # Get pending charges
    pending_charges = Charge.query.filter_by(
        user_id=current_user.id,
        status='PENDING'
    ).all()
    
    return render_template('dashboard.html', 
                         total_usage=total_usage,
                         this_month_usage=this_month_usage,
                         recent_usage=recent_usage,
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
        
        # Check if user can use service
        total_cost = len(valid_keys) * 0.10  # R$ 0.10 per XML
        
        if not current_user.can_use_service(total_cost):
            if current_user.is_trial_active():
                flash('Seu período de teste expirou. Recarregue seu saldo para continuar.', 'warning')
            else:
                flash(f'Saldo insuficiente. Você precisa de R$ {total_cost:.2f} para processar {len(valid_keys)} chaves.', 'warning')
            return redirect(url_for('add_balance'))
        
        # Create download job
        job_id = str(uuid.uuid4())
        job = DownloadJob(job_id, valid_keys, current_user.id)
        
        with jobs_lock:
            download_jobs[job_id] = job
        
        # Deduct balance if not in trial
        if not current_user.is_trial_active():
            current_user.deduct_balance(total_cost, f"Download de {len(valid_keys)} XMLs")
        
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
    
    # Check if user can use DANFE service
    danfe_cost = job.successful * 0.15  # R$ 0.15 per DANFE
    
    if not current_user.can_use_service(danfe_cost):
        flash(f'Saldo insuficiente para gerar DANFE. Custo: R$ {danfe_cost:.2f}', 'warning')
        return redirect(url_for('add_balance'))
    
    # Deduct balance if not in trial
    if not current_user.is_trial_active():
        current_user.deduct_balance(danfe_cost, f"Geração de {job.successful} DANFEs")
    
    # Record usage
    danfe_module = ServiceModule.query.filter_by(name='danfe_generation').first()
    if danfe_module:
        usage = UsageRecord(
            user_id=current_user.id,
            module_id=danfe_module.id,
            quantity=job.successful,
            cost=danfe_cost if not current_user.is_trial_active() else 0.0,
            description=f"Geração de {job.successful} DANFEs",
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
    """Process download job in background"""
    from automation import InvoiceDownloader
    
    with jobs_lock:
        job = download_jobs.get(job_id)
    
    if not job:
        return
    
    try:
        job.status = "running"
        
        for i, invoice_key in enumerate(job.invoice_keys):
            try:
                # Create fresh downloader instance
                downloader = InvoiceDownloader()
                
                # Download XML only initially
                result = downloader.download_invoice_xml(invoice_key, job_id, 'xml')
                
                job.processed += 1
                
                if result['success']:
                    job.successful += 1
                    job.downloaded_files.append(result['file_path'])
                else:
                    job.failed += 1
                    job.errors.append({
                        'invoice_key': invoice_key,
                        'error': result['error']
                    })
                
                # Cleanup
                if downloader:
                    try:
                        downloader.cleanup()
                    except:
                        pass
                        
            except Exception as e:
                job.processed += 1
                job.failed += 1
                job.errors.append({
                    'invoice_key': invoice_key,
                    'error': str(e)
                })
        
        job.status = "completed"
        job.end_time = datetime.now()
        
    except Exception as e:
        logger.error(f"Job error: {str(e)}")
        job.status = "failed"

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
@app.route('/api/job_status/<job_id>')
@login_required
def job_status(job_id):
    """Get job status"""
    with jobs_lock:
        job = download_jobs.get(job_id)
        
        if not job or job.user_id != current_user.id:
            return jsonify({'error': 'Job not found'}), 404
        
        return jsonify(job.to_dict())

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)