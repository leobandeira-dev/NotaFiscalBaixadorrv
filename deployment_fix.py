"""
Deployment fix script to resolve database connection and startup issues
This script addresses the core problems preventing successful deployment
"""

import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_database_url():
    """Fix database URL format for Neon PostgreSQL compatibility"""
    database_url = os.environ.get("DATABASE_URL")
    
    if not database_url:
        logger.error("DATABASE_URL not found in environment variables")
        return None
    
    # Convert postgres:// to postgresql:// for SQLAlchemy compatibility
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
        logger.info("Converted postgres:// to postgresql:// in DATABASE_URL")
    
    return database_url

def test_database_connection():
    """Test database connection with proper error handling"""
    database_url = fix_database_url()
    
    if not database_url:
        return False
    
    try:
        # Create engine with Neon-optimized settings
        engine = create_engine(
            database_url,
            pool_pre_ping=True,
            pool_recycle=300,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            connect_args={
                'connect_timeout': 10,
                'application_name': 'cross_xml_downloader'
            }
        )
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
            logger.info("Database connection test successful")
            return True
            
    except OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected database error: {e}")
        return False

def validate_environment():
    """Validate all required environment variables"""
    required_vars = ['DATABASE_URL']
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    logger.info("All required environment variables present")
    return True

def main():
    """Main deployment validation function"""
    logger.info("Starting deployment validation...")
    
    # Validate environment
    if not validate_environment():
        return False
    
    # Test database connection
    if not test_database_connection():
        return False
    
    logger.info("Deployment validation successful")
    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)