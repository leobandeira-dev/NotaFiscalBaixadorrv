#!/usr/bin/env python3
"""
Teste manual para processar XML enviado por email
"""

import os
from new_app import app, db
from models import User, XMLFile
from email_xml_processor import EmailXMLProcessor
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_xml_processing():
    """Testa processamento do XML enviado via email"""
    
    with app.app_context():
        try:
            # Buscar usuário teste
            user = User.query.filter_by(email='teste@xmldownloader.com').first()
            if not user:
                logger.error("Usuário teste não encontrado")
                return
                
            logger.info(f"Testando com usuário: {user.email} (ID: {user.id})")
            
            # Verificar XMLs existentes antes
            existing_count = XMLFile.query.filter_by(user_id=user.id).count()
            logger.info(f"XMLs existentes antes: {existing_count}")
            
            # Simular XML anexado do email
            xml_filename = "42250485179240000239550020004175361171503396.xml"
            
            # Verificar se existe o arquivo XML na pasta de anexos
            xml_path = f"attached_assets/{xml_filename}"
            if os.path.exists(xml_path):
                logger.info(f"Arquivo XML encontrado: {xml_path}")
                
                # Ler conteúdo do XML
                with open(xml_path, 'rb') as f:
                    xml_content = f.read()
                
                # Criar estrutura de anexo simulada
                xml_attachment = {
                    'filename': xml_filename,
                    'content': xml_content,
                    'size': len(xml_content)
                }
                
                logger.info(f"Processando XML: {xml_filename} ({xml_attachment['size']} bytes)")
                
                # Processar XML
                xml_processor = EmailXMLProcessor(user)
                xml_file = xml_processor.save_xml_to_database(xml_attachment)
                
                if xml_file:
                    logger.info(f"✅ XML salvo com sucesso!")
                    logger.info(f"ID: {xml_file.id}")
                    logger.info(f"NF: {xml_file.numero_nf}/{xml_file.serie_nf}")
                    logger.info(f"Emitente: {xml_file.nome_emitente}")
                    logger.info(f"Destinatário: {xml_file.nome_destinatario}")
                    logger.info(f"Valor: R$ {xml_file.valor_total}")
                    logger.info(f"Tipo importação: {xml_file.import_type}")
                else:
                    logger.error("❌ Falha ao salvar XML")
                
                # Verificar XMLs após processamento
                new_count = XMLFile.query.filter_by(user_id=user.id).count()
                logger.info(f"XMLs após processamento: {new_count}")
                
            else:
                logger.error(f"Arquivo XML não encontrado: {xml_path}")
                # Listar arquivos disponíveis
                if os.path.exists("attached_assets"):
                    files = [f for f in os.listdir("attached_assets") if f.endswith('.xml')]
                    logger.info(f"Arquivos XML disponíveis: {files}")
                
        except Exception as e:
            logger.error(f"Erro no teste: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_xml_processing()