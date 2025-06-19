"""
Gerador de DANFE oficial com layout SEFAZ
Usando brazilfiscalreport para compliance total com padrão NFe modelo 55
"""

import os
import logging
from typing import Optional
from brazilfiscalreport.danfe import Danfe
from lxml import etree

logger = logging.getLogger(__name__)

class SefazDanfeGenerator:
    """Gerador DANFE com layout oficial SEFAZ usando brazilfiscalreport"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def generate_danfe_from_xml(self, xml_content: str, output_path: str) -> bool:
        """
        Gera DANFE oficial a partir do XML da NFe
        
        Args:
            xml_content: Conteúdo XML da NFe
            output_path: Caminho para salvar o PDF
            
        Returns:
            True se gerado com sucesso
        """
        try:
            self.logger.info("Iniciando geração DANFE com layout SEFAZ oficial...")
            
            # Parse do XML
            root = etree.fromstring(xml_content.encode('utf-8'))
            
            # Criar instância do DANFE
            danfe = Danfe(xml=xml_content)
            
            # Gerar PDF
            danfe.output(output_path)
            
            if os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                self.logger.info(f"DANFE SEFAZ gerado com sucesso: {output_path} ({file_size} bytes)")
                return True
            else:
                self.logger.error("Arquivo DANFE não foi criado")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao gerar DANFE SEFAZ: {str(e)}")
            return False
    
    def generate_danfe_from_file(self, xml_file_path: str, output_dir: str = "downloads") -> Optional[str]:
        """
        Gera DANFE a partir de um arquivo XML
        
        Args:
            xml_file_path: Caminho do arquivo XML
            output_dir: Diretório de saída
            
        Returns:
            Caminho do PDF gerado ou None se falhou
        """
        try:
            if not os.path.exists(xml_file_path):
                self.logger.error(f"Arquivo XML não encontrado: {xml_file_path}")
                return None
            
            # Ler XML
            with open(xml_file_path, 'r', encoding='utf-8') as f:
                xml_content = f.read()
            
            # Nome do arquivo de saída
            base_name = os.path.basename(xml_file_path).replace('.xml', '')
            output_filename = f"DANFE_SEFAZ_{base_name}.pdf"
            output_path = os.path.join(output_dir, output_filename)
            
            # Garantir que o diretório existe
            os.makedirs(output_dir, exist_ok=True)
            
            # Gerar DANFE
            if self.generate_danfe_from_xml(xml_content, output_path):
                return output_path
            else:
                return None
                
        except Exception as e:
            self.logger.error(f"Erro ao processar arquivo XML: {str(e)}")
            return None

def generate_sefaz_danfe_from_file(xml_file_path: str, output_dir: str = "downloads") -> Optional[str]:
    """
    Função utilitária para gerar DANFE SEFAZ a partir de um arquivo XML
    
    Args:
        xml_file_path: Caminho do arquivo XML
        output_dir: Diretório de saída
        
    Returns:
        Caminho do PDF gerado ou None se falhou
    """
    generator = SefazDanfeGenerator()
    return generator.generate_danfe_from_file(xml_file_path, output_dir)

if __name__ == "__main__":
    # Teste com o XML existente
    test_xml = "downloads/35250513516247000107550010000113401146202508.xml"
    if os.path.exists(test_xml):
        print(f"Testando geração DANFE SEFAZ com: {test_xml}")
        result = generate_sefaz_danfe_from_file(test_xml)
        if result:
            print(f"DANFE SEFAZ gerado: {result}")
        else:
            print("Falha na geração DANFE SEFAZ")
    else:
        print("Arquivo XML de teste não encontrado")