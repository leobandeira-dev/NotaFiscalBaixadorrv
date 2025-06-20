"""
Sistema de Verificação de Segurança para Produção
Valida todas as implementações de isolamento de dados e segurança
"""

import os
import logging
from flask import current_app
from models import db, User, XMLFile, UsageRecord, StripeTransaction
from security import SecurityManager, DataIsolationManager, BillingSecurityManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ProductionSecurityValidator:
    """Validador de segurança para ambiente de produção"""
    
    def __init__(self):
        self.validation_results = []
        self.security_issues = []
        self.passed_checks = 0
        self.total_checks = 0
    
    def validate_data_isolation(self):
        """Validar isolamento de dados por usuário"""
        logger.info("Validando isolamento de dados por usuário...")
        
        try:
            # Verificar se XMLFile possui user_id
            xml_columns = [column.name for column in XMLFile.__table__.columns]
            if 'user_id' not in xml_columns:
                self.security_issues.append("CRITICAL: XMLFile não possui campo user_id")
            else:
                self.passed_checks += 1
                logger.info("✓ XMLFile possui isolamento por user_id")
            
            # Verificar se UsageRecord possui user_id
            usage_columns = [column.name for column in UsageRecord.__table__.columns]
            if 'user_id' not in usage_columns:
                self.security_issues.append("CRITICAL: UsageRecord não possui campo user_id")
            else:
                self.passed_checks += 1
                logger.info("✓ UsageRecord possui isolamento por user_id")
            
            # Verificar se StripeTransaction possui user_id
            stripe_columns = [column.name for column in StripeTransaction.__table__.columns]
            if 'user_id' not in stripe_columns:
                self.security_issues.append("CRITICAL: StripeTransaction não possui campo user_id")
            else:
                self.passed_checks += 1
                logger.info("✓ StripeTransaction possui isolamento por user_id")
            
            self.total_checks += 3
            
        except Exception as e:
            self.security_issues.append(f"Erro ao validar isolamento de dados: {e}")
    
    def validate_security_managers(self):
        """Validar implementação dos gerenciadores de segurança"""
        logger.info("Validando gerenciadores de segurança...")
        
        try:
            # Verificar SecurityManager
            if hasattr(SecurityManager, 'validate_user_access'):
                self.passed_checks += 1
                logger.info("✓ SecurityManager.validate_user_access implementado")
            else:
                self.security_issues.append("CRITICAL: SecurityManager.validate_user_access não implementado")
            
            # Verificar DataIsolationManager
            if hasattr(DataIsolationManager, 'filter_user_xmls'):
                self.passed_checks += 1
                logger.info("✓ DataIsolationManager.filter_user_xmls implementado")
            else:
                self.security_issues.append("CRITICAL: DataIsolationManager.filter_user_xmls não implementado")
            
            # Verificar BillingSecurityManager
            if hasattr(BillingSecurityManager, 'validate_service_usage'):
                self.passed_checks += 1
                logger.info("✓ BillingSecurityManager.validate_service_usage implementado")
            else:
                self.security_issues.append("CRITICAL: BillingSecurityManager.validate_service_usage não implementado")
            
            self.total_checks += 3
            
        except Exception as e:
            self.security_issues.append(f"Erro ao validar gerenciadores de segurança: {e}")
    
    def validate_environment_security(self):
        """Validar configurações de segurança do ambiente"""
        logger.info("Validando configurações de ambiente...")
        
        try:
            # Verificar variáveis de ambiente críticas
            required_vars = ['DATABASE_URL', 'SESSION_SECRET', 'STRIPE_SECRET_KEY']
            for var in required_vars:
                if os.environ.get(var):
                    self.passed_checks += 1
                    logger.info(f"✓ {var} configurado")
                else:
                    self.security_issues.append(f"CRITICAL: {var} não configurado")
            
            # Verificar configuração do Flask
            if current_app.secret_key:
                self.passed_checks += 1
                logger.info("✓ Flask secret_key configurado")
            else:
                self.security_issues.append("CRITICAL: Flask secret_key não configurado")
            
            self.total_checks += len(required_vars) + 1
            
        except Exception as e:
            self.security_issues.append(f"Erro ao validar ambiente: {e}")
    
    def validate_admin_permissions(self):
        """Validar sistema de permissões administrativas"""
        logger.info("Validando sistema de permissões...")
        
        try:
            # Verificar se existe super admin
            super_admin = User.query.filter_by(is_super_admin=True).first()
            if super_admin:
                self.passed_checks += 1
                logger.info("✓ Super admin configurado")
            else:
                self.security_issues.append("WARNING: Nenhum super admin configurado")
            
            # Verificar campos de permissão no modelo User
            user_columns = [column.name for column in User.__table__.columns]
            required_fields = ['is_admin', 'is_super_admin']
            for field in required_fields:
                if field in user_columns:
                    self.passed_checks += 1
                    logger.info(f"✓ Campo {field} presente no modelo User")
                else:
                    self.security_issues.append(f"CRITICAL: Campo {field} ausente no modelo User")
            
            self.total_checks += 1 + len(required_fields)
            
        except Exception as e:
            self.security_issues.append(f"Erro ao validar permissões: {e}")
    
    def validate_billing_system(self):
        """Validar sistema de cobrança e créditos"""
        logger.info("Validando sistema de cobrança...")
        
        try:
            # Verificar campos de cobrança no User
            user_columns = [column.name for column in User.__table__.columns]
            billing_fields = ['current_balance', 'trial_expires_at']
            for field in billing_fields:
                if field in user_columns:
                    self.passed_checks += 1
                    logger.info(f"✓ Campo de cobrança {field} presente")
                else:
                    self.security_issues.append(f"CRITICAL: Campo de cobrança {field} ausente")
            
            self.total_checks += len(billing_fields)
            
        except Exception as e:
            self.security_issues.append(f"Erro ao validar sistema de cobrança: {e}")
    
    def run_full_validation(self):
        """Executar validação completa de segurança"""
        logger.info("=== INICIANDO VALIDAÇÃO DE SEGURANÇA DE PRODUÇÃO ===")
        
        self.validate_data_isolation()
        self.validate_security_managers()
        self.validate_environment_security()
        self.validate_admin_permissions()
        self.validate_billing_system()
        
        # Gerar relatório
        self.generate_security_report()
        
        return len(self.security_issues) == 0
    
    def generate_security_report(self):
        """Gerar relatório de segurança"""
        logger.info("=== RELATÓRIO DE SEGURANÇA ===")
        logger.info(f"Verificações passadas: {self.passed_checks}/{self.total_checks}")
        
        if self.security_issues:
            logger.error("PROBLEMAS DE SEGURANÇA ENCONTRADOS:")
            for issue in self.security_issues:
                logger.error(f"  - {issue}")
        else:
            logger.info("✓ TODOS OS TESTES DE SEGURANÇA PASSARAM")
        
        # Calcular score de segurança
        if self.total_checks > 0:
            security_score = (self.passed_checks / self.total_checks) * 100
            logger.info(f"Score de Segurança: {security_score:.1f}%")
            
            if security_score >= 95:
                logger.info("🟢 SISTEMA PRONTO PARA PRODUÇÃO")
            elif security_score >= 80:
                logger.warning("🟡 SISTEMA NECESSITA CORREÇÕES MENORES")
            else:
                logger.error("🔴 SISTEMA NÃO ESTÁ PRONTO PARA PRODUÇÃO")

def run_production_security_check():
    """Executar verificação de segurança para produção"""
    validator = ProductionSecurityValidator()
    return validator.run_full_validation()

if __name__ == "__main__":
    run_production_security_check()