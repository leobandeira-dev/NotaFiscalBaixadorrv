"""
Aplicação principal corrigida com sistema de download simplificado
"""
import os
import json
import uuid
import logging
import time
from datetime import datetime
from threading import Thread, Lock
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_required, current_user
from werkzeug.middleware.proxy_fix import ProxyFix
from models import db, User, XMLFile, DownloadJob as DBDownloadJob
from simple_production_robot import SimpleProductionRobot

# Configurar aplicação
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    "pool_recycle": 300,
}

db.init_app(app)

# Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Job tracking
download_jobs = {}
jobs_lock = Lock()

logger = logging.getLogger(__name__)

def is_production():
    """Detecta ambiente de produção"""
    return 'replit.dev' in os.environ.get('REPLIT_DEV_DOMAIN', '')

def validate_invoice_keys(keys_text):
    """Valida chaves de nota fiscal"""
    if not keys_text or not keys_text.strip():
        return []
    
    valid_keys = []
    for line in keys_text.strip().split('\n'):
        key = line.strip()
        if len(key) == 44 and key.isdigit():
            valid_keys.append(key)
    
    return valid_keys

class SimpleJob:
    """Job simplificado para downloads"""
    def __init__(self, job_id, keys, user_id):
        self.job_id = job_id
        self.invoice_keys = keys
        self.user_id = user_id
        self.total_keys = len(keys)
        self.processed = 0
        self.successful = 0
        self.failed = 0
        self.status = "starting"
        self.files = []
        self.errors = []
        self.start_time = datetime.utcnow()
        self.end_time = None

    @property
    def progress_percentage(self):
        return round((self.processed / self.total_keys) * 100, 2) if self.total_keys > 0 else 0

def process_downloads_directly(job_id, user_id, invoice_keys):
    """Processa downloads sem threading complexo"""
    try:
        with app.app_context():
            logger.info(f"🎯 Processando job {job_id} com {len(invoice_keys)} chaves")
            
            # Buscar job
            with jobs_lock:
                if job_id not in download_jobs:
                    logger.error(f"Job {job_id} não encontrado")
                    return
                job = download_jobs[job_id]
            
            job.status = "running"
            
            # Processar cada XML
            for i, invoice_key in enumerate(invoice_keys):
                try:
                    logger.info(f"🔄 Processando {i+1}/{len(invoice_keys)}: {invoice_key}")
                    
                    # Download com robô simplificado
                    result = SimpleProductionRobot.simple_download(
                        invoice_key=invoice_key,
                        job_id=job_id,
                        user_id=user_id
                    )
                    
                    # Atualizar progresso
                    job.processed = i + 1
                    
                    if result.get('success'):
                        job.successful += 1
                        if result.get('file_path'):
                            job.files.append(result['file_path'])
                        logger.info(f"✅ Sucesso: {invoice_key}")
                    else:
                        job.failed += 1
                        job.errors.append({
                            'invoice_key': invoice_key,
                            'error': result.get('error', 'Erro desconhecido')
                        })
                        logger.warning(f"❌ Falha: {invoice_key}")
                    
                    time.sleep(1)  # Pausa entre downloads
                    
                except Exception as e:
                    logger.error(f"💥 Erro processando {invoice_key}: {str(e)}")
                    job.processed = i + 1
                    job.failed += 1
                    job.errors.append({
                        'invoice_key': invoice_key,
                        'error': str(e)
                    })
            
            # Finalizar
            job.status = "completed" if job.successful > 0 else "failed"
            job.end_time = datetime.utcnow()
            
            logger.info(f"🎉 Job {job_id} finalizado: {job.successful} sucessos, {job.failed} falhas")
            
    except Exception as e:
        logger.error(f"💥💥 Erro crítico no job {job_id}: {str(e)}")
        with jobs_lock:
            if job_id in download_jobs:
                download_jobs[job_id].status = "failed"

@app.route('/xml-download', methods=['GET', 'POST'])
@login_required
def xml_download():
    """Página de download de XMLs"""
    if request.method == 'POST':
        try:
            keys_text = request.form.get('invoice_keys', '')
            valid_keys = validate_invoice_keys(keys_text)
            
            if not valid_keys:
                flash('Nenhuma chave válida encontrada. Verifique o formato (44 dígitos).', 'error')
                return render_template('xml_download.html')
            
            # Criar job
            job_id = str(uuid.uuid4())
            job = SimpleJob(job_id, valid_keys, current_user.id)
            
            with jobs_lock:
                download_jobs[job_id] = job
            
            # Processar downloads
            if is_production():
                # Em produção: processamento direto sem threading
                thread = Thread(target=process_downloads_directly, 
                              args=(job_id, current_user.id, valid_keys))
                thread.daemon = True
                thread.start()
            else:
                # Em desenvolvimento: usar sistema normal
                process_downloads_directly(job_id, current_user.id, valid_keys)
            
            flash(f'Download iniciado para {len(valid_keys)} chave(s).', 'success')
            return redirect(url_for('download_status', job_id=job_id))
            
        except Exception as e:
            logger.error(f"Erro no download: {str(e)}")
            flash('Erro interno. Tente novamente.', 'error')
            return render_template('xml_download.html')
    
    return render_template('xml_download.html')

@app.route('/download/<job_id>')
@login_required
def download_status(job_id):
    """Status do download"""
    with jobs_lock:
        job = download_jobs.get(job_id)
    
    if not job:
        flash('Job não encontrado.', 'error')
        return redirect(url_for('xml_download'))
    
    return render_template('download_status.html', job=job)

@app.route('/api/job_status/<job_id>')
def api_job_status(job_id):
    """API para status do job"""
    with jobs_lock:
        job = download_jobs.get(job_id)
    
    if not job:
        return jsonify({'error': 'Job não encontrado'}), 404
    
    return jsonify({
        'job_id': job.job_id,
        'status': job.status,
        'processed': job.processed,
        'successful': job.successful,
        'failed': job.failed,
        'total_keys': job.total_keys,
        'progress_percentage': job.progress_percentage,
        'files': job.files,
        'errors': job.errors
    })

@app.route('/')
def index():
    """Página inicial"""
    return render_template('index.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000, debug=True)