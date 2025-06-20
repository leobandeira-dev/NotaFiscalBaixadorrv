#!/usr/bin/env python3
"""
Teste do Sistema de Enquadramento Completo
Valida a implementação dos estilos Layout 1 e Layout 2 em todas as seções
"""

import sys
import os
from io import BytesIO

# Adicionar path do projeto
sys.path.append('.')

from responsive_label_generator import ResponsiveTransportLabelGenerator

def test_framing_system():
    """Testa o sistema de enquadramento com XML real"""
    print("🔧 Testando sistema de enquadramento completo...")
    
    # XML de teste (REAL SINALIZACAO)
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
    <NFe xmlns="http://www.portalfiscal.inf.br/nfe">
        <infNFe Id="NFe35250513516247000107550010000113401146202508" versao="4.00">
            <ide>
                <cUF>35</cUF>
                <cNF>14620250</cNF>
                <natOp>VENDA</natOp>
                <mod>55</mod>
                <serie>1</serie>
                <nNF>11340</nNF>
                <dhEmi>2025-05-27T10:30:00-03:00</dhEmi>
                <tpNF>1</tpNF>
                <idDest>2</idDest>
                <cMunFG>3525904</cMunFG>
                <tpImp>1</tpImp>
                <tpEmis>1</tpEmis>
                <cDV>8</cDV>
                <tpAmb>1</tpAmb>
                <finNFe>1</finNFe>
                <indFinal>0</indFinal>
                <indPres>9</indPres>
            </ide>
            <emit>
                <CNPJ>13516247000107</CNPJ>
                <xNome>REAL SINALIZACAO INDUSTRIA COMERCIO E SERVICOS LTDA ME</xNome>
                <enderEmit>
                    <xLgr>RUA GUARUJA</xLgr>
                    <nro>434</nro>
                    <xBairro>ITAUM</xBairro>
                    <cMun>4208203</cMun>
                    <xMun>JOINVILLE</xMun>
                    <UF>SC</UF>
                    <CEP>89210440</CEP>
                </enderEmit>
            </emit>
            <dest>
                <CNPJ>06347493000158</CNPJ>
                <xNome>CONSORCIO ALUMAR</xNome>
                <enderDest>
                    <xLgr>ESTRADA DO PORTINHO</xLgr>
                    <nro>S/N</nro>
                    <xBairro>PORTINHO</xBairro>
                    <cMun>2111300</cMun>
                    <xMun>SAO LUIS</xMun>
                    <UF>MA</UF>
                    <CEP>65110000</CEP>
                </enderDest>
            </dest>
            <total>
                <ICMSTot>
                    <vNF>13585.25</vNF>
                </ICMSTot>
            </total>
            <transp>
                <modFrete>0</modFrete>
                <transporta>
                    <CNPJ>92252077000106</CNPJ>
                    <xNome>SCHREIBER LOGISTICA LTDA</xNome>
                </transporta>
                <vol>
                    <qVol>62</qVol>
                    <esp>VOLUMES</esp>
                    <pesoL>856.200</pesoL>
                    <pesoB>856.200</pesoB>
                </vol>
            </transp>
        </infNFe>
    </NFe>
</nfeProc>"""
    
    try:
        # Testar Layout 1 (Moderno - fundos cinza)
        print("\n📋 Testando Layout 1 (Moderno - fundos cinza)...")
        generator_layout1 = ResponsiveTransportLabelGenerator(
            company_name="CROSS TRANSPORTE",
            company_subtitle="LOGISTICS",
            paper_width_mm=100,
            paper_height_mm=150,
            layout_style="layout1"
        )
        
        pdf_buffer_layout1 = generator_layout1.generate_transport_label_with_volume_info(
            xml_content=xml_content,
            pedido_number="CROSS-001",
            area_code="01",
            volume_info="5/62",
            current_volume=5,
            total_volumes=62
        )
        
        if pdf_buffer_layout1 and len(pdf_buffer_layout1.getvalue()) > 1000:
            print(f"✅ Layout 1 gerado com sucesso: {len(pdf_buffer_layout1.getvalue())} bytes")
        else:
            print("❌ Falha na geração do Layout 1")
            return False
        
        # Testar Layout 2 (Alto contraste - faixas pretas)
        print("\n📋 Testando Layout 2 (Alto contraste - faixas pretas)...")
        generator_layout2 = ResponsiveTransportLabelGenerator(
            company_name="CROSS TRANSPORTE",
            company_subtitle="LOGISTICS", 
            paper_width_mm=100,
            paper_height_mm=150,
            layout_style="layout2"
        )
        
        pdf_buffer_layout2 = generator_layout2.generate_transport_label_with_volume_info(
            xml_content=xml_content,
            pedido_number="CROSS-002",
            area_code="02",
            volume_info="15/62",
            current_volume=15,
            total_volumes=62
        )
        
        if pdf_buffer_layout2 and len(pdf_buffer_layout2.getvalue()) > 1000:
            print(f"✅ Layout 2 gerado com sucesso: {len(pdf_buffer_layout2.getvalue())} bytes")
        else:
            print("❌ Falha na geração do Layout 2")
            return False
        
        # Salvar PDFs de teste para verificação visual
        with open('teste_layout1_enquadramento.pdf', 'wb') as f:
            f.write(pdf_buffer_layout1.getvalue())
        
        with open('teste_layout2_enquadramento.pdf', 'wb') as f:
            f.write(pdf_buffer_layout2.getvalue())
        
        print("\n✅ Sistema de enquadramento completo implementado com sucesso!")
        print("📁 Arquivos de teste salvos:")
        print("   - teste_layout1_enquadramento.pdf (Moderno - fundos cinza)")
        print("   - teste_layout2_enquadramento.pdf (Alto contraste - faixas pretas)")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro no teste: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_framing_system()
    sys.exit(0 if success else 1)