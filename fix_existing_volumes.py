#!/usr/bin/env python3
"""
Script para corrigir quantidade_volumes nos XMLs existentes no banco
"""
import os
import sys
sys.path.append('.')

from new_app import app
from models import db, XMLFile
from xml_processor import extract_xml_data

def fix_existing_volumes():
    """Corrige quantidade_volumes nos XMLs existentes"""
    with app.app_context():
        print("🔧 Corrigindo quantidade_volumes nos XMLs existentes...")
        print()
        
        # Buscar XMLs com quantidade_volumes = 0
        xmls_to_fix = XMLFile.query.filter_by(quantidade_volumes=0).all()
        
        print(f"📋 Encontrados {len(xmls_to_fix)} XMLs para corrigir")
        print()
        
        fixed_count = 0
        
        for xml_file in xmls_to_fix:
            try:
                # Extrair dados do XML content
                xml_data = extract_xml_data(xml_file.xml_content, xml_file.filename)
                
                # Verificar se tem volumes para corrigir
                volumes = xml_data.get('quantidade_volumes', 0)
                
                if volumes > 0:
                    print(f"✏️  Corrigindo NF {xml_file.numero_nf}: {xml_file.quantidade_volumes} → {volumes} volumes")
                    
                    # Atualizar quantidade_volumes
                    xml_file.quantidade_volumes = volumes
                    fixed_count += 1
                else:
                    print(f"⚠️  NF {xml_file.numero_nf}: sem volumes no XML")
                    
            except Exception as e:
                print(f"❌ Erro ao processar NF {xml_file.numero_nf}: {e}")
        
        # Salvar mudanças
        if fixed_count > 0:
            db.session.commit()
            print()
            print(f"✅ {fixed_count} XMLs corrigidos com sucesso!")
        else:
            print()
            print("ℹ️  Nenhum XML precisou ser corrigido")
        
        # Verificar resultado
        print()
        print("📊 Status após correção:")
        total_xmls = XMLFile.query.count()
        xmls_with_volumes = XMLFile.query.filter(XMLFile.quantidade_volumes > 0).count()
        xmls_without_volumes = XMLFile.query.filter_by(quantidade_volumes=0).count()
        
        print(f"   Total de XMLs: {total_xmls}")
        print(f"   Com volumes: {xmls_with_volumes}")
        print(f"   Sem volumes: {xmls_without_volumes}")

if __name__ == "__main__":
    fix_existing_volumes()