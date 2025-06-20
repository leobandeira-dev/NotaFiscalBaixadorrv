"""
Enhanced Gunicorn configuration for production deployment
Optimized for Neon PostgreSQL and Replit deployment environment
"""

import os
import multiprocessing

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = min(4, (multiprocessing.cpu_count() * 2) + 1)
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to prevent memory leaks
max_requests = 1000
max_requests_jitter = 100

# Database connection settings
preload_app = True  # Load application code before the worker processes are forked

# Restart workers if they use too much memory
max_worker_memory = 300 * 1024 * 1024  # 300MB

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "cross_xml_downloader"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Graceful timeout for worker shutdown
graceful_timeout = 30

def on_starting(server):
    """Called just before the master process is initialized."""
    print("Starting Cross XML Downloader server...")

def on_reload(server):
    """Called to recycle workers during a reload via SIGHUP."""
    print("Reloading Cross XML Downloader server...")

def when_ready(server):
    """Called just after the server is started."""
    print(f"Cross XML Downloader ready. PID: {os.getpid()}")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    print(f"Worker {worker.pid} killed")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    print(f"Worker {worker.pid} spawned")

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    print(f"Worker {worker.pid} ready")

def post_worker_init(worker):
    """Called just after a worker has initialized the application."""
    print(f"Worker {worker.pid} application initialized")

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    print(f"Worker {worker.pid} aborted")

def on_exit(server):
    """Called just before exiting."""
    print("Cross XML Downloader server shutting down...")

# Environment-specific configuration
if os.environ.get('REPLIT_DEPLOYMENT'):
    # Production deployment settings
    workers = 2  # Conservative for Replit
    timeout = 60
    graceful_timeout = 45
    max_requests = 500
    worker_class = "sync"
    
elif os.environ.get('REPLIT_DEV_DOMAIN'):
    # Development settings
    workers = 1
    timeout = 120
    reload = True
    reload_engine = 'auto'
    
# Database-specific settings for Neon PostgreSQL
def on_starting(server):
    """Initialize database connections on startup"""
    import logging
    logger = logging.getLogger("gunicorn.error")
    
    try:
        # Import and validate database configuration
        from database_config import validate_database_environment, DatabaseHealthCheck
        
        validate_database_environment()
        logger.info("Database environment validation successful")
        
        # Test database connection
        health_check = DatabaseHealthCheck()
        if health_check.test_connection():
            logger.info("Database connection test successful")
        else:
            logger.warning("Database connection test failed - may affect worker startup")
            
    except Exception as e:
        logger.error(f"Database initialization error: {e}")
        # Don't fail startup, let workers handle connection issues

def post_worker_init(worker):
    """Initialize worker-specific database connections"""
    import logging
    logger = logging.getLogger("gunicorn.error")
    
    try:
        # Import Flask app to trigger database initialization
        from new_app import app
        
        with app.app_context():
            from models import db
            # Test database connection in worker
            db.engine.execute("SELECT 1")
            logger.info(f"Worker {worker.pid} database connection established")
            
    except Exception as e:
        logger.error(f"Worker {worker.pid} database initialization failed: {e}")
        # Worker will handle reconnection attempts