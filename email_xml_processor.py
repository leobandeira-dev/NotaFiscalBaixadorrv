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
    def __init__(self, user=None):
        self.user = user
    
    def process_xml_content(self, xml_content):
        """Processa conteúdo XML e extrai dados da NFe"""
        try:
            # Parse XML
            root = ET.fromstring(xml_content)
            
            # Definir namespaces
            namespaces = {
                'nfe': 'http://www.portalfiscal.inf.br/nfe'
            }
            
            # Extrair dados da NFe
            xml_data = {}
            
            # Buscar elemento infNFe
            inf_nfe = root.find('.//nfe:infNFe', namespaces)
            if inf_nfe is None:
                logger.error("Elemento infNFe não encontrado no XML")
                return None
            
            # Chave da NFe
            xml_data['chave_nf'] = inf_nfe.get('Id', '').replace('NFe', '') if inf_nfe.get('Id') else 'N/A'
            
            # Dados da NFe
            ide = inf_nfe.find('nfe:ide', namespaces)
            if ide is not None:
                xml_data['numero_nf'] = ide.findtext('nfe:nNF', 'N/A', namespaces)
                xml_data['serie_nf'] = ide.findtext('nfe:serie', 'N/A', namespaces)
                
                # Data de emissão
                dhemi = ide.findtext('nfe:dhEmi', namespaces=namespaces)
                if dhemi:
                    try:
                        xml_data['data_emissao'] = datetime.fromisoformat(dhemi.replace('Z', '+00:00')).date()
                    except:
                        xml_data['data_emissao'] = None
                else:
                    xml_data['data_emissao'] = None
            
            # Dados do emitente
            emit = inf_nfe.find('nfe:emit', namespaces)
            if emit is not None:
                xml_data['nome_emitente'] = emit.findtext('nfe:xNome', 'N/A', namespaces)
                xml_data['cnpj_emitente'] = emit.findtext('nfe:CNPJ', 'N/A', namespaces)
                
                # Endereço do emitente
                enderemit = emit.find('nfe:enderEmit', namespaces)
                if enderemit is not None:
                    xml_data['cidade_emitente'] = enderemit.findtext('nfe:xMun', 'N/A', namespaces)
                    xml_data['uf_emitente'] = enderemit.findtext('nfe:UF', 'N/A', namespaces)
                    xml_data['cep_emitente'] = enderemit.findtext('nfe:CEP', 'N/A', namespaces)
                    
                    # Endereço completo
                    logradouro = enderemit.findtext('nfe:xLgr', '', namespaces)
                    numero = enderemit.findtext('nfe:nro', '', namespaces)
                    bairro = enderemit.findtext('nfe:xBairro', '', namespaces)
                    xml_data['endereco_emitente'] = f"{logradouro}, {numero}, {bairro}".strip(', ')
            
            # Dados do destinatário
            dest = inf_nfe.find('nfe:dest', namespaces)
            if dest is not None:
                xml_data['nome_destinatario'] = dest.findtext('nfe:xNome', 'N/A', namespaces)
                
                # CNPJ ou CPF do destinatário
                cnpj_dest = dest.findtext('nfe:CNPJ', None, namespaces)
                cpf_dest = dest.findtext('nfe:CPF', None, namespaces)
                xml_data['destinatario_cnpj_cpf'] = cnpj_dest if cnpj_dest else (cpf_dest if cpf_dest else 'N/A')
                
                # Endereço do destinatário
                enderdest = dest.find('nfe:enderDest', namespaces)
                if enderdest is not None:
                    xml_data['cidade_destinatario'] = enderdest.findtext('nfe:xMun', 'N/A', namespaces)
                    xml_data['uf_destinatario'] = enderdest.findtext('nfe:UF', 'N/A', namespaces)
                    xml_data['cep_destinatario'] = enderdest.findtext('nfe:CEP', 'N/A', namespaces)
                    
                    # Endereço completo
                    logradouro = enderdest.findtext('nfe:xLgr', '', namespaces)
                    numero = enderdest.findtext('nfe:nro', '', namespaces)
                    bairro = enderdest.findtext('nfe:xBairro', '', namespaces)
                    xml_data['endereco_destinatario'] = f"{logradouro}, {numero}, {bairro}".strip(', ')
            
            # Dados da transportadora
            transp = inf_nfe.find('nfe:transp', namespaces)
            if transp is not None:
                transporta = transp.find('nfe:transporta', namespaces)
                if transporta is not None:
                    xml_data['nome_transportadora'] = transporta.findtext('nfe:xNome', 'N/A', namespaces)
                else:
                    xml_data['nome_transportadora'] = 'N/A'
            else:
                xml_data['nome_transportadora'] = 'N/A'
            
            # Totais da NFe
            total = inf_nfe.find('nfe:total/nfe:ICMSTot', namespaces)
            if total is not None:
                valor_total_str = total.findtext('nfe:vNF', '0', namespaces)
                try:
                    xml_data['valor_total'] = float(valor_total_str)
                except:
                    xml_data['valor_total'] = 0.0
            else:
                xml_data['valor_total'] = 0.0
            
            # Peso bruto e volumes
            transp = inf_nfe.find('nfe:transp', namespaces)
            if transp is not None:
                # Peso bruto
                peso_bruto_str = transp.findtext('nfe:vol/nfe:pesoB', '0', namespaces)
                try:
                    xml_data['peso_bruto'] = float(peso_bruto_str)
                except:
                    xml_data['peso_bruto'] = 0.0
                
                # Contar volumes
                volumes = transp.findall('nfe:vol', namespaces)
                xml_data['volumes'] = len(volumes) if volumes else 0
            else:
                xml_data['peso_bruto'] = 0.0
                xml_data['volumes'] = 0
            
            return xml_data
            
        except Exception as e:
            logger.error(f"Erro ao processar XML: {e}")
            return None
        
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
            # Verificar estado da conexão primeiro
            try:
                stat_info = pop3.stat()
                total_messages = stat_info[0]
                logger.info(f"Total de mensagens (STAT): {total_messages}")
            except Exception as stat_error:
                logger.error(f"Erro ao obter STAT: {stat_error}")
                return messages_with_xml
            
            if total_messages == 0:
                logger.info("Nenhuma mensagem encontrada")
                return messages_with_xml
            
            # Processar cada mensagem usando apenas RETR (sem LIST)
            for i in range(1, total_messages + 1):
                try:
                    # Baixar mensagem diretamente com RETR
                    try:
                        raw_message_lines = pop3.retr(i)[1]
                        raw_message = b'\n'.join(raw_message_lines)
                        message = email.message_from_bytes(raw_message)
                    except Exception as retr_error:
                        logger.error(f"Erro RETR na mensagem {i}: {retr_error}")
                        continue
                    
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
    
    def save_xml_to_database(self, xml_attachment):
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
                    xml_file = XMLFile()
                    xml_file.user_id = self.user.id
                    xml_file.filename = xml_attachment['filename']
                    xml_file.invoice_key = xml_data.get('chave_nf', 'N/A')
                    xml_file.import_type = 'email'  # Marcar como importado via email
                    xml_file.numero_nf = xml_data.get('numero_nf', 'N/A')
                    xml_file.serie_nf = xml_data.get('serie_nf', 'N/A')
                    xml_file.data_emissao = xml_data.get('data_emissao')
                    xml_file.valor_total = xml_data.get('valor_total', 0.0)
                    xml_file.peso_bruto = xml_data.get('peso_bruto', 0.0)
                    xml_file.quantidade_volumes = xml_data.get('volumes', 0)
                    xml_file.cnpj_emitente = xml_data.get('cnpj_emitente', 'N/A')
                    xml_file.nome_emitente = xml_data.get('nome_emitente', 'N/A')
                    xml_file.destinatario_cnpj_cpf = xml_data.get('destinatario_cnpj_cpf', 'N/A')
                    # Dados do remetente (usar dados do emitente)
                    xml_file.remetente_razao = xml_data.get('nome_emitente', 'N/A')
                    xml_file.remetente_cidade = xml_data.get('cidade_emitente', 'N/A')
                    xml_file.remetente_uf = xml_data.get('uf_emitente', 'N/A')
                    xml_file.remetente_endereco = xml_data.get('endereco_emitente', 'N/A')
                    xml_file.remetente_cep = xml_data.get('cep_emitente', 'N/A')
                    # Dados do destinatário
                    xml_file.destinatario_razao = xml_data.get('nome_destinatario', 'N/A')
                    xml_file.destinatario_cidade = xml_data.get('cidade_destinatario', 'N/A')
                    xml_file.destinatario_uf = xml_data.get('uf_destinatario', 'N/A')
                    xml_file.destinatario_endereco = xml_data.get('endereco_destinatario', 'N/A')
                    xml_file.destinatario_cep = xml_data.get('cep_destinatario', 'N/A')
                    xml_file.imported_at = datetime.now()
                    
                    # Armazenar conteúdo XML no banco de dados
                    xml_file.xml_content = xml_attachment['content'].decode('utf-8')
                    
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
            
            # Buscar mensagens com XML usando abordagem robusta
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
                        xml_record = self.save_xml_to_database(xml_attachment)
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
    
    def process_user_emails(self):
        """Processa emails do usuário usando suas credenciais armazenadas"""
        if not self.user:
            return {'success': False, 'error': 'Usuário não fornecido'}
            
        if not self.user.has_pop3_configured():
            return {'success': False, 'error': 'POP3 não configurado para este usuário'}
        
        try:
            # Descriptografar a senha armazenada
            from email_encryption import decrypt_email_password
            
            stored_password_hash = getattr(self.user, 'pop3_password_hash', None)
            if not stored_password_hash:
                return {'success': False, 'error': 'Senha POP3 não encontrada'}
            
            # Descriptografar a senha para autenticação
            decrypted_password = decrypt_email_password(stored_password_hash)
            if not decrypted_password:
                return {'success': False, 'error': 'Erro ao descriptografar senha POP3'}
            
            return self.process_email_xmls(decrypted_password)
            
        except Exception as e:
            logger.error(f"Erro ao processar emails do usuário {self.user.id}: {e}")
            return {'success': False, 'error': str(e)}