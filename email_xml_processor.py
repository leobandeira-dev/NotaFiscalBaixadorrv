"""
Processador de XMLs recebidos via email
Conecta ao servidor POP3, baixa emails com anexos XML e processa automaticamente
"""

import poplib
import email
import os
import logging
from email.mime.multipart import MIMEMultipart
from werkzeug.security import check_password_hash
import xml.etree.ElementTree as ET
from datetime import datetime
import re
from models import User, XMLFile, db
import tempfile

logger = logging.getLogger(__name__)

class EmailXMLProcessor:
    def __init__(self, user):
        self.user = user
        
    def connect_pop3(self):
        """Conecta ao servidor POP3 do usuário"""
        if not self.user.has_pop3_configured():
            raise Exception("POP3 não configurado para este usuário")
            
        try:
            if self.user.pop3_ssl:
                pop3 = poplib.POP3_SSL(self.user.pop3_server, self.user.pop3_port)
            else:
                pop3 = poplib.POP3(self.user.pop3_server, self.user.pop3_port)
                
            logger.info(f"Conectado ao POP3 {self.user.pop3_server}:{self.user.pop3_port}")
            return pop3
            
        except Exception as e:
            logger.error(f"Erro ao conectar POP3: {e}")
            raise
    
    def authenticate_pop3(self, pop3, password):
        """Autentica no servidor POP3"""
        try:
            pop3.user(self.user.pop3_email)
            pop3.pass_(password)
            logger.info(f"Autenticado como {self.user.pop3_email}")
            return True
        except Exception as e:
            logger.error(f"Erro de autenticação POP3: {e}")
            raise
    
    def get_messages_with_xml(self, pop3):
        """Busca mensagens com anexos XML"""
        messages_with_xml = []
        
        try:
            # Obter lista de mensagens
            messages_info = pop3.list()[1]
            total_messages = len(messages_info)
            logger.info(f"Total de mensagens: {total_messages}")
            
            # Processar cada mensagem
            for i in range(1, total_messages + 1):
                try:
                    # Baixar mensagem completa
                    raw_message = b'\n'.join(pop3.retr(i)[1])
                    message = email.message_from_bytes(raw_message)
                    
                    # Verificar se tem anexos XML
                    xml_attachments = self.extract_xml_attachments(message)
                    if xml_attachments:
                        messages_with_xml.append({
                            'message_id': i,
                            'subject': message.get('Subject', 'Sem assunto'),
                            'from': message.get('From', 'Remetente desconhecido'),
                            'date': message.get('Date', 'Data desconhecida'),
                            'xml_attachments': xml_attachments
                        })
                        logger.info(f"Mensagem {i} contém {len(xml_attachments)} anexo(s) XML")
                        
                except Exception as e:
                    logger.error(f"Erro ao processar mensagem {i}: {e}")
                    continue
                    
            return messages_with_xml
            
        except Exception as e:
            logger.error(f"Erro ao buscar mensagens: {e}")
            raise
    
    def extract_xml_attachments(self, message):
        """Extrai anexos XML de uma mensagem de email"""
        xml_attachments = []
        
        try:
            if message.is_multipart():
                for part in message.walk():
                    # Verificar se é um anexo
                    if part.get_content_disposition() == 'attachment':
                        filename = part.get_filename()
                        if filename and filename.lower().endswith('.xml'):
                            content = part.get_payload(decode=True)
                            if content:
                                xml_attachments.append({
                                    'filename': filename,
                                    'content': content,
                                    'size': len(content)
                                })
                                logger.info(f"Anexo XML encontrado: {filename} ({len(content)} bytes)")
            else:
                # Mensagem simples, verificar se é XML
                filename = message.get_filename()
                if filename and filename.lower().endswith('.xml'):
                    content = message.get_payload(decode=True)
                    if content:
                        xml_attachments.append({
                            'filename': filename,
                            'content': content,
                            'size': len(content)
                        })
                        
        except Exception as e:
            logger.error(f"Erro ao extrair anexos XML: {e}")
            
        return xml_attachments
    
    def save_xml_to_database(self, xml_attachment, email_info):
        """Salva XML no banco de dados com import_type = 'email'"""
        try:
            # Criar arquivo temporário para processar o XML
            with tempfile.NamedTemporaryFile(mode='wb', suffix='.xml', delete=False) as temp_file:
                temp_file.write(xml_attachment['content'])
                temp_file_path = temp_file.name
            
            try:
                # Processar XML diretamente
                xml_data = self.process_xml_content(xml_attachment['content'].decode('utf-8'))
                
                if xml_data:
                    # Criar registro na tabela xml_files
                    xml_file = XMLFile(
                        user_id=self.user.id,
                        filename=xml_attachment['filename'],
                        file_size=xml_attachment['size'],
                        import_type='email',  # Marcar como importado via email
                        chave_nf=xml_data.get('chave_nf', 'N/A'),
                        numero_nf=xml_data.get('numero_nf', 'N/A'),
                        serie_nf=xml_data.get('serie_nf', 'N/A'),
                        data_emissao=xml_data.get('data_emissao'),
                        valor_total=xml_data.get('valor_total', 0.0),
                        peso_bruto=xml_data.get('peso_bruto', 0.0),
                        volumes=xml_data.get('volumes', 0),
                        nome_emitente=xml_data.get('nome_emitente', 'N/A'),
                        cidade_emitente=xml_data.get('cidade_emitente', 'N/A'),
                        uf_emitente=xml_data.get('uf_emitente', 'N/A'),
                        endereco_emitente=xml_data.get('endereco_emitente', 'N/A'),
                        cep_emitente=xml_data.get('cep_emitente', 'N/A'),
                        nome_destinatario=xml_data.get('nome_destinatario', 'N/A'),
                        cidade_destinatario=xml_data.get('cidade_destinatario', 'N/A'),
                        uf_destinatario=xml_data.get('uf_destinatario', 'N/A'),
                        endereco_destinatario=xml_data.get('endereco_destinatario', 'N/A'),
                        cep_destinatario=xml_data.get('cep_destinatario', 'N/A'),
                        nome_transportadora=xml_data.get('nome_transportadora', 'N/A'),
                        remetente_nome=xml_data.get('nome_emitente', 'N/A'),
                        remetente_cidade=xml_data.get('cidade_emitente', 'N/A'),
                        remetente_uf=xml_data.get('uf_emitente', 'N/A'),
                        remetente_endereco=xml_data.get('endereco_emitente', 'N/A'),
                        remetente_cep=xml_data.get('cep_emitente', 'N/A')
                    )
                    
                    # Salvar XML físico no diretório
                    xml_dir = f"downloads/user_{self.user.id}"
                    os.makedirs(xml_dir, exist_ok=True)
                    xml_file_path = os.path.join(xml_dir, xml_attachment['filename'])
                    
                    with open(xml_file_path, 'wb') as f:
                        f.write(xml_attachment['content'])
                    
                    xml_file.file_path = xml_file_path
                    
                    # Salvar no banco de dados
                    db.session.add(xml_file)
                    db.session.commit()
                    
                    logger.info(f"XML salvo no banco: {xml_attachment['filename']} - NF {xml_data.get('numero_nf', 'N/A')}")
                    
                    return xml_file
                else:
                    logger.error(f"Não foi possível processar XML: {xml_attachment['filename']}")
                    return None
                    
            finally:
                # Limpar arquivo temporário
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Erro ao salvar XML no banco: {e}")
            db.session.rollback()
            return None
    
    def process_email_xmls(self, password):
        """Processo principal: busca emails e processa XMLs"""
        processed_xmls = []
        pop3 = None
        
        try:
            # Conectar e autenticar
            pop3 = self.connect_pop3()
            self.authenticate_pop3(pop3, password)
            
            # Buscar mensagens com XML
            messages_with_xml = self.get_messages_with_xml(pop3)
            logger.info(f"Encontradas {len(messages_with_xml)} mensagens com XML")
            
            # Processar cada XML encontrado
            for message_info in messages_with_xml:
                for xml_attachment in message_info['xml_attachments']:
                    try:
                        # Verificar se XML já foi processado (evitar duplicatas)
                        existing_xml = XMLFile.query.filter_by(
                            user_id=self.user.id,
                            filename=xml_attachment['filename'],
                            import_type='email'
                        ).first()
                        
                        if existing_xml:
                            logger.info(f"XML já processado: {xml_attachment['filename']}")
                            continue
                        
                        # Processar novo XML
                        xml_record = self.save_xml_to_database(xml_attachment, message_info)
                        if xml_record:
                            processed_xmls.append({
                                'filename': xml_attachment['filename'],
                                'size': xml_attachment['size'],
                                'numero_nf': xml_record.numero_nf,
                                'email_subject': message_info['subject'],
                                'email_from': message_info['from']
                            })
                            
                    except Exception as e:
                        logger.error(f"Erro ao processar XML {xml_attachment['filename']}: {e}")
                        continue
                        
            return {
                'success': True,
                'processed_count': len(processed_xmls),
                'processed_xmls': processed_xmls,
                'total_messages': len(messages_with_xml)
            }
            
        except Exception as e:
            logger.error(f"Erro no processamento de emails: {e}")
            return {
                'success': False,
                'error': str(e),
                'processed_count': 0
            }
            
        finally:
            if pop3:
                try:
                    pop3.quit()
                except:
                    pass