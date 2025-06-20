#!/usr/bin/env python3
"""
Test script to validate XML parsing with the real XML file
"""
import sys
import os
from xml_processor import extract_xml_data

def test_xml_parsing():
    """Test the XML parser with the actual XML file"""
    xml_file_path = "attached_assets/42250485179240000239550020004175361171503396_1750379433035.xml"
    
    if not os.path.exists(xml_file_path):
        print(f"XML file not found: {xml_file_path}")
        return
    
    # Read the XML content
    with open(xml_file_path, 'r', encoding='utf-8') as f:
        xml_content = f.read()
    
    print("XML Content (first 200 chars):")
    print(xml_content[:200])
    print("\n" + "="*50 + "\n")
    
    # Extract data using our parser
    extracted_data = extract_xml_data(xml_content)
    
    print("Extracted NFe Data:")
    print("-" * 30)
    
    # Print all extracted fields
    for key, value in extracted_data.items():
        print(f"{key}: {value}")
    
    print("\n" + "="*50)
    print("KEY FIELDS VALIDATION:")
    print("-" * 30)
    
    # Validate key fields
    required_fields = [
        'numero_nf', 'serie_nf', 'data_emissao', 'valor_total',
        'peso_bruto', 'quantidade_volumes', 'cnpj_emitente', 'nome_emitente',
        'remetente_razao', 'remetente_cidade', 'remetente_uf', 'remetente_endereco',
        'destinatario_razao', 'destinatario_cidade', 'destinatario_uf', 'destinatario_endereco'
    ]
    
    missing_fields = []
    for field in required_fields:
        value = extracted_data.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ''):
            missing_fields.append(field)
        else:
            print(f"✓ {field}: {value}")
    
    if missing_fields:
        print(f"\n❌ Missing/Empty fields: {missing_fields}")
    else:
        print(f"\n✅ All required fields extracted successfully!")

if __name__ == "__main__":
    test_xml_parsing()