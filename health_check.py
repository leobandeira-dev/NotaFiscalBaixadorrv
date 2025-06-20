"""
Health check system for deployment monitoring
Provides comprehensive health status for database, application, and external services
"""

import time
import logging
from flask import jsonify, current_app
from database_config import DatabaseHealthCheck
from models import db, User, SystemSettings

logger = logging.getLogger(__name__)

class ApplicationHealthCheck:
    """Comprehensive application health monitoring"""
    
    def __init__(self):
        self.db_health = DatabaseHealthCheck()
        
    def check_database_health(self):
        """Check database connectivity and basic operations"""
        try:
            # Test basic connection
            if not self.db_health.test_connection():
                return {
                    'status': 'unhealthy',
                    'error': 'Database connection failed'
                }
            
            # Test basic query
            user_count = User.query.count()
            
            return {
                'status': 'healthy',
                'user_count': user_count,
                'connection': 'active'
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_application_health(self):
        """Check application-specific functionality"""
        try:
            # Check if critical models are accessible
            settings_count = SystemSettings.query.count()
            
            # Check if downloads directory exists
            import os
            downloads_dir = os.path.join(os.getcwd(), 'downloads')
            downloads_exists = os.path.exists(downloads_dir)
            
            return {
                'status': 'healthy',
                'settings_count': settings_count,
                'downloads_directory': downloads_exists,
                'version': '1.0.0'
            }
            
        except Exception as e:
            logger.error(f"Application health check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e)
            }
    
    def check_external_services(self):
        """Check external service connectivity"""
        services = {}
        
        try:
            # Check if Stripe keys are configured
            stripe_configured = bool(current_app.config.get('STRIPE_SECRET_KEY'))
            services['stripe'] = 'configured' if stripe_configured else 'not_configured'
            
            # Check if email is configured
            mail_configured = bool(current_app.config.get('MAIL_USERNAME'))
            services['email'] = 'configured' if mail_configured else 'not_configured'
            
            # Check if Asaas is configured
            asaas_configured = bool(current_app.config.get('ASAAS_API_KEY'))
            services['asaas'] = 'configured' if asaas_configured else 'not_configured'
            
            return {
                'status': 'healthy',
                'services': services
            }
            
        except Exception as e:
            logger.error(f"External services check failed: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'services': services
            }
    
    def get_comprehensive_health(self):
        """Get complete health status"""
        timestamp = time.time()
        
        # Run all health checks
        db_health = self.check_database_health()
        app_health = self.check_application_health()
        services_health = self.check_external_services()
        
        # Determine overall status
        overall_healthy = all([
            db_health.get('status') == 'healthy',
            app_health.get('status') == 'healthy',
            services_health.get('status') == 'healthy'
        ])
        
        return {
            'status': 'healthy' if overall_healthy else 'unhealthy',
            'timestamp': timestamp,
            'checks': {
                'database': db_health,
                'application': app_health,
                'external_services': services_health
            }
        }

def setup_health_endpoints(app):
    """Setup health check endpoints"""
    health_checker = ApplicationHealthCheck()
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Simple health check endpoint"""
        try:
            health_status = health_checker.get_comprehensive_health()
            status_code = 200 if health_status['status'] == 'healthy' else 503
            return jsonify(health_status), status_code
        except Exception as e:
            logger.error(f"Health check endpoint error: {e}")
            return jsonify({
                'status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }), 500
    
    @app.route('/health/db', methods=['GET'])
    def database_health():
        """Database-specific health check"""
        try:
            db_health = health_checker.check_database_health()
            status_code = 200 if db_health['status'] == 'healthy' else 503
            return jsonify(db_health), status_code
        except Exception as e:
            return jsonify({
                'status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }), 500
    
    @app.route('/health/ready', methods=['GET'])
    def readiness_check():
        """Kubernetes-style readiness probe"""
        try:
            # Quick checks for readiness
            db_status = health_checker.db_health.test_connection()
            
            if db_status:
                return jsonify({
                    'status': 'ready',
                    'timestamp': time.time()
                }), 200
            else:
                return jsonify({
                    'status': 'not_ready',
                    'reason': 'database_unavailable',
                    'timestamp': time.time()
                }), 503
                
        except Exception as e:
            return jsonify({
                'status': 'not_ready',
                'reason': str(e),
                'timestamp': time.time()
            }), 503
    
    @app.route('/health/live', methods=['GET'])
    def liveness_check():
        """Kubernetes-style liveness probe"""
        return jsonify({
            'status': 'alive',
            'timestamp': time.time()
        }), 200