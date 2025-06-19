"""
Teste simples para verificar se a geração de DANFE está funcionando
"""

import os
from simple_danfe import generate_simple_danfe

# XML de teste simples
xml_test = '''<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
    <NFe>
        <infNFe Id="NFe35200513516247000107550010000113401146202508">
            <ide>
                <cUF>35</cUF>
                <cNF>14620250</cNF>
                <natOp>Venda</natOp>
                <mod>55</mod>
                <serie>1</serie>
                <nNF>11340</nNF>
                <dhEmi>2025-06-19T10:00:00-03:00</dhEmi>
                <tpNF>1</tpNF>
                <idDest>1</idDest>
                <cMunFG>3550308</cMunFG>
                <tpImp>1</tpImp>
                <tpEmis>1</tpEmis>
                <cDV>8</cDV>
                <tpAmb>1</tpAmb>
                <finNFe>1</finNFe>
                <indFinal>1</indFinal>
                <indPres>1</indPres>
            </ide>
            <emit>
                <CNPJ>13516247000107</CNPJ>
                <xNome>Empresa Teste LTDA</xNome>
                <enderEmit>
                    <xLgr>Rua Teste</xLgr>
                    <nro>123</nro>
                    <xBairro>Centro</xBairro>
                    <cMun>3550308</cMun>
                    <xMun>São Paulo</xMun>
                    <UF>SP</UF>
                    <CEP>01234567</CEP>
                </enderEmit>
                <IE>123456789</IE>
            </emit>
            <dest>
                <CNPJ>11222333000199</CNPJ>
                <xNome>Cliente Teste LTDA</xNome>
                <enderDest>
                    <xLgr>Avenida Teste</xLgr>
                    <nro>456</nro>
                    <xBairro>Vila Teste</xBairro>
                    <cMun>3550308</cMun>
                    <xMun>São Paulo</xMun>
                    <UF>SP</UF>
                    <CEP>09876543</CEP>
                </enderDest>
                <IE>987654321</IE>
            </dest>
            <det nItem="1">
                <prod>
                    <cProd>001</cProd>
                    <xProd>Produto de Teste</xProd>
                    <NCM>12345678</NCM>
                    <CFOP>5102</CFOP>
                    <uCom>UN</uCom>
                    <qCom>1.0000</qCom>
                    <vUnCom>100.0000</vUnCom>
                    <vProd>100.00</vProd>
                </prod>
            </det>
            <total>
                <ICMSTot>
                    <vBC>100.00</vBC>
                    <vICMS>18.00</vICMS>
                    <vBCST>0.00</vBCST>
                    <vST>0.00</vST>
                    <vProd>100.00</vProd>
                    <vFrete>0.00</vFrete>
                    <vSeg>0.00</vSeg>
                    <vDesc>0.00</vDesc>
                    <vNF>100.00</vNF>
                </ICMSTot>
            </total>
        </infNFe>
    </NFe>
</nfeProc>'''

def test_danfe_generation():
    """Teste de geração de DANFE"""
    print("Testando geração de DANFE...")
    
    # Criar diretório de downloads se não existir
    os.makedirs('downloads', exist_ok=True)
    
    # Gerar DANFE
    output_path = 'downloads/test_danfe.pdf'
    success = generate_simple_danfe(xml_test, output_path)
    
    if success:
        print(f"✓ DANFE gerado com sucesso: {output_path}")
        print(f"✓ Tamanho do arquivo: {os.path.getsize(output_path)} bytes")
        return True
    else:
        print("✗ Falha na geração do DANFE")
        return False

if __name__ == "__main__":
    test_danfe_generation()