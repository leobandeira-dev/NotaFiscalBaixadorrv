"""
CROSS XML Downloader Pro - Sistema Completo
Aplicação Flask com autenticação, cobrança e processamento XML
"""

import os
import sys
import logging
import json
import uuid
import threading
from datetime import datetime, timedelta
from threading import Thread, Lock
from werkzeug.middleware.proxy_fix import ProxyFix
import pytz

# Flask imports
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_file, session, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

# SQLAlchemy imports
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

# Initialize Flask app
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import models and database instance
from models import db, User, XMLFile, ServiceModule, UsageRecord, Charge, CreditBalance, UserActivity

# Initialize database with app
db.init_app(app)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Download job management
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
        self.files = []
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
            'files': self.files,
            'errors': self.errors,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'progress_percentage': round((self.processed / self.total_keys) * 100, 2) if self.total_keys > 0 else 0
        }

# Background processing function
def process_download_job(job_id):
    """Process download job in background with proper Flask context"""
    with app.app_context():
        try:
            from automation_fixed import InvoiceDownloader
            from simple_credit_system import get_user_xml_balance, charge_xml_credit
            
            with jobs_lock:
                job = download_jobs.get(job_id)
            
            if not job:
                return
            
            job.status = "running"
            downloader = InvoiceDownloader()
            
            for i, invoice_key in enumerate(job.invoice_keys):
                try:
                    # Check if user has sufficient credits
                    if not charge_for_xml_download(job.user_id, invoice_key):
                        job.errors.append(f"Créditos insuficientes para {invoice_key}")
                        job.failed += 1
                    else:
                        # Download XML
                        success, file_path, error = downloader.download_xml(invoice_key)
                        
                        if success and file_path:
                            job.files.append(os.path.basename(file_path))
                            job.successful += 1
                        else:
                            job.errors.append(error or f"Erro no download de {invoice_key}")
                            job.failed += 1
                    
                    job.processed += 1
                    
                except Exception as e:
                    job.errors.append(f"Erro processando {invoice_key}: {str(e)}")
                    job.failed += 1
                    job.processed += 1
            
            job.status = "completed"
            job.end_time = datetime.now()
            
        except Exception as e:
            logger.error(f"Error in process_download_job: {str(e)}")
            if job_id in download_jobs:
                download_jobs[job_id].status = "failed"

# Main routes
@app.route('/')
def index():
    """Landing page"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('landing.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    from simple_credit_system import get_user_xml_balance, get_trial_status
    
    # Get user balance and trial status
    xml_balance = get_user_xml_balance(current_user.id)
    trial_status = get_trial_status(current_user.id)
    
    # Get recent XMLs
    recent_xmls = XMLFile.query.filter_by(user_id=current_user.id)\
                             .order_by(XMLFile.created_at.desc())\
                             .limit(5).all()
    
    # Get recent activities
    from new_app import get_user_recent_activities
    recent_activities = get_user_recent_activities(current_user.id, limit=5)
    
    return render_template('dashboard.html',
                         xml_balance=xml_balance,
                         trial_status=trial_status,
                         recent_xmls=recent_xmls,
                         recent_activities=recent_activities)

@app.route('/xml-download')
@login_required
def xml_download():
    """XML download page"""
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
        
        # Validate keys format
        valid_keys = []
        for key in invoice_keys:
            if len(key) == 44 and key.isdigit():
                valid_keys.append(key)
            else:
                flash(f'Chave inválida: {key}. Deve conter exatamente 44 dígitos.', 'error')
                return redirect(url_for('xml_download'))
        
        # Create download job
        job_id = str(uuid.uuid4())
        job = DownloadJob(job_id, valid_keys, current_user.id)
        
        with jobs_lock:
            download_jobs[job_id] = job
        
        # Start download process in background
        thread = Thread(target=process_download_job, args=(job_id,))
        thread.daemon = True
        thread.start()
        
        flash(f'Processo de download iniciado para {len(valid_keys)} chave(s).', 'success')
        return redirect(url_for('download_status', job_id=job_id))
        
    except Exception as e:
        logger.error(f"Error in submit_keys: {str(e)}")
        flash('Erro interno. Tente novamente.', 'error')
        return redirect(url_for('xml_download'))

@app.route('/download/<job_id>')
@login_required
def download_status(job_id):
    """Display download progress"""
    with jobs_lock:
        job = download_jobs.get(job_id)
    
    if not job or job.user_id != current_user.id:
        flash('Job de download não encontrado.', 'error')
        return redirect(url_for('xml_download'))
    
    return render_template('download_status.html', job=job)

@app.route('/api/job_status/<job_id>')
@login_required
def job_status(job_id):
    """API endpoint to get job status"""
    with jobs_lock:
        job = download_jobs.get(job_id)
        
        if not job or job.user_id != current_user.id:
            return jsonify({'error': 'Job not found'}), 404
        
        response = job.to_dict()
        return jsonify(response)

# Authentication routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Email ou senha inválidos.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Email já cadastrado.', 'error')
            return render_template('register.html')
        
        user = User(email=email, name=name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('Conta criada com sucesso! Você tem 7 dias de teste gratuito.', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    return redirect(url_for('index'))

# Initialize database and default data
def init_default_data():
    """Initialize default system data"""
    # Simple initialization without complex model creation
    try:
        logger.info("Default modules would be initialized here")
    except Exception as e:
        logger.error(f"Error initializing default data: {str(e)}")

# Create tables and initialize data
with app.app_context():
    try:
        db.create_all()
        init_default_data()
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {str(e)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)