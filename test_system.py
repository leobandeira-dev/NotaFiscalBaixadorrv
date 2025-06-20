#!/usr/bin/env python3
"""
Teste completo do sistema após correções
Verifica se os XMLs estão sendo salvos corretamente no banco de dados
"""

from new_app import app
from models import db, XMLFile, ImportedXML, User, UsageRecord

def test_system():
    with app.app_context():
        print('=== TESTE APÓS CORREÇÕES ===')
        print()
        
        # Verificar usuários
        users = User.query.all()
        print(f'Total de usuários: {len(users)}')
        for user in users:
            print(f'  - {user.email} (ID: {user.id}, Trial até: {user.trial_expires_at})')
        print()
        
        # Verificar XMLs registrados
        xml_files = XMLFile.query.all()
        imported_xmls = ImportedXML.query.all()
        
        print(f'XMLs na tabela XMLFile: {len(xml_files)}')
        for xml in xml_files:
            print(f'  - {xml.invoice_key} (User: {xml.user_id}, Data: {xml.imported_at})')
        print()
        
        print(f'XMLs na tabela ImportedXML: {len(imported_xmls)}')
        for xml in imported_xmls:
            print(f'  - {xml.invoice_key} (User: {xml.user_id}, Data: {xml.imported_at})')
        print()
        
        # Verificar UsageRecord
        usage_records = UsageRecord.query.all()
        print(f'Registros de uso: {len(usage_records)}')
        for record in usage_records:
            print(f'  - {record.description} (User: {record.user_id}, Custo: R${record.cost:.2f}, Data: {record.created_at})')
        print()
        
        print('=== TESTE DE NOVO DOWNLOAD ===')
        # Simular um novo download para testar o sistema corrigido
        from automation_fixed import InvoiceDownloader
        
        downloader = InvoiceDownloader()
        
        # XML de teste com namespace correto
        test_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
    <NFe>
        <infNFe>
            <ide>
                <nNF>123456</nNF>
                <serie>1</serie>
                <dhEmi>2025-06-19T10:30:00</dhEmi>
            </ide>
            <emit>
                <CNPJ>12345678000123</CNPJ>
                <xNome>Empresa Teste</xNome>
            </emit>
            <total>
                <ICMSTot>
                    <vNF>150.00</vNF>
                </ICMSTot>
            </total>
        </infNFe>
    </NFe>
</nfeProc>'''
        
        # Testar salvamento com contexto Flask
        result = downloader.save_xml_content(
            xml_content=test_xml,
            invoice_key='12345678901234567890123456789012345678901234',
            job_id='test-job-123',
            user_id=2  # Use user ID 2 (leonardobandeir@gmail.com)
        )
        
        print(f'Resultado do teste de salvamento: {result}')
        
        # Verificar se foi salvo
        imported_xmls_after = ImportedXML.query.all()
        print(f'XMLs após teste: {len(imported_xmls_after)}')
        
        if len(imported_xmls_after) > len(imported_xmls):
            print('✅ SUCESSO: XML foi salvo no banco de dados!')
            new_xml = imported_xmls_after[-1]
            print(f'   - Chave: {new_xml.invoice_key}')
            print(f'   - Emissor: {new_xml.nome_emitente}')
            print(f'   - Valor: R$ {new_xml.valor_total}')
            print(f'   - Data: {new_xml.imported_at}')
        else:
            print('❌ ERRO: XML não foi salvo no banco de dados')

if __name__ == '__main__':
    test_system()