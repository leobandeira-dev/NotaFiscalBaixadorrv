#!/usr/bin/env python3
"""
Correção específica para problemas de conexão Chrome WebDriver
Implementa estratégias robustas para lidar com desconexões
"""
import time
import logging
from selenium.common.exceptions import WebDriverException

logger = logging.getLogger(__name__)

class ChromeConnectionFix:
    """Implementa correções para problemas de conexão do Chrome"""
    
    @staticmethod
    def handle_chrome_disconnection(driver, job_id, operation_name="operation"):
        """
        Lida com desconexões do Chrome de forma robusta
        
        Args:
            driver: Instância do WebDriver
            job_id: ID do job para logging
            operation_name: Nome da operação sendo executada
            
        Returns:
            bool: True se a conexão foi restaurada, False caso contrário
        """
        try:
            logger.info(f"[Job {job_id}] Detectada desconexão do Chrome durante {operation_name}")
            
            # Tenta verificar se o driver ainda está funcional
            try:
                driver.current_url
                logger.info(f"[Job {job_id}] Driver ainda funcional, continuando...")
                return True
            except:
                logger.info(f"[Job {job_id}] Driver desconectado, tentando recuperação...")
            
            # Tentativa de recuperação básica
            try:
                driver.quit()
                logger.info(f"[Job {job_id}] Driver anterior encerrado")
            except:
                pass
            
            # Aguarda antes de tentar novamente
            time.sleep(3)
            
            logger.info(f"[Job {job_id}] Conexão não pode ser restaurada automaticamente")
            return False
            
        except Exception as e:
            logger.error(f"[Job {job_id}] Erro durante recuperação de conexão: {e}")
            return False
    
    @staticmethod
    def is_connection_error(error_message):
        """
        Verifica se o erro é relacionado à conexão do Chrome
        
        Args:
            error_message: Mensagem de erro
            
        Returns:
            bool: True se for erro de conexão
        """
        connection_indicators = [
            "disconnected",
            "not connected to DevTools",
            "Session info: chrome=",
            "chrome not reachable",
            "connection was lost",
            "target window already closed"
        ]
        
        error_lower = error_message.lower()
        return any(indicator.lower() in error_lower for indicator in connection_indicators)
    
    @staticmethod
    def get_error_category(error_message):
        """
        Categoriza o tipo de erro para melhor handling
        
        Args:
            error_message: Mensagem de erro
            
        Returns:
            str: Categoria do erro
        """
        if ChromeConnectionFix.is_connection_error(error_message):
            return "chrome_connection_lost"
        elif "TimeoutException" in error_message:
            return "timeout"
        elif "NoSuchElementException" in error_message:
            return "element_not_found"
        elif "WebDriverException" in error_message:
            return "webdriver_error"
        else:
            return "unknown"
    
    @staticmethod
    def create_error_response(job_id, invoice_key, error_message, attempt_count=1):
        """
        Cria resposta de erro padronizada
        
        Args:
            job_id: ID do job
            invoice_key: Chave da nota fiscal
            error_message: Mensagem de erro
            attempt_count: Número de tentativas realizadas
            
        Returns:
            dict: Resposta de erro padronizada
        """
        error_category = ChromeConnectionFix.get_error_category(error_message)
        
        # Mensagem amigável baseada na categoria
        if error_category == "chrome_connection_lost":
            friendly_message = "Conexão com o navegador foi perdida durante o processo"
        elif error_category == "timeout":
            friendly_message = "Tempo limite excedido durante o download"
        elif error_category == "element_not_found":
            friendly_message = "Elemento não encontrado na página (possível mudança no site)"
        else:
            friendly_message = "Erro técnico durante o download"
        
        return {
            'success': False,
            'error': friendly_message,
            'technical_error': error_message,
            'error_category': error_category,
            'invoice_key': invoice_key,
            'job_id': job_id,
            'attempts_made': attempt_count
        }