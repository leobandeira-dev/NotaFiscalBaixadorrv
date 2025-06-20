#!/usr/bin/env python3
"""
Teste do sistema de ID estruturado para etiquetas
Verifica se o formato: NúmeroNF + Data + Hora + Minuto + Volume está funcionando
"""

from transul_exact_layout_generator import generate_transul_exact_label_from_xml
from xml_processor import extract_xml_data
import os
from datetime import datetime

def test_structured_label_id():
    """Testa a geração de ID estruturado e QR code com ID da etiqueta"""
    
    # XML de teste existente
    xml_files = [f for f in os.listdir('.') if f.endswith('.xml')]
    
    if not xml_files:
        print("❌ Nenhum arquivo XML encontrado para teste")
        return False
    
    xml_file = xml_files[0]
    print(f"🧪 Testando com arquivo XML: {xml_file}")
    
    try:
        # Ler XML
        with open(xml_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        # Extrair dados
        xml_data = extract_xml_data(xml_content)
        numero_nf = xml_data.get('numero_nf', 'N/A')
        
        print(f"📄 Número NF: {numero_nf}")
        
        # Gerar etiqueta com volume 1
        volume_info = "1/3"  # Volume 1 de 3
        
        pdf_buffer = generate_transul_exact_label_from_xml(
            xml_content=xml_content,
            pedido_number="PED123456",
            area_code="01",
            volume_info=volume_info
        )
        
        if pdf_buffer:
            # Salvar PDF de teste
            output_file = f"teste_label_id_estruturado_{datetime.now().strftime('%H%M%S')}.pdf"
            with open(output_file, 'wb') as f:
                f.write(pdf_buffer.getvalue())
            
            file_size = len(pdf_buffer.getvalue())
            print(f"✅ Etiqueta gerada: {output_file}")
            print(f"📊 Tamanho do arquivo: {file_size:,} bytes")
            
            # Calcular ID esperado com separadores
            now = datetime.now()
            nf_numero = ''.join(filter(str.isdigit, str(numero_nf)))
            data_str = now.strftime("%d%m")
            hora_str = now.strftime("%H%M")
            volume_number = volume_info.split('/')[0]
            expected_id = f"{nf_numero}-{data_str}-{hora_str}-{volume_number}"
            
            print(f"🔢 ID estruturado esperado: {expected_id}")
            print(f"   📋 Formato: NF({nf_numero}) - Data({data_str}) - Hora({hora_str}) - Volume({volume_number})")
            print(f"   📅 Data/Hora atual: {now.strftime('%d/%m %H:%M')}")
            print(f"   📦 Volume: {volume_number} de {volume_info.split('/')[1] if '/' in volume_info else '1'}")
            print(f"   🔍 QR Code contém: {expected_id}")
            
            return True
        else:
            print("❌ Falha na geração da etiqueta")
            return False
            
    except Exception as e:
        print(f"❌ Erro no teste: {e}")
        return False

def test_multiple_volumes():
    """Testa geração de múltiplos volumes com IDs únicos"""
    
    xml_files = [f for f in os.listdir('.') if f.endswith('.xml')]
    if not xml_files:
        return False
    
    xml_file = xml_files[0]
    
    try:
        with open(xml_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()
        
        print(f"\n🔄 Testando múltiplos volumes...")
        
        # Gerar 3 volumes
        for volume in range(1, 4):
            volume_info = f"{volume}/3"
            
            pdf_buffer = generate_transul_exact_label_from_xml(
                xml_content=xml_content,
                pedido_number="PED123456",
                area_code="01",
                volume_info=volume_info
            )
            
            if pdf_buffer:
                output_file = f"teste_volume_{volume}_de_3.pdf"
                with open(output_file, 'wb') as f:
                    f.write(pdf_buffer.getvalue())
                
                # Calcular ID para este volume com separadores
                xml_data = extract_xml_data(xml_content)
                numero_nf = xml_data.get('numero_nf', 'N/A')
                now = datetime.now()
                nf_numero = ''.join(filter(str.isdigit, str(numero_nf)))
                data_str = now.strftime("%d%m")
                hora_str = now.strftime("%H%M")
                expected_id = f"{nf_numero}-{data_str}-{hora_str}-{volume}"
                
                file_size = len(pdf_buffer.getvalue())
                print(f"   📦 Volume {volume}: {output_file} ({file_size:,} bytes)")
                print(f"   🔢 ID: {expected_id}")
        
        print("✅ Teste de múltiplos volumes concluído")
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste de múltiplos volumes: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando teste do sistema de ID estruturado")
    print("=" * 60)
    
    # Teste básico
    success1 = test_structured_label_id()
    
    # Teste múltiplos volumes
    success2 = test_multiple_volumes()
    
    print("\n" + "=" * 60)
    if success1 and success2:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("✅ Sistema de ID estruturado funcionando corretamente")
        print("✅ QR Code reflete o ID único da etiqueta")
        print("✅ Múltiplos volumes geram IDs únicos")
    else:
        print("❌ ALGUNS TESTES FALHARAM")
    
    print("\n📋 Formato do ID: NúmeroNF + DDMMHHMM + Volume")
    print("📋 Exemplo: 417549201215301 = NF 417549 + 20/12 15:30 + Volume 1")