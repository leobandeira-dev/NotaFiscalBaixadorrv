#!/usr/bin/env python3
"""
Test script para verificar o sistema de preços por volume e módulo de etiquetas
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from stripe_integration import PricingManager
from models import User, db
from new_app import app

def test_volume_pricing():
    """Testa o sistema de preços por volume para XMLs"""
    print("=== TESTE DE PREÇOS POR VOLUME ===")
    
    # Testar diferentes quantidades
    test_quantities = [1, 100, 500, 750, 1000, 1500, 2000, 3000]
    
    for qty in test_quantities:
        price_per_unit = PricingManager.get_xml_price_by_volume(qty)
        total_cost = PricingManager.calculate_total_xml_cost(qty)
        
        print(f"\nQuantidade: {qty} XMLs")
        print(f"  Preço unitário: R$ {price_per_unit:.3f}")
        print(f"  Custo total: R$ {total_cost['total_cost']:.2f}")
        print(f"  Preço médio: R$ {total_cost['average_price']:.3f}")
        
        # Mostrar breakdown detalhado
        for breakdown in total_cost['breakdown']:
            print(f"    Faixa {breakdown['range']}: {breakdown['quantity']} XMLs × R$ {breakdown['price_per_unit']:.3f} = R$ {breakdown['subtotal']:.2f}")

def test_labels_subscription():
    """Testa o sistema de assinatura do módulo de etiquetas"""
    print("\n=== TESTE DE ASSINATURA DE ETIQUETAS ===")
    
    with app.app_context():
        # Buscar usuário de teste
        test_user = User.query.filter_by(email='admin@xmldownloader.com').first()
        
        if not test_user:
            print("❌ Usuário de teste não encontrado")
            return
        
        print(f"Usuário: {test_user.name} ({test_user.email})")
        print(f"  Trial de etiquetas ativo: {test_user.is_labels_trial_active()}")
        print(f"  Assinatura ativa: {test_user.labels_subscription_active}")
        print(f"  Tem acesso às etiquetas: {test_user.has_labels_access()}")
        
        if test_user.labels_trial_expires_at:
            print(f"  Trial expira em: {test_user.labels_trial_expires_at}")
        
        if test_user.labels_subscription_expires_at:
            print(f"  Assinatura expira em: {test_user.labels_subscription_expires_at}")

def test_credit_packages():
    """Testa os pacotes de créditos disponíveis"""
    print("\n=== TESTE DE PACOTES DE CRÉDITOS ===")
    
    for package_id, package in PricingManager.CREDIT_PACKAGES.items():
        print(f"\nPacote: {package['name']}")
        print(f"  Créditos: R$ {package['credits']:.2f}")
        print(f"  Preço: R$ {package['price_brl']/100:.2f}")
        print(f"  Descrição: {package['description']}")
        
        # Calcular economia
        savings = PricingManager.calculate_xml_package_savings(package_id)
        if savings:
            print(f"  XMLs estimados: {savings['xml_count']}")
            print(f"  Economia: {savings['savings_percent']:.1f}%")

def test_pricing_consistency():
    """Verifica consistência dos preços"""
    print("\n=== TESTE DE CONSISTÊNCIA ===")
    
    # Verificar se preços estão consistentes
    xml_price = PricingManager.PRICES['xml_download']
    labels_price = PricingManager.PRICES['labels_module']
    
    print(f"Preço base XML: R$ {xml_price:.3f}")
    print(f"Preço módulo etiquetas: R$ {labels_price:.2f}/mês")
    
    # Verificar faixas de volume
    print("\nFaixas de volume configuradas:")
    for (min_qty, max_qty), price in sorted(PricingManager.XML_VOLUME_PRICING.items()):
        max_display = "∞" if max_qty == float('inf') else str(max_qty)
        print(f"  {min_qty}-{max_display}: R$ {price:.3f} por XML")
    
    # Verificar produtos Stripe
    print(f"\nProdutos Stripe:")
    for service, product_id in PricingManager.STRIPE_PRODUCTS.items():
        print(f"  {service}: {product_id}")

if __name__ == "__main__":
    print("TESTE DO SISTEMA DE PREÇOS E ASSINATURAS")
    print("=" * 50)
    
    try:
        test_volume_pricing()
        test_labels_subscription()
        test_credit_packages()
        test_pricing_consistency()
        
        print("\n" + "=" * 50)
        print("✅ TODOS OS TESTES CONCLUÍDOS")
        
    except Exception as e:
        print(f"\n❌ ERRO DURANTE OS TESTES: {str(e)}")
        import traceback
        traceback.print_exc()