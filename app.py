import os
import logging
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from threading import Thread, Lock
import uuid
import zipfile
from datetime import datetime
import json

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "default_secret_key_for_development")

# Global variables for tracking downloads
download_jobs = {}
jobs_lock = Lock()

# Ensure downloads directory exists
os.makedirs('downloads', exist_ok=True)

class DownloadJob:
    def __init__(self, job_id, invoice_keys):
        self.job_id = job_id
        self.invoice_keys = invoice_keys
        self.total_keys = len(invoice_keys)
        self.processed = 0
        self.successful = 0
        self.failed = 0
        self.status = "starting"  # starting, running, completed, failed
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

@app.route('/')
def index():
    """Main page with form to input invoice keys"""
    return render_template('index.html')

@app.route('/submit_keys', methods=['POST'])
def submit_keys():
    """Handle form submission with invoice keys"""
    try:
        keys_text = request.form.get('invoice_keys', '').strip()
        
        if not keys_text:
            flash('Por favor, insira pelo menos uma chave de nota fiscal.', 'error')
            return redirect(url_for('index'))
        
        # Parse invoice keys - split by lines and remove empty lines
        invoice_keys = [key.strip() for key in keys_text.split('\n') if key.strip()]
        
        if not invoice_keys:
            flash('Nenhuma chave válida encontrada.', 'error')
            return redirect(url_for('index'))
        
        # Validate invoice keys format (44 digits)
        valid_keys = []
        invalid_keys = []
        
        for key in invoice_keys:
            # Remove any non-digit characters
            clean_key = ''.join(filter(str.isdigit, key))
            if len(clean_key) == 44:
                valid_keys.append(clean_key)
            else:
                invalid_keys.append(key)
        
        if not valid_keys:
            flash('Nenhuma chave válida encontrada. Chaves devem ter 44 dígitos.', 'error')
            return redirect(url_for('index'))
        
        if invalid_keys:
            flash(f'Chaves inválidas ignoradas: {len(invalid_keys)}', 'warning')
        
        # Create download job
        job_id = str(uuid.uuid4())
        job = DownloadJob(job_id, valid_keys)
        
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
        flash('Erro interno do servidor. Tente novamente.', 'error')
        return redirect(url_for('index'))

@app.route('/download/<job_id>')
def download_status(job_id):
    """Display download progress page"""
    with jobs_lock:
        job = download_jobs.get(job_id)
    
    if not job:
        flash('Job de download não encontrado.', 'error')
        return redirect(url_for('index'))
    
    return render_template('download.html', job=job)

@app.route('/api/job_status/<job_id>')
def job_status(job_id):
    """API endpoint to get job status"""
    with jobs_lock:
        job = download_jobs.get(job_id)
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    return jsonify(job.to_dict())

@app.route('/download_zip/<job_id>')
def download_zip(job_id):
    """Download all files as ZIP"""
    with jobs_lock:
        job = download_jobs.get(job_id)
    
    if not job or job.status != 'completed':
        flash('Download não disponível.', 'error')
        return redirect(url_for('index'))
    
    if not job.downloaded_files:
        flash('Nenhum arquivo foi baixado com sucesso.', 'error')
        return redirect(url_for('download_status', job_id=job_id))
    
    try:
        # Create ZIP file
        zip_filename = f'xml_invoices_{job_id[:8]}.zip'
        zip_path = os.path.join('downloads', zip_filename)
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in job.downloaded_files:
                if os.path.exists(file_path):
                    arcname = os.path.basename(file_path)
                    zipf.write(file_path, arcname)
        
        return send_file(zip_path, as_attachment=True, download_name=zip_filename)
        
    except Exception as e:
        logger.error(f"Error creating ZIP file: {str(e)}")
        flash('Erro ao criar arquivo ZIP.', 'error')
        return redirect(url_for('download_status', job_id=job_id))

def process_download_job(job_id):
    """Process download job in background"""
    from automation import InvoiceDownloader
    
    with jobs_lock:
        job = download_jobs.get(job_id)
    
    if not job:
        return
    
    try:
        job.status = "running"
        downloader = InvoiceDownloader()
        
        for i, invoice_key in enumerate(job.invoice_keys):
            try:
                logger.info(f"Processing invoice key {i+1}/{job.total_keys}: {invoice_key}")
                
                # Download XML for this invoice key
                result = downloader.download_invoice_xml(invoice_key, job_id)
                
                job.processed += 1
                
                if result['success']:
                    job.successful += 1
                    job.downloaded_files.append(result['file_path'])
                    logger.info(f"Successfully downloaded: {result['file_path']}")
                else:
                    job.failed += 1
                    job.errors.append({
                        'invoice_key': invoice_key,
                        'error': result['error']
                    })
                    logger.error(f"Failed to download {invoice_key}: {result['error']}")
                
            except Exception as e:
                job.processed += 1
                job.failed += 1
                error_msg = f"Erro inesperado: {str(e)}"
                job.errors.append({
                    'invoice_key': invoice_key,
                    'error': error_msg
                })
                logger.error(f"Unexpected error processing {invoice_key}: {str(e)}")
        
        job.status = "completed"
        job.end_time = datetime.now()
        
        # Clean up selenium driver
        downloader.cleanup()
        
        logger.info(f"Job {job_id} completed. Success: {job.successful}, Failed: {job.failed}")
        
    except Exception as e:
        job.status = "failed"
        job.end_time = datetime.now()
        logger.error(f"Job {job_id} failed with error: {str(e)}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
