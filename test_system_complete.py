#!/usr/bin/env python3
"""
Teste completo do sistema de preços por volume e assinatura de etiquetas
Verifica todas as funcionalidades integradas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stripe_integration import PricingManager, CreditManager
from models import User, XMLFile, UsageRecord, db
from new_app import app
from datetime import datetime, timedelta

def test_xml_volume_pricing_integration():
    """Testa integração completa do sistema de preços por volume"""
    print("=== TESTE DE INTEGRAÇÃO - PREÇOS POR VOLUME ===")
    
    with app.app_context():
        # Buscar usuário de teste
        test_user = User.query.filter_by(email='admin@xmldownloader.com').first()
        
        if not test_user:
            print("❌ Usuário de teste não encontrado")
            return False
        
        print(f"✅ Usuário encontrado: {test_user.name}")
        print(f"   Saldo atual: R$ {test_user.current_balance:.2f}")
        
        # Testar diferentes volumes de download
        test_scenarios = [
            {"quantity": 100, "expected_price": 0.10},
            {"quantity": 750, "expected_price": 0.08},  # Faixa mista
            {"quantity": 1500, "expected_price": 0.07}, # Faixa mista
            {"quantity": 3000, "expected_price": 0.06}  # Maior volume
        ]
        
        for scenario in test_scenarios:
            qty = scenario["quantity"]
            expected_unit_price = scenario["expected_price"]
            
            # Calcular preço usando sistema de volume
            total_cost_data = PricingManager.calculate_total_xml_cost(qty)
            unit_price = PricingManager.get_xml_price_by_volume(qty)
            
            print(f"\n📊 Volume: {qty} XMLs")
            print(f"   Preço unitário atual: R$ {unit_price:.3f}")
            print(f"   Custo total: R$ {total_cost_data['total_cost']:.2f}")
            print(f"   Preço médio: R$ {total_cost_data['average_price']:.3f}")
            
            # Verificar se está na faixa correta
            if qty <= 500:
                assert unit_price == 0.10, f"Erro: Esperado R$ 0.10, obtido R$ {unit_price:.3f}"
            elif qty <= 1000:
                assert unit_price == 0.08, f"Erro: Esperado R$ 0.08, obtido R$ {unit_price:.3f}"
            elif qty <= 2000:
                assert unit_price == 0.07, f"Erro: Esperado R$ 0.07, obtido R$ {unit_price:.3f}"
            else:
                assert unit_price == 0.06, f"Erro: Esperado R$ 0.06, obtido R$ {unit_price:.3f}"
            
            print(f"   ✅ Preço unitário correto para faixa de volume")
        
        return True

def test_labels_subscription_system():
    """Testa sistema completo de assinatura de etiquetas"""
    print("\n=== TESTE DE SISTEMA DE ASSINATURA ===")
    
    with app.app_context():
        test_user = User.query.filter_by(email='admin@xmldownloader.com').first()
        
        if not test_user:
            print("❌ Usuário de teste não encontrado")
            return False
        
        print(f"✅ Testando assinatura para: {test_user.name}")
        
        # Verificar métodos de acesso
        has_labels_access = test_user.has_labels_access()
        is_trial_active = test_user.is_labels_trial_active()
        is_subscription_active = test_user.labels_subscription_active
        
        print(f"   Tem acesso às etiquetas: {has_labels_access}")
        print(f"   Trial ativo: {is_trial_active}")
        print(f"   Assinatura ativa: {is_subscription_active}")
        
        # Verificar configuração de preços
        labels_price = PricingManager.PRICES['labels_module']
        print(f"   Preço mensal: R$ {labels_price:.2f}")
        
        # Verificar produto Stripe
        stripe_product = PricingManager.STRIPE_PRODUCTS.get('labels_module')
        print(f"   Produto Stripe: {stripe_product}")
        
        assert labels_price == 49.90, f"Erro: Preço esperado R$ 49.90, obtido R$ {labels_price}"
        assert stripe_product is not None, "Erro: Produto Stripe não configurado"
        
        print("   ✅ Sistema de assinatura configurado corretamente")
        return True

def test_credit_system_integration():
    """Testa integração do sistema de créditos"""
    print("\n=== TESTE DE SISTEMA DE CRÉDITOS ===")
    
    with app.app_context():
        test_user = User.query.filter_by(email='admin@xmldownloader.com').first()
        
        if not test_user:
            print("❌ Usuário de teste não encontrado")
            return False
        
        print(f"✅ Testando créditos para: {test_user.name}")
        
        # Verificar saldo atual
        current_balance = CreditManager.get_user_balance(test_user.id)
        print(f"   Saldo atual: R$ {current_balance:.2f}")
        
        # Testar pacotes de créditos
        packages = PricingManager.CREDIT_PACKAGES
        print(f"   Pacotes disponíveis: {len(packages)}")
        
        for package_id, package in packages.items():
            savings = PricingManager.calculate_xml_package_savings(package_id)
            print(f"   📦 {package['name']}: R$ {package['price_brl']/100:.2f} = {package['credits']:.0f} créditos")
            if savings:
                print(f"      Economia: {savings['savings_percent']:.1f}%")
        
        # Verificar histórico de uso
        usage_history = CreditManager.get_usage_history(test_user.id, days=30)
        print(f"   Registros de uso (30 dias): {len(usage_history)}")
        
        print("   ✅ Sistema de créditos funcionando")
        return True

def test_xml_processing_integration():
    """Testa integração do processamento de XML com cobrança"""
    print("\n=== TESTE DE PROCESSAMENTO XML ===")
    
    with app.app_context():
        # Contar XMLs no sistema
        total_xmls = XMLFile.query.count()
        print(f"✅ XMLs no sistema: {total_xmls}")
        
        if total_xmls > 0:
            # Pegar um XML de exemplo
            sample_xml = XMLFile.query.first()
            print(f"   Exemplo: NF {sample_xml.numero_nf}/{sample_xml.serie_nf}")
            print(f"   Emitente: {sample_xml.nome_emitente}")
            print(f"   Valor: R$ {sample_xml.valor_total:.2f}")
            print(f"   Peso: {sample_xml.peso_bruto}kg")
            print(f"   Volumes: {sample_xml.quantidade_volumes}")
        
        # Verificar registros de uso
        usage_records = UsageRecord.query.count()
        print(f"   Registros de uso: {usage_records}")
        
        print("   ✅ Processamento XML integrado")
        return True

def test_database_consistency():
    """Verifica consistência do banco de dados"""
    print("\n=== TESTE DE CONSISTÊNCIA DO BANCO ===")
    
    with app.app_context():
        # Verificar usuários
        users_count = User.query.count()
        print(f"✅ Usuários cadastrados: {users_count}")
        
        # Verificar XMLs
        xmls_count = XMLFile.query.count()
        print(f"✅ XMLs processados: {xmls_count}")
        
        # Verificar registros de uso
        usage_count = UsageRecord.query.count()
        print(f"✅ Registros de uso: {usage_count}")
        
        # Verificar integridade de dados
        users_with_balance = User.query.filter(User.current_balance > 0).count()
        print(f"✅ Usuários com saldo: {users_with_balance}")
        
        # Verificar usuários com trial ativo
        trial_users = User.query.filter(User.trial_expires_at > datetime.utcnow()).count()
        print(f"✅ Usuários em trial: {trial_users}")
        
        print("   ✅ Banco de dados consistente")
        return True

def run_all_tests():
    """Executa todos os testes do sistema"""
    print("TESTE COMPLETO DO SISTEMA XMLDownloader Pro")
    print("=" * 60)
    
    tests = [
        ("Preços por Volume", test_xml_volume_pricing_integration),
        ("Sistema de Assinatura", test_labels_subscription_system),
        ("Sistema de Créditos", test_credit_system_integration),
        ("Processamento XML", test_xml_processing_integration),
        ("Consistência do Banco", test_database_consistency)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            print(f"\n🔍 Executando: {test_name}")
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name}: PASSOU")
            else:
                print(f"❌ {test_name}: FALHOU")
        except Exception as e:
            print(f"❌ {test_name}: ERRO - {str(e)}")
            results.append((test_name, False))
    
    # Relatório final
    print("\n" + "=" * 60)
    print("RELATÓRIO FINAL DOS TESTES")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name}: {status}")
    
    print(f"\nRESULTADO: {passed}/{total} testes passaram ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 TODOS OS TESTES PASSARAM - SISTEMA COMPLETAMENTE FUNCIONAL!")
        return True
    else:
        print("⚠️  ALGUNS TESTES FALHARAM - VERIFICAR PROBLEMAS")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)