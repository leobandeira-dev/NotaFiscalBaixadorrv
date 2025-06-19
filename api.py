"""
MeuDANFe XML Downloader API
REST API for bulk downloading XML invoices from meudanfe.com.br
"""

import os
import logging
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from threading import Thread
import uuid
from datetime import datetime
import json

# Import from main app
from app import DownloadJob, download_jobs, jobs_lock, process_download_job
from automation import InvoiceDownloader

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create API Flask app
api = Flask(__name__)
api.secret_key = os.environ.get("SESSION_SECRET", "api_secret_key")

# Enable CORS for API access
CORS(api)

# API Configuration
API_VERSION = "1.0"
API_TITLE = "MeuDANFe XML Downloader API"

@api.route('/api/v1/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'version': API_VERSION,
        'title': API_TITLE,
        'timestamp': datetime.now().isoformat()
    })

@api.route('/api/v1/jobs', methods=['POST'])
def create_download_job():
    """
    Create a new download job for invoice XMLs
    
    Body:
    {
        "invoice_keys": ["key1", "key2", ...],
        "callback_url": "optional_webhook_url"
    }
    
    Returns:
    {
        "job_id": "uuid",
        "status": "created",
        "total_keys": 2,
        "created_at": "2025-06-19T04:00:00"
    }
    """
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
        
        # Add callback URL if provided
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

@api.route('/api/v1/jobs/<job_id>', methods=['GET'])
def get_job_status(job_id):
    """
    Get job status and progress
    
    Returns:
    {
        "job_id": "uuid",
        "status": "running|completed|failed",
        "progress": {
            "total_keys": 5,
            "processed": 3,
            "successful": 2,
            "failed": 1,
            "percentage": 60.0
        },
        "files": [...],
        "errors": [...],
        "created_at": "2025-06-19T04:00:00",
        "completed_at": "2025-06-19T04:05:00"
    }
    """
    try:
        with jobs_lock:
            job = download_jobs.get(job_id)
            
            if not job:
                return jsonify({
                    'error': 'Job not found',
                    'code': 'JOB_NOT_FOUND'
                }), 404
            
            # Check for untracked downloaded files
            if job.status in ["running", "completed"] and job.processed == 0:
                downloads_dir = 'downloads'
                if os.path.exists(downloads_dir):
                    for invoice_key in job.invoice_keys:
                        file_path = os.path.join(downloads_dir, f"{invoice_key}.xml")
                        if os.path.exists(file_path) and file_path not in job.downloaded_files:
                            job.downloaded_files.append(file_path)
                            job.successful += 1
                            job.processed += 1
                            
                            if job.processed >= job.total_keys:
                                job.status = "completed"
                                job.end_time = datetime.now()
            
            # Prepare response
            response = {
                'job_id': job.job_id,
                'status': job.status,
                'progress': {
                    'total_keys': job.total_keys,
                    'processed': job.processed,
                    'successful': job.successful,
                    'failed': job.failed,
                    'percentage': (job.processed / job.total_keys * 100) if job.total_keys > 0 else 0
                },
                'files': [os.path.basename(f) for f in job.downloaded_files],
                'errors': job.errors,
                'created_at': job.start_time.isoformat() if job.start_time else None,
                'completed_at': job.end_time.isoformat() if job.end_time else None
            }
            
            return jsonify(response)
            
    except Exception as e:
        logger.error(f"API: Error getting job status: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'code': 'INTERNAL_ERROR'
        }), 500

@api.route('/api/v1/jobs', methods=['GET'])
def list_jobs():
    """
    List all jobs with optional filtering
    
    Query parameters:
    - status: filter by status (running, completed, failed)
    - limit: maximum number of jobs to return (default: 50)
    - offset: number of jobs to skip (default: 0)
    
    Returns:
    {
        "jobs": [...],
        "total": 10,
        "limit": 50,
        "offset": 0
    }
    """
    try:
        # Get query parameters
        status_filter = request.args.get('status')
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        with jobs_lock:
            all_jobs = list(download_jobs.values())
            
            # Filter by status if provided
            if status_filter:
                all_jobs = [job for job in all_jobs if job.status == status_filter]
            
            # Sort by creation time (newest first)
            all_jobs.sort(key=lambda x: x.start_time, reverse=True)
            
            # Apply pagination
            total = len(all_jobs)
            jobs_page = all_jobs[offset:offset + limit]
            
            # Format jobs for response
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

@api.route('/api/v1/jobs/<job_id>/files/<filename>', methods=['GET'])
def download_file(job_id, filename):
    """
    Download a specific XML file from a completed job
    
    Returns the XML file as attachment
    """
    try:
        with jobs_lock:
            job = download_jobs.get(job_id)
            
            if not job:
                return jsonify({
                    'error': 'Job not found',
                    'code': 'JOB_NOT_FOUND'
                }), 404
            
            # Find the file
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

@api.route('/api/v1/jobs/<job_id>/files', methods=['GET'])
def list_job_files(job_id):
    """
    List all files for a specific job
    
    Returns:
    {
        "job_id": "uuid",
        "files": [
            {
                "filename": "key.xml",
                "size": 4590,
                "download_url": "/api/v1/jobs/uuid/files/key.xml"
            }
        ]
    }
    """
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

@api.route('/api/v1/test', methods=['POST'])
def test_connection():
    """
    Test connection to meudanfe.com.br
    
    Returns:
    {
        "status": "success|error",
        "message": "Connection test result",
        "timestamp": "2025-06-19T04:00:00"
    }
    """
    try:
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

@api.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found',
        'code': 'NOT_FOUND'
    }), 404

@api.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors"""
    return jsonify({
        'error': 'Method not allowed',
        'code': 'METHOD_NOT_ALLOWED'
    }), 405

@api.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'error': 'Internal server error',
        'code': 'INTERNAL_ERROR'
    }), 500

if __name__ == '__main__':
    api.run(host='0.0.0.0', port=5001, debug=True)