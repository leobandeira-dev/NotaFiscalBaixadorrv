import os
import logging
import time
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from flask_cors import CORS
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

# Enable CORS for API access
CORS(app)

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
        self.callback_url = None  # Optional webhook URL for API usage
        self.download_type = 'xml'  # xml, danfe, both

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
        download_type = request.form.get('download_type', 'xml').strip()
        
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
        job.download_type = download_type  # Store download type in job
        
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
        
        # Check for untracked downloaded files
        if job.status in ["running", "completed"] and job.processed == 0:
            logger.info(f"Checking for untracked downloads for job {job_id}")
            
            # Look for files that match this job's invoice keys
            downloads_dir = 'downloads'
            if os.path.exists(downloads_dir):
                for invoice_key in job.invoice_keys:
                    file_path = os.path.join(downloads_dir, f"{invoice_key}.xml")
                    if os.path.exists(file_path) and file_path not in job.downloaded_files:
                        # Found a file that was downloaded but not tracked
                        logger.info(f"Found untracked download: {file_path}")
                        job.downloaded_files.append(file_path)
                        job.successful += 1
                        job.processed += 1
                        
                        # If all files are processed, mark as completed
                        if job.processed >= job.total_keys:
                            job.status = "completed"
                            job.end_time = datetime.now()
                            logger.info(f"Job {job_id} marked as completed after finding untracked files")
        
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

@app.route('/api-docs')
def api_docs():
    """API Documentation page"""
    return render_template('api_docs.html')

@app.route('/download_file/<job_id>/<filename>')
def download_individual_file(job_id, filename):
    """Download individual XML file"""
    with jobs_lock:
        job = download_jobs.get(job_id)
    
    if not job:
        flash('Job de download não encontrado.', 'error')
        return redirect(url_for('index'))
    
    # Find the file in downloaded files
    file_path = None
    for downloaded_file in job.downloaded_files:
        if os.path.basename(downloaded_file) == filename:
            file_path = downloaded_file
            break
    
    if not file_path or not os.path.exists(file_path):
        flash('Arquivo não encontrado.', 'error')
        return redirect(url_for('download_status', job_id=job_id))
    
    try:
        return send_file(file_path, as_attachment=True, download_name=filename)
    except Exception as e:
        logger.error(f"Error sending file {filename}: {str(e)}")
        flash('Erro ao enviar arquivo.', 'error')
        return redirect(url_for('download_status', job_id=job_id))

@app.route('/test_automation')
def test_automation():
    """Test the automation system connectivity"""
    try:
        from automation_fixed import InvoiceDownloader
        
        downloader = InvoiceDownloader()
        result = downloader.test_connection()
        downloader.cleanup()
        
        return jsonify({
            'test_result': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error testing automation: {str(e)}")
        return jsonify({
            'test_result': {
                'success': False,
                'error': str(e)
            },
            'timestamp': datetime.now().isoformat()
        }), 500

def process_download_job(job_id):
    """Process download job in background"""
    from automation_fixed import InvoiceDownloader
    
    with jobs_lock:
        job = download_jobs.get(job_id)
    
    if not job:
        return
    
    try:
        job.status = "running"
        
        for i, invoice_key in enumerate(job.invoice_keys):
            try:
                logger.info(f"Processing invoice key {i+1}/{job.total_keys}: {invoice_key}")
                
                # Create fresh downloader instance for each key to prevent crashes
                downloader = None
                try:
                    downloader = InvoiceDownloader()
                    
                    # Download based on job download type
                    download_type = getattr(job, 'download_type', 'xml')
                    
                    if download_type == 'both':
                        # Download both XML and DANFE
                        xml_result = downloader.download_invoice_xml(invoice_key, job_id, 'xml')
                        danfe_result = downloader.download_invoice_xml(invoice_key, job_id, 'danfe')
                        
                        # Consider successful if at least one succeeds
                        if xml_result['success'] or danfe_result['success']:
                            result = {'success': True, 'file_paths': []}
                            if xml_result['success']:
                                result['file_paths'].append(xml_result['file_path'])
                            if danfe_result['success']:
                                result['file_paths'].append(danfe_result['file_path'])
                        else:
                            result = {
                                'success': False,
                                'error': f"XML: {xml_result.get('error', 'erro desconhecido')}, DANFE: {danfe_result.get('error', 'erro desconhecido')}"
                            }
                    else:
                        # Download single type
                        result = downloader.download_invoice_xml(invoice_key, job_id, download_type)
                    
                    # Update job status with thread safety
                    job.processed += 1
                    
                    if result['success']:
                        job.successful += 1
                        if download_type == 'both':
                            # Handle multiple files
                            for file_path in result['file_paths']:
                                job.downloaded_files.append(file_path)
                                logger.info(f"Successfully downloaded: {file_path}")
                        else:
                            # Handle single file
                            job.downloaded_files.append(result['file_path'])
                            logger.info(f"Successfully downloaded: {result['file_path']}")
                    else:
                        job.failed += 1
                        job.errors.append({
                            'invoice_key': invoice_key,
                            'error': result['error']
                        })
                        logger.error(f"Failed to download {invoice_key}: {result['error']}")
                    
                    # Log current progress
                    progress = (job.processed / job.total_keys) * 100
                    logger.info(f"Progress: {job.processed}/{job.total_keys} ({progress:.1f}%) - Success: {job.successful}, Failed: {job.failed}")
                
                except Exception as download_error:
                    job.processed += 1
                    job.failed += 1
                    error_msg = f"Erro no download: {str(download_error)}"
                    job.errors.append({
                        'invoice_key': invoice_key,
                        'error': error_msg
                    })
                    logger.error(f"Download error for {invoice_key}: {str(download_error)}")
                
                finally:
                    # Always cleanup the driver after each download
                    if downloader:
                        try:
                            downloader.cleanup()
                        except Exception as cleanup_error:
                            logger.warning(f"Error cleaning up driver: {cleanup_error}")
                
                # Small delay between downloads to prevent overwhelming the server
                time.sleep(2)
                
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
        
        logger.info(f"Job {job_id} completed. Success: {job.successful}, Failed: {job.failed}")
        
    except Exception as e:
        job.status = "failed"
        job.end_time = datetime.now()
        logger.error(f"Job {job_id} failed with error: {str(e)}")

# API Endpoints
@app.route('/api/v1/health', methods=['GET'])
def api_health():
    """API Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': '1.0',
        'service': 'XML Downloader API',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/v1/jobs', methods=['POST'])
def api_create_job():
    """Create a new download job via API"""
    try:
        data = request.get_json()
        
        if not data or 'invoice_keys' not in data:
            return jsonify({
                'error': 'Missing invoice_keys in request body',
                'code': 'MISSING_INVOICE_KEYS'
            }), 400
        
        invoice_keys = data['invoice_keys']
        
        if not isinstance(invoice_keys, list) or len(invoice_keys) == 0:
            return jsonify({
                'error': 'invoice_keys must be a non-empty list',
                'code': 'INVALID_INVOICE_KEYS'
            }), 400
        
        # Validate invoice keys format (44 digits)
        invalid_keys = []
        for key in invoice_keys:
            if not isinstance(key, str) or len(key) != 44 or not key.isdigit():
                invalid_keys.append(key)
        
        if invalid_keys:
            return jsonify({
                'error': 'Invalid invoice key format. Must be 44 digits.',
                'code': 'INVALID_KEY_FORMAT',
                'invalid_keys': invalid_keys
            }), 400
        
        # Create download job
        job_id = str(uuid.uuid4())
        job = DownloadJob(job_id, invoice_keys)
        
        if 'callback_url' in data:
            job.callback_url = data['callback_url']
        
        with jobs_lock:
            download_jobs[job_id] = job
        
        # Start background processing
        thread = Thread(target=process_download_job, args=(job_id,))
        thread.daemon = True
        thread.start()
        
        logger.info(f"API: Created job {job_id} with {len(invoice_keys)} keys")
        
        return jsonify({
            'job_id': job_id,
            'status': 'created',
            'total_keys': len(invoice_keys),
            'created_at': job.start_time.isoformat()
        }), 201
        
    except Exception as e:
        logger.error(f"API: Error creating job: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@app.route('/api/v1/jobs', methods=['GET'])
def api_list_jobs():
    """List all jobs with filtering"""
    try:
        status_filter = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        with jobs_lock:
            all_jobs = list(download_jobs.values())
            
            if status_filter:
                all_jobs = [job for job in all_jobs if job.status == status_filter]
            
            all_jobs.sort(key=lambda x: x.start_time, reverse=True)
            
            total = len(all_jobs)
            jobs_page = all_jobs[offset:offset + limit]
            
            formatted_jobs = []
            for job in jobs_page:
                formatted_jobs.append({
                    'job_id': job.job_id,
                    'status': job.status,
                    'total_keys': job.total_keys,
                    'processed': job.processed,
                    'successful': job.successful,
                    'failed': job.failed,
                    'created_at': job.start_time.isoformat() if job.start_time else None,
                    'completed_at': job.end_time.isoformat() if job.end_time else None
                })
            
            return jsonify({
                'jobs': formatted_jobs,
                'total': total,
                'limit': limit,
                'offset': offset
            })
            
    except Exception as e:
        logger.error(f"API: Error listing jobs: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@app.route('/api/v1/jobs/<job_id>/files', methods=['GET'])
def api_list_job_files(job_id):
    """List files for a specific job"""
    try:
        with jobs_lock:
            job = download_jobs.get(job_id)
            
            if not job:
                return jsonify({
                    'error': 'Job not found',
                    'code': 'JOB_NOT_FOUND'
                }), 404
            
            files = []
            for file_path in job.downloaded_files:
                if os.path.exists(file_path):
                    filename = os.path.basename(file_path)
                    file_size = os.path.getsize(file_path)
                    
                    files.append({
                        'filename': filename,
                        'size': file_size,
                        'download_url': f'/api/v1/jobs/{job_id}/files/{filename}'
                    })
            
            return jsonify({
                'job_id': job_id,
                'files': files
            })
            
    except Exception as e:
        logger.error(f"API: Error listing job files: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@app.route('/api/v1/jobs/<job_id>/files/<filename>', methods=['GET'])
def api_download_file(job_id, filename):
    """Download a specific file from a job"""
    try:
        with jobs_lock:
            job = download_jobs.get(job_id)
            
            if not job:
                return jsonify({
                    'error': 'Job not found',
                    'code': 'JOB_NOT_FOUND'
                }), 404
            
            file_path = None
            for downloaded_file in job.downloaded_files:
                if os.path.basename(downloaded_file) == filename:
                    file_path = downloaded_file
                    break
            
            if not file_path or not os.path.exists(file_path):
                return jsonify({
                    'error': 'File not found',
                    'code': 'FILE_NOT_FOUND'
                }), 404
            
            return send_file(file_path, as_attachment=True, download_name=filename)
            
    except Exception as e:
        logger.error(f"API: Error downloading file: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@app.route('/api/v1/test', methods=['POST'])
def api_test_connection():
    """Test connection to invoice system"""
    try:
        from automation_fixed import InvoiceDownloader
        
        downloader = InvoiceDownloader()
        result = downloader.test_connection()
        downloader.cleanup()
        
        return jsonify({
            'status': 'success' if result.get('success') else 'error',
            'message': result.get('message', 'Connection test completed'),
            'details': result,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"API: Error testing connection: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Connection test failed: {str(e)}',
            'timestamp': datetime.now().isoformat()
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
