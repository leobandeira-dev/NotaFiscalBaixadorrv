"""
Sistema de processamento de emails para importação automática de XMLs
"""

import imaplib
import email
import os
import tempfile
from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from xml_processor import save_xml_to_database
from models import User, db
import logging

logger = logging.getLogger(__name__)

def check_user_emails(user_id: int) -> int:
    """
    Verifica emails de um usuário específico e processa XMLs anexados
    
    Args:
        user_id: ID do usuário
        
    Returns:
        Número de XMLs processados
    """
    try:
        user = User.query.get(user_id)
        if not user or not user.has_email_import_configured():
            return 0
            
        # Conectar ao servidor de email
        imap = connect_to_email_server(user)
        if not imap:
            return 0
            
        # Buscar emails não lidos
        xml_files = search_xml_emails(imap)
        processed_count = 0
        
        for email_msg, attachment_data in xml_files:
            try:
                # Salvar XML no banco de dados
                result = save_xml_to_database(
                    xml_content=attachment_data,
                    user_id=user_id,
                    import_type='EMAIL'
                )
                
                if result.get('success'):
                    processed_count += 1
                    logger.info(f"XML processado via email para usuário {user_id}")
                    
            except Exception as e:
                logger.error(f"Erro ao processar XML via email: {e}")
                
        # Atualizar timestamp da última verificação
        user.import_email_last_check = datetime.utcnow()
        db.session.commit()
        
        # Fechar conexão
        imap.close()
        imap.logout()
        
        return processed_count
        
    except Exception as e:
        logger.error(f"Erro ao verificar emails do usuário {user_id}: {e}")
        return 0

def connect_to_email_server(user: User) -> imaplib.IMAP4:
    """
    Conecta ao servidor de email do usuário
    
    Args:
        user: Objeto User com credenciais configuradas
        
    Returns:
        Conexão IMAP ou None se falhar
    """
    try:
        # Descriptografar senha (usando check_password_hash para recuperar)
        # Nota: Em produção, usar criptografia reversível adequada
        
        if user.import_email_ssl:
            imap = imaplib.IMAP4_SSL(user.import_email_server, user.import_email_port)
        else:
            imap = imaplib.IMAP4(user.import_email_server, user.import_email_port)
        
        # Para esta implementação, precisamos da senha em texto claro
        # Em produção, implementar criptografia reversível adequada
        logger.warning("Sistema de email configurado mas senha criptografada - implemente descriptografia adequada")
        return None
        
    except Exception as e:
        logger.error(f"Erro ao conectar servidor de email: {e}")
        return None

def search_xml_emails(imap: imaplib.IMAP4) -> List[Tuple[email.message.EmailMessage, str]]:
    """
    Busca emails com anexos XML
    
    Args:
        imap: Conexão IMAP ativa
        
    Returns:
        Lista de tuplas (email_message, xml_content)
    """
    try:
        imap.select('INBOX')
        
        # Buscar emails não lidos dos últimos 7 dias
        search_criteria = '(UNSEEN SINCE "{}") (OR (BODY "xml") (SUBJECT "xml"))'.format(
            (datetime.now() - timedelta(days=7)).strftime('%d-%b-%Y')
        )
        
        typ, data = imap.search(None, search_criteria)
        xml_files = []
        
        for email_id in data[0].split():
            typ, msg_data = imap.fetch(email_id, '(RFC822)')
            email_body = msg_data[0][1]
            email_message = email.message_from_bytes(email_body)
            
            # Processar anexos
            for part in email_message.walk():
                if part.get_content_disposition() == 'attachment':
                    filename = part.get_filename()
                    if filename and filename.lower().endswith('.xml'):
                        xml_content = part.get_payload(decode=True).decode('utf-8')
                        xml_files.append((email_message, xml_content))
                        
            # Marcar como lido
            imap.store(email_id, '+FLAGS', '\\Seen')
            
        return xml_files
        
    except Exception as e:
        logger.error(f"Erro ao buscar emails XML: {e}")
        return []

def check_all_users_emails() -> int:
    """
    Verifica emails de todos os usuários configurados
    
    Returns:
        Total de XMLs processados
    """
    try:
        users_with_email = User.query.filter_by(import_email_configured=True).all()
        total_processed = 0
        
        for user in users_with_email:
            try:
                processed = check_user_emails(user.id)
                total_processed += processed
                logger.info(f"Processados {processed} XMLs para usuário {user.id}")
                
            except Exception as e:
                logger.error(f"Erro ao processar emails do usuário {user.id}: {e}")
                
        return total_processed
        
    except Exception as e:
        logger.error(f"Erro ao verificar emails de todos os usuários: {e}")
        return 0

# Função simplificada para demonstração
def check_user_emails_demo(user_id: int) -> int:
    """
    Versão de demonstração do verificador de emails
    Simula o processamento de XMLs recebidos via email
    """
    try:
        user = User.query.get(user_id)
        if not user or not user.has_email_import_configured():
            return 0
            
        # Simular verificação de email
        user.import_email_last_check = datetime.utcnow()
        db.session.commit()
        
        # Em uma implementação real, aqui conectaria ao servidor de email
        # e processaria XMLs anexados
        logger.info(f"Verificação de email simulada para usuário {user_id}")
        
        # Retornar 0 XMLs processados (demonstração)
        return 0
        
    except Exception as e:
        logger.error(f"Erro na verificação demo de emails: {e}")
        return 0

# Usar a versão demo temporariamente
check_user_emails = check_user_emails_demo