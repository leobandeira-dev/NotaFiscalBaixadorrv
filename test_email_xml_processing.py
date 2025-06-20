#!/usr/bin/env python3
"""
Teste direto do sistema de processamento XML via email
"""

import os
import sys
from new_app import app, db
from models import User, XMLFile
from email_xml_processor import EmailXMLProcessor
from email_processor import EmailProcessor
import logging

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_email_xml_processing():
    """Testa o processamento de XML do email diretamente"""
    
    with app.app_context():
        try:
            # Buscar usuário de teste
            user = User.query.filter_by(email='teste@xmldownloader.com').first()
            if not user:
                logger.error("Usuário teste não encontrado")
                return
            
            logger.info(f"Usuário encontrado: {user.email} (ID: {user.id})")
            
            # Verificar XMLs existentes
            existing_xmls = XMLFile.query.filter_by(user_id=user.id).count()
            logger.info(f"XMLs existentes no banco: {existing_xmls}")
            
            # Testar conexão POP3
            email_processor = EmailProcessor(user)
            
            # Verificar configuração POP3
            if not user.pop3_server:
                logger.error("Configuração POP3 não encontrada")
                return
            
            logger.info(f"Configuração POP3: {user.pop3_server}:{user.pop3_port}")
            
            # Testar conexão
            try:
                messages = email_processor.check_pop3_messages("CrossWMS@2024")
                logger.info(f"Mensagens encontradas: {len(messages)}")
                
                xml_processor = EmailXMLProcessor(user)
                processed_count = 0
                
                for msg in messages:
                    logger.info(f"Processando mensagem: {msg.get('subject', 'Sem assunto')}")
                    
                    if 'xml_attachments' in msg and msg['xml_attachments']:
                        for xml_attachment in msg['xml_attachments']:
                            logger.info(f"Processando XML: {xml_attachment['filename']} ({xml_attachment['size']} bytes)")
                            
                            try:
                                xml_file = xml_processor.save_xml_to_database(xml_attachment)
                                if xml_file:
                                    processed_count += 1
                                    logger.info(f"✅ XML salvo: NF {xml_file.numero_nf}/{xml_file.serie_nf}")
                                else:
                                    logger.error(f"❌ Falha ao salvar XML: {xml_attachment['filename']}")
                            except Exception as e:
                                logger.error(f"❌ Erro ao processar XML {xml_attachment['filename']}: {e}")
                    else:
                        logger.info("Nenhum XML encontrado nesta mensagem")
                
                # Verificar XMLs após processamento
                new_xmls = XMLFile.query.filter_by(user_id=user.id).count()
                logger.info(f"XMLs no banco após processamento: {new_xmls}")
                logger.info(f"XMLs processados com sucesso: {processed_count}")
                
                # Listar XMLs do usuário
                user_xmls = XMLFile.query.filter_by(user_id=user.id).all()
                for xml in user_xmls:
                    logger.info(f"XML: {xml.filename} - NF {xml.numero_nf}/{xml.serie_nf} - Tipo: {xml.import_type}")
                
            except Exception as e:
                logger.error(f"Erro na conexão POP3: {e}")
                
        except Exception as e:
            logger.error(f"Erro geral no teste: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_email_xml_processing()