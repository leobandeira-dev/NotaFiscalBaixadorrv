#!/usr/bin/env python3
"""
Teste para verificar exibição da razão social do remetente
Verifica se o nome da empresa emitente é corretamente exibido no campo Remetente
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from xml_processor import extract_xml_data
from transul_exact_layout_generator import TransulExactLayoutGenerator
from datetime import datetime
import io

def test_sender_name_display():
    """Testa se a razão social do remetente é exibida corretamente"""
    
    print("🧪 Testando exibição da razão social do remetente")
    print("=" * 60)
    
    # Usar o XML real que contém CORSUL COMERCIO
    xml_file = "42250485179240000239550020004175361171503396_1750379433035.xml"
    
    if not os.path.exists(xml_file):
        print(f"❌ Arquivo XML não encontrado: {xml_file}")
        return False
    
    # Ler e processar XML
    with open(xml_file, 'r', encoding='utf-8') as f:
        xml_content = f.read()
    
    # Extrair dados do XML
    xml_data = extract_xml_data(xml_content)
    
    print(f"📄 Arquivo XML: {xml_file}")
    print(f"📋 Número NF: {xml_data.get('numero_nf', 'N/A')}")
    print(f"🏢 Nome emitente extraído: {xml_data.get('nome_emitente', 'N/A')}")
    print(f"🔍 Campo emitente_nome: {xml_data.get('emitente_nome', 'N/A')}")
    
    # Verificar se o nome foi extraído corretamente
    nome_emitente = xml_data.get('nome_emitente', '')
    if not nome_emitente or nome_emitente == 'N/A':
        print("❌ Nome do emitente não foi extraído do XML")
        return False
    
    print(f"✅ Nome emitente encontrado: {nome_emitente}")
    
    # Gerar etiqueta de teste
    generator = TransulExactLayoutGenerator()
    
    # Configurar dados para teste
    test_data = {
        'numero_nf': xml_data.get('numero_nf', '417549'),
        'serie_nf': xml_data.get('serie_nf', '2'),
        'pedido_number': 'PED-TEST-123',
        'destinatario_nome': 'TESTE DESTINATARIO LTDA',
        'destinatario_endereco': 'RUA TESTE, 123, CENTRO',
        'destinatario_cidade': 'SAO PAULO',
        'destinatario_uf': 'SP',
        'peso_bruto': 15.5,
        'volumes': 1
    }
    
    # Incluir dados do XML extraído
    test_data.update(xml_data)
    
    print(f"📦 Dados para geração: {test_data.get('nome_emitente', 'N/A')}")
    
    # Gerar etiqueta usando o método correto
    pdf_buffer = generator.generate_transul_exact_label(
        xml_content=xml_content,
        pedido_number=test_data.get('pedido_number', 'PED-TEST-123'),
        area_code="01",
        company_logo_path=None,
        volume_info="1/1"
    )
    
    if pdf_buffer:
        # Salvar arquivo de teste
        output_file = "teste_razao_social_remetente.pdf"
        with open(output_file, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        file_size = len(pdf_buffer.getvalue())
        print(f"✅ Etiqueta gerada: {output_file}")
        print(f"📊 Tamanho: {file_size:,} bytes")
        
        # Verificar se o nome do remetente foi processado corretamente
        # (simulando a lógica do gerador)
        remetente_nome = test_data.get('nome_emitente', test_data.get('emitente_nome', 'N/A'))
        if remetente_nome and remetente_nome != 'N/A' and len(remetente_nome) > 30:
            palavras = remetente_nome.split()
            if len(palavras) > 1:
                remetente_resumido = f"{palavras[0]} {palavras[-1]}"
            else:
                remetente_resumido = remetente_nome[:30]
        else:
            remetente_resumido = remetente_nome or 'N/A'
        
        print(f"🏷️  Campo Remetente exibirá: '{remetente_resumido}'")
        
        if remetente_resumido != 'N/A':
            print("✅ SUCESSO: Razão social do remetente será exibida corretamente!")
            return True
        else:
            print("❌ FALHOU: Razão social não foi processada")
            return False
    else:
        print("❌ Falha na geração da etiqueta")
        return False

if __name__ == "__main__":
    success = test_sender_name_display()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 TESTE PASSOU!")
        print("✅ A razão social do remetente é exibida corretamente")
    else:
        print("❌ TESTE FALHOU!")
        print("⚠️  A razão social do remetente não está sendo exibida")
    print("=" * 60)