"""
Enhanced database configuration for Neon PostgreSQL compatibility
Includes connection pooling, retry logic, and health checks
"""

import os
import time
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

class DatabaseConfig:
    """Enhanced database configuration with Neon PostgreSQL support"""
    
    @staticmethod
    def get_database_url():
        """Get database URL with fallback and validation"""
        database_url = os.environ.get("DATABASE_URL")
        
        if not database_url:
            # Check alternative environment variable names
            database_url = (
                os.environ.get("POSTGRES_URL") or
                os.environ.get("POSTGRESQL_URL") or
                os.environ.get("DB_URL")
            )
        
        if not database_url:
            raise ValueError("No database URL found in environment variables")
        
        # Ensure postgresql:// prefix for SQLAlchemy compatibility
        if database_url.startswith("postgres://"):
            database_url = database_url.replace("postgres://", "postgresql://", 1)
        
        return database_url
    
    @staticmethod
    def get_engine_options():
        """Get optimized engine options for Neon PostgreSQL"""
        return {
            # Connection pooling for Neon compatibility
            'poolclass': QueuePool,
            'pool_size': 5,
            'max_overflow': 10,
            'pool_timeout': 30,
            'pool_recycle': 300,  # 5 minutes
            'pool_pre_ping': True,
            
            # Connection options for stability
            'connect_args': {
                'connect_timeout': 10,
                'application_name': 'cross_xml_downloader',
                'options': '-c timezone=UTC'
            },
            
            # Engine options for reliability
            'echo': False,
            'future': True
        }
    
    @staticmethod
    def get_sqlalchemy_config():
        """Get complete SQLAlchemy configuration"""
        return {
            'SQLALCHEMY_DATABASE_URI': DatabaseConfig.get_database_url(),
            'SQLALCHEMY_ENGINE_OPTIONS': DatabaseConfig.get_engine_options(),
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SQLALCHEMY_RECORD_QUERIES': False
        }

class DatabaseHealthCheck:
    """Database health check and connection validation"""
    
    def __init__(self, app=None):
        self.app = app
        self.engine = None
        
    def init_app(self, app):
        """Initialize with Flask app"""
        self.app = app
        
    def create_test_engine(self):
        """Create engine for testing connection"""
        try:
            database_url = DatabaseConfig.get_database_url()
            engine_options = DatabaseConfig.get_engine_options()
            
            self.engine = create_engine(database_url, **engine_options)
            return True
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            return False
    
    def test_connection(self, max_retries=3, retry_delay=2):
        """Test database connection with retry logic"""
        if not self.engine:
            if not self.create_test_engine():
                return False
        
        for attempt in range(max_retries):
            try:
                with self.engine.connect() as conn:
                    result = conn.execute(text("SELECT 1"))
                    result.fetchone()
                    logger.info("Database connection test successful")
                    return True
                    
            except OperationalError as e:
                logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                else:
                    logger.error("All database connection attempts failed")
                    return False
            except Exception as e:
                logger.error(f"Unexpected database error: {e}")
                return False
        
        return False
    
    def wait_for_database(self, timeout=60, check_interval=2):
        """Wait for database to become available"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.test_connection():
                logger.info("Database is now available")
                return True
            
            logger.info("Waiting for database to become available...")
            time.sleep(check_interval)
        
        logger.error(f"Database did not become available within {timeout} seconds")
        return False
    
    def health_check_endpoint(self):
        """Health check endpoint for deployment"""
        try:
            if self.test_connection():
                return {
                    'status': 'healthy',
                    'database': 'connected',
                    'timestamp': time.time()
                }, 200
            else:
                return {
                    'status': 'unhealthy',
                    'database': 'disconnected',
                    'timestamp': time.time()
                }, 503
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }, 500

def validate_database_environment():
    """Validate all required database environment variables"""
    required_vars = ['DATABASE_URL']
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            # Check alternative names
            alternatives = {
                'DATABASE_URL': ['POSTGRES_URL', 'POSTGRESQL_URL', 'DB_URL']
            }
            
            found = False
            for alt in alternatives.get(var, []):
                if os.environ.get(alt):
                    found = True
                    break
            
            if not found:
                missing_vars.append(var)
    
    if missing_vars:
        raise EnvironmentError(f"Missing required database environment variables: {', '.join(missing_vars)}")
    
    return True

def initialize_database_with_retry(app, max_retries=3, retry_delay=2):
    """Initialize database with retry logic"""
    
    for attempt in range(max_retries):
        try:
            # Apply database configuration if not already set
            if not app.config.get('SQLALCHEMY_DATABASE_URI'):
                config = DatabaseConfig.get_sqlalchemy_config()
                for key, value in config.items():
                    app.config[key] = value
            
            # Test connection without re-initializing SQLAlchemy
            with app.app_context():
                from models import db
                # Use newer SQLAlchemy syntax
                with db.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                logger.info("Database connection test successful")
                return True
                
        except Exception as e:
            logger.warning(f"Database connection attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                logger.error("All database connection attempts failed")
                return False
    
    return False