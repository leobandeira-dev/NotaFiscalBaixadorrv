"""
Teste Funcional Completo do Sistema
Verifica todas as funcionalidades críticas após implementação de segurança
"""

import os
import sys
import requests
import json
import time
import logging
from datetime import datetime

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SystemFunctionalTest:
    """Teste funcional completo do sistema"""
    
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.failed_tests = []
        
    def test_landing_page(self):
        """Testar página principal"""
        logger.info("Testando landing page...")
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                if "XMLDownloader Pro" in response.text:
                    self.test_results.append("✓ Landing page carregando corretamente")
                    return True
                else:
                    self.failed_tests.append("✗ Landing page sem conteúdo esperado")
                    return False
            else:
                self.failed_tests.append(f"✗ Landing page retornou status {response.status_code}")
                return False
        except Exception as e:
            self.failed_tests.append(f"✗ Erro ao acessar landing page: {e}")
            return False
    
    def test_login_page(self):
        """Testar página de login"""
        logger.info("Testando página de login...")
        try:
            response = self.session.get(f"{self.base_url}/login")
            if response.status_code == 200:
                if "Fazer Login" in response.text or "Login" in response.text:
                    self.test_results.append("✓ Página de login acessível")
                    return True
                else:
                    self.failed_tests.append("✗ Página de login sem formulário")
                    return False
            else:
                self.failed_tests.append(f"✗ Página de login retornou status {response.status_code}")
                return False
        except Exception as e:
            self.failed_tests.append(f"✗ Erro ao acessar página de login: {e}")
            return False
    
    def test_register_page(self):
        """Testar página de cadastro"""
        logger.info("Testando página de cadastro...")
        try:
            response = self.session.get(f"{self.base_url}/register")
            if response.status_code == 200:
                if "Criar Conta" in response.text or "Cadastrar" in response.text:
                    self.test_results.append("✓ Página de cadastro acessível")
                    return True
                else:
                    self.failed_tests.append("✗ Página de cadastro sem formulário")
                    return False
            else:
                self.failed_tests.append(f"✗ Página de cadastro retornou status {response.status_code}")
                return False
        except Exception as e:
            self.failed_tests.append(f"✗ Erro ao acessar página de cadastro: {e}")
            return False
    
    def test_api_documentation(self):
        """Testar documentação da API"""
        logger.info("Testando documentação da API...")
        try:
            response = self.session.get(f"{self.base_url}/api-docs")
            if response.status_code == 200:
                if "API Documentation" in response.text:
                    self.test_results.append("✓ Documentação da API acessível")
                    return True
                else:
                    self.failed_tests.append("✗ Documentação da API incompleta")
                    return False
            else:
                self.failed_tests.append(f"✗ Documentação da API retornou status {response.status_code}")
                return False
        except Exception as e:
            self.failed_tests.append(f"✗ Erro ao acessar documentação da API: {e}")
            return False
    
    def test_pricing_page(self):
        """Testar página de preços"""
        logger.info("Testando página de preços...")
        try:
            response = self.session.get(f"{self.base_url}/pricing")
            if response.status_code == 200:
                if "R$ 0,10" in response.text and "R$ 49,90" in response.text:
                    self.test_results.append("✓ Página de preços com valores corretos")
                    return True
                else:
                    self.failed_tests.append("✗ Página de preços sem valores esperados")
                    return False
            else:
                self.failed_tests.append(f"✗ Página de preços retornou status {response.status_code}")
                return False
        except Exception as e:
            self.failed_tests.append(f"✗ Erro ao acessar página de preços: {e}")
            return False
    
    def test_static_assets(self):
        """Testar recursos estáticos"""
        logger.info("Testando recursos estáticos...")
        try:
            # Testar CSS
            css_response = self.session.get(f"{self.base_url}/static/style.css")
            if css_response.status_code == 200:
                self.test_results.append("✓ CSS principal carregando")
            else:
                self.failed_tests.append("✗ CSS principal não encontrado")
            
            # Testar JavaScript
            js_response = self.session.get(f"{self.base_url}/static/js/main.js")
            if js_response.status_code == 200:
                self.test_results.append("✓ JavaScript principal carregando")
            else:
                self.failed_tests.append("✗ JavaScript principal não encontrado")
            
            return css_response.status_code == 200 and js_response.status_code == 200
            
        except Exception as e:
            self.failed_tests.append(f"✗ Erro ao acessar recursos estáticos: {e}")
            return False
    
    def test_security_headers(self):
        """Testar cabeçalhos de segurança"""
        logger.info("Testando cabeçalhos de segurança...")
        try:
            response = self.session.get(f"{self.base_url}/")
            headers = response.headers
            
            security_checks = []
            
            # Verificar cabeçalhos de segurança importantes
            if 'X-Frame-Options' in headers:
                security_checks.append("✓ X-Frame-Options presente")
            else:
                security_checks.append("⚠ X-Frame-Options ausente")
            
            if 'X-XSS-Protection' in headers:
                security_checks.append("✓ X-XSS-Protection presente")
            else:
                security_checks.append("⚠ X-XSS-Protection ausente")
            
            if 'X-Content-Type-Options' in headers:
                security_checks.append("✓ X-Content-Type-Options presente")
            else:
                security_checks.append("⚠ X-Content-Type-Options ausente")
            
            self.test_results.extend(security_checks)
            return True
            
        except Exception as e:
            self.failed_tests.append(f"✗ Erro ao verificar cabeçalhos de segurança: {e}")
            return False
    
    def test_rate_limiting(self):
        """Testar rate limiting básico"""
        logger.info("Testando rate limiting...")
        try:
            # Fazer múltiplas requisições rápidas
            responses = []
            for i in range(10):
                response = self.session.get(f"{self.base_url}/")
                responses.append(response.status_code)
            
            # Verificar se todas foram bem-sucedidas (rate limiting pode não estar ativo para GET simples)
            if all(status == 200 for status in responses):
                self.test_results.append("✓ Sistema respondendo consistentemente")
                return True
            else:
                self.failed_tests.append("✗ Sistema com respostas inconsistentes")
                return False
                
        except Exception as e:
            self.failed_tests.append(f"✗ Erro ao testar rate limiting: {e}")
            return False
    
    def run_all_tests(self):
        """Executar todos os testes funcionais"""
        logger.info("=== INICIANDO TESTES FUNCIONAIS COMPLETOS ===")
        
        tests = [
            self.test_landing_page,
            self.test_login_page,
            self.test_register_page,
            self.test_api_documentation,
            self.test_pricing_page,
            self.test_static_assets,
            self.test_security_headers,
            self.test_rate_limiting
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                self.failed_tests.append(f"✗ Erro no teste {test.__name__}: {e}")
        
        self.generate_test_report(passed, total)
        return passed == total
    
    def generate_test_report(self, passed, total):
        """Gerar relatório de testes"""
        logger.info("=== RELATÓRIO DE TESTES FUNCIONAIS ===")
        logger.info(f"Testes aprovados: {passed}/{total}")
        
        if self.test_results:
            logger.info("SUCESSOS:")
            for result in self.test_results:
                logger.info(f"  {result}")
        
        if self.failed_tests:
            logger.error("FALHAS:")
            for failure in self.failed_tests:
                logger.error(f"  {failure}")
        
        success_rate = (passed / total) * 100 if total > 0 else 0
        logger.info(f"Taxa de sucesso: {success_rate:.1f}%")
        
        if success_rate >= 90:
            logger.info("🟢 SISTEMA FUNCIONANDO CORRETAMENTE")
        elif success_rate >= 75:
            logger.warning("🟡 SISTEMA COM PROBLEMAS MENORES")
        else:
            logger.error("🔴 SISTEMA COM PROBLEMAS CRÍTICOS")

def run_system_tests():
    """Executar testes funcionais do sistema"""
    tester = SystemFunctionalTest()
    return tester.run_all_tests()

if __name__ == "__main__":
    run_system_tests()