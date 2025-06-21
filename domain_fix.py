"""
Correção específica para funcionamento no domínio crossxml.com.br
Sistema de detecção e ajustes automáticos para domínio personalizado
"""
import os
import logging

logger = logging.getLogger(__name__)

class DomainFix:
    """Correções específicas para domínio personalizado"""
    
    @staticmethod
    def is_custom_domain():
        """Detecta se está rodando no domínio crossxml.com.br"""
        return any([
            'crossxml.com.br' in str(os.environ.get('REPLIT_DOMAINS', '')),
            os.environ.get('CUSTOM_DOMAIN') == 'crossxml.com.br',
            'crossxml' in str(os.environ.get('REPLIT_DEPLOYMENT', ''))
        ])
    
    @staticmethod
    def apply_domain_fixes():
        """Aplica correções específicas para domínio personalizado"""
        if DomainFix.is_custom_domain():
            logger.info("🔧 Aplicando correções para domínio crossxml.com.br")
            
            # Force deploy environment detection
            os.environ['CUSTOM_DOMAIN_ACTIVE'] = 'true'
            
            # Ensure proper Chrome configuration
            os.environ['CHROME_FORCE_HEADLESS'] = 'true'
            
            # Apply extended timeouts for custom domain
            os.environ['CUSTOM_DOMAIN_TIMEOUTS'] = 'true'
            
            logger.info("✅ Correções aplicadas para domínio personalizado")
            return True
        
        return False
    
    @staticmethod
    def get_domain_specific_timeouts():
        """Retorna timeouts otimizados para o domínio atual"""
        if DomainFix.is_custom_domain():
            return {
                'element_wait': 10,  # Aumentado para domínio personalizado
                'xml_button': 8,     # Mais tempo para botão XML
                'download_poll': 1.5, # Polling mais lento
                'max_attempts': 25   # Mais tentativas
            }
        else:
            return {
                'element_wait': 3,
                'xml_button': 2,
                'download_poll': 0.5,
                'max_attempts': 15
            }