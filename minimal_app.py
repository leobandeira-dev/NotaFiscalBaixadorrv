"""
Minimal deployment-ready application that starts immediately
This version defers all database operations to prevent startup blocking
"""

import os
import logging
from datetime import datetime
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)

# Minimal configuration
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

# Database configuration - simplified for deployment
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///fallback.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    'pool_pre_ping': True,
    'pool_recycle': 300,
    'pool_size': 1,
    'max_overflow': 2,
    'pool_timeout': 10
}

# Initialize database
db = SQLAlchemy(app)

# Health check endpoint - no database dependency
@app.route('/health')
def health_check():
    """Health check endpoint for deployment verification"""
    return jsonify({
        'status': 'healthy', 
        'timestamp': datetime.now().isoformat(),
        'service': 'cross_xml_downloader'
    }), 200

# Database status endpoint
@app.route('/db-status')
def database_status():
    """Check database connectivity without blocking startup"""
    try:
        from sqlalchemy import text
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return jsonify({'database': 'connected', 'timestamp': datetime.now().isoformat()}), 200
    except Exception as e:
        logger.warning(f"Database connection test failed: {e}")
        return jsonify({'database': 'disconnected', 'error': str(e), 'timestamp': datetime.now().isoformat()}), 503

# Root endpoint
@app.route('/')
def index():
    """Root endpoint"""
    return jsonify({
        'service': 'CROSS XML Downloader PRO',
        'status': 'running',
        'version': '1.0.0',
        'endpoints': ['/health', '/db-status'],
        'timestamp': datetime.now().isoformat()
    })

if __name__ == "__main__":
    logger.info("Starting minimal deployment application")
    app.run(host="0.0.0.0", port=5000, debug=False)