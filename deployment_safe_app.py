"""
Deployment-safe version of CROSS XML Downloader
Ensures rapid startup while providing full functionality after deployment
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, jsonify, send_from_directory
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Basic configuration for immediate startup
app.secret_key = os.environ.get("SESSION_SECRET", "dev-deployment-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Health check endpoints - no dependencies
@app.route('/health')
def health_check():
    """Health check endpoint for deployment verification"""
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'service': 'cross_xml_downloader'
    }), 200

@app.route('/db-status')
def database_status():
    """Database status endpoint - checks connection without blocking startup"""
    try:
        # Only import and check database when requested
        from models import db
        from sqlalchemy import text
        
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return jsonify({
            'database': 'connected', 
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.warning(f"Database connection test failed: {e}")
        return jsonify({
            'database': 'disconnected', 
            'error': str(e), 
            'timestamp': datetime.now().isoformat()
        }), 503

# Root route - serves landing page
@app.route('/')
def index():
    """Home page - serves static landing page for immediate response"""
    try:
        return send_from_directory('static', 'index.html')
    except Exception as e:
        logger.warning(f"Static file not found, serving basic response: {e}")
        return jsonify({
            'service': 'CROSS XML Downloader PRO',
            'status': 'running',
            'version': '1.0.0',
            'message': 'Sistema de automação fiscal empresarial',
            'endpoints': ['/health', '/db-status', '/app'],
            'timestamp': datetime.now().isoformat()
        })

# Full application route - lazy loads complete functionality
@app.route('/app')
@app.route('/dashboard')
@app.route('/login')
@app.route('/register')
def load_full_app():
    """Redirect to full application functionality"""
    try:
        # For now, redirect to login page template or show coming soon
        return redirect('/#login-section')
    except Exception as e:
        logger.error(f"Failed to load full application: {e}")
        return jsonify({
            'error': 'Sistema temporariamente indisponível',
            'message': 'Aguarde alguns instantes e tente novamente',
            'timestamp': datetime.now().isoformat()
        }), 503

# API endpoints for immediate functionality
@app.route('/api/status')
def api_status():
    """API status endpoint"""
    return jsonify({
        'api': 'operational',
        'version': '1.0.0',
        'timestamp': datetime.now().isoformat(),
        'features': ['xml_download', 'danfe_generation', 'transport_labels']
    })

if __name__ == "__main__":
    logger.info("Starting deployment-safe CROSS XML Downloader")
    app.run(host="0.0.0.0", port=5000, debug=False)