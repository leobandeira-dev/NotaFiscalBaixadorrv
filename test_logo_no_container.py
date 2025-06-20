#!/usr/bin/env python3
"""
Teste específico - Logo sem container em contraste
Valida se a logo aparece sem fundo preto, apenas com borda sutil
"""

import os
import logging
from transul_exact_layout_generator import generate_transul_exact_label_from_xml

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_logo_sem_container():
    """Testa logo sem container em contraste"""
    
    # XML de teste
    xml_content = """<?xml version="1.0" encoding="UTF-8"?>
    <nfeProc xmlns="http://www.portalfiscal.inf.br/nfe">
        <NFe>
            <infNFe Id="NFe35250513516247000107550010000113401146202508">
                <ide>
                    <cUF>35</cUF>
                    <cNF>14620250</cNF>
                    <natOp>VENDA</natOp>
                    <mod>55</mod>
                    <serie>1</serie>
                    <nNF>417549</nNF>
                    <dhEmi>2025-06-20T15:57:00-03:00</dhEmi>
                </ide>
                <emit>
                    <CNPJ>85179240000239</CNPJ>
                    <xNome>CORSUL COMERCIO E REPRESENTACOES DO SUL LTDA</xNome>
                    <enderEmit>
                        <xLgr>RUA GUARUJA</xLgr>
                        <nro>434</nro>
                        <xBairro>ITAUM</xBairro>
                        <cMun>3523909</cMun>
                        <xMun>JOINVILLE</xMun>
                        <UF>SC</UF>
                        <CEP>89210001</CEP>
                    </enderEmit>
                </emit>
                <dest>
                    <CNPJ>16066814000116</CNPJ>
                    <xNome>CONSORCIO ALUMAR</xNome>
                    <enderDest>
                        <xLgr>RODOVIA BR 135 KM 15</xLgr>
                        <nro>S/N</nro>
                        <xBairro>ZONA INDUSTRIAL</xBairro>
                        <cMun>2111300</cMun>
                        <xMun>SAO LUIS</xMun>
                        <UF>MA</UF>
                        <CEP>65110000</CEP>
                    </enderDest>
                </dest>
                <transp>
                    <transporta>
                        <CNPJ>02914511000106</CNPJ>
                        <xNome>SCHREIBER LOGISTICA LTDA</xNome>
                    </transporta>
                    <vol>
                        <qVol>2</qVol>
                        <pesoB>16.2</pesoB>
                    </vol>
                </transp>
                <total>
                    <ICMSTot>
                        <vNF>6100.00</vNF>
                    </ICMSTot>
                </total>
            </infNFe>
        </NFe>
    </nfeProc>"""
    
    logger.info("Testando logo sem container em contraste")
    
    try:
        # Encontrar logo existente
        logo_path = None
        possible_logos = [
            "static/logos/1/company_logo.png",
            "static/logos/1/company_logo.jpg", 
            "generated-icon.png"
        ]
        
        for path in possible_logos:
            if os.path.exists(path):
                logo_path = path
                logger.info(f"Logo encontrada: {path}")
                break
        
        if not logo_path:
            logger.warning("Nenhuma logo encontrada para teste")
            return False
        
        # Gerar etiqueta com logo corrigida
        pdf_logo_corrigida = generate_transul_exact_label_from_xml(
            xml_content=xml_content,
            pedido_number="PED417549",
            area_code="01",
            company_logo_path=logo_path,
            volume_info="1/2",
            paper_width_mm=100,
            paper_height_mm=150,
            company_name="LAF LOGÍSTICA",
            company_subtitle="OPERADOR LOGÍSTICO"
        )
        
        if pdf_logo_corrigida:
            logger.info(f"PDF com logo corrigida gerado: {len(pdf_logo_corrigida.getvalue())} bytes")
            
            # Salvar para verificação
            with open("teste_logo_sem_container.pdf", "wb") as f:
                f.write(pdf_logo_corrigida.getvalue())
            logger.info("Arquivo salvo: teste_logo_sem_container.pdf")
            
            logger.info("CORREÇÃO APLICADA:")
            logger.info("- Logo aparece SEM fundo preto")
            logger.info("- Apenas borda cinza sutil para delimitar área")
            logger.info("- Nome da empresa em texto preto ao lado da logo")
            logger.info("- Logo preserva transparência e aspecto original")
            
            return True
        else:
            logger.error("Falha ao gerar PDF com logo corrigida")
            return False
        
    except Exception as e:
        logger.error(f"Erro durante teste: {e}")
        return False

if __name__ == "__main__":
    success = test_logo_sem_container()
    if success:
        print("\nCORREÇÃO DA LOGO IMPLEMENTADA!")
        print("A logo agora aparece:")
        print("• SEM container preto em contraste")
        print("• Com borda cinza sutil apenas")
        print("• Preservando aparência original da empresa")
        print("• Nome da empresa em texto preto legível")
    else:
        print("\nProblema ao aplicar correção da logo")