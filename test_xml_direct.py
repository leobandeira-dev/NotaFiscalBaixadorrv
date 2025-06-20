#!/usr/bin/env python3
"""
Teste direto para processar XML do email e salvar no banco
"""

import os
import poplib
import email
from email.header import decode_header
import logging
from new_app import app, db
from models import User, XMLFile
from email_xml_processor import EmailXMLProcessor

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_pop3_and_xml():
    """Teste direto de conexão POP3 e processamento XML"""
    
    with app.app_context():
        try:
            # Buscar usuário teste
            user = User.query.filter_by(email='teste@xmldownloader.com').first()
            if not user:
                logger.error("Usuário teste não encontrado")
                return
                
            logger.info(f"Testando com usuário: {user.email}")
            
            # Conectar ao POP3
            pop3_server = poplib.POP3_SSL('pop.titan.email', 995)
            pop3_server.user('suporte@crosswms.com.br')
            pop3_server.pass_('CrossWMS@2024')
            
            # Listar mensagens
            num_messages = len(pop3_server.list()[1])
            logger.info(f"Total de mensagens no servidor: {num_messages}")
            
            xml_processor = EmailXMLProcessor(user)
            processed_count = 0
            
            # Processar mensagens recentes
            for i in range(max(1, num_messages-10), num_messages + 1):
                try:
                    # Baixar mensagem
                    raw_email = b"\n".join(pop3_server.retr(i)[1])
                    msg = email.message_from_bytes(raw_email)
                    
                    # Decodificar assunto
                    subject = ""
                    if msg["Subject"]:
                        decoded = decode_header(msg["Subject"])
                        subject = str(decoded[0][0])
                        if isinstance(decoded[0][0], bytes):
                            subject = decoded[0][0].decode(decoded[0][1] or 'utf-8')
                    
                    logger.info(f"Mensagem {i}: {subject}")
                    
                    # Verificar anexos XML
                    for part in msg.walk():
                        if part.get_content_disposition() == 'attachment':
                            filename = part.get_filename()
                            if filename and filename.lower().endswith('.xml'):
                                logger.info(f"XML encontrado: {filename}")
                                
                                # Extrair conteúdo do XML
                                xml_content = part.get_payload(decode=True)
                                xml_attachment = {
                                    'filename': filename,
                                    'content': xml_content,
                                    'size': len(xml_content)
                                }
                                
                                # Processar XML
                                try:
                                    xml_file = xml_processor.save_xml_to_database(xml_attachment)
                                    if xml_file:
                                        processed_count += 1
                                        logger.info(f"✅ XML salvo: {filename} - NF {xml_file.numero_nf}")
                                    else:
                                        logger.error(f"❌ Falha ao salvar: {filename}")
                                except Exception as e:
                                    logger.error(f"❌ Erro ao processar {filename}: {e}")
                                    import traceback
                                    traceback.print_exc()
                
                except Exception as e:
                    logger.error(f"Erro ao processar mensagem {i}: {e}")
            
            # Fechar conexão
            pop3_server.quit()
            
            logger.info(f"Processamento concluído. XMLs salvos: {processed_count}")
            
            # Verificar XMLs no banco
            user_xmls = XMLFile.query.filter_by(user_id=user.id).all()
            logger.info(f"Total de XMLs do usuário no banco: {len(user_xmls)}")
            
            for xml in user_xmls:
                logger.info(f"XML: {xml.filename} - NF {xml.numero_nf} - Tipo: {xml.import_type}")
                
        except Exception as e:
            logger.error(f"Erro geral: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_pop3_and_xml()