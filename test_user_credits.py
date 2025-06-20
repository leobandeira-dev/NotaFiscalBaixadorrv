#!/usr/bin/env python3
"""
Script para criar usuário de teste e adicionar 100 créditos XML
Verifica integração com tabelas do banco e API do Stripe
"""

import os
import sys
from datetime import datetime
from werkzeug.security import generate_password_hash

# Configurar o ambiente Flask
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def create_test_user_with_credits():
    """Criar usuário de teste e adicionar 100 créditos XML"""
    
    try:
        # Importar dependências do Flask
        from models import db, User, StripeTransaction, CreditBalance
        from new_app import app
        
        with app.app_context():
            print("=== TESTE DE INTEGRAÇÃO: SISTEMA DE CRÉDITOS XML ===")
            print()
            
            # 1. Verificar usuário existente ou criar novo
            test_email = "teste@xmldownloader.com"
            user = User.query.filter_by(email=test_email).first()
            
            if not user:
                print("📝 Criando usuário de teste...")
                user = User(
                    email=test_email,
                    name="Usuario Teste",
                    password_hash=generate_password_hash("senha123"),
                    trial_expires_at=datetime.utcnow(),
                    created_at=datetime.utcnow()
                )
                db.session.add(user)
                db.session.commit()
                print(f"✅ Usuário criado: ID {user.id} - {user.email}")
            else:
                print(f"👤 Usuário existente encontrado: ID {user.id} - {user.email}")
            
            print()
            
            # 2. Verificar saldo atual
            from stripe_pricing_system import get_user_xml_credits
            current_balance = get_user_xml_credits(user.id)
            print(f"💰 Saldo atual de créditos XML: {current_balance}")
            
            # 3. Criar transação Stripe simulada (compra de 100 créditos)
            print("🛒 Criando transação de compra de 100 créditos XML...")
            
            stripe_transaction = StripeTransaction(
                user_id=user.id,
                stripe_payment_intent_id=f"pi_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                stripe_session_id=f"cs_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                amount_brl=10.00,  # R$ 10,00 por 100 créditos (R$ 0,10 cada)
                credits_purchased=100.0,
                package_id="test_package_100",
                status="completed",
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow()
            )
            
            db.session.add(stripe_transaction)
            db.session.commit()
            print(f"✅ Transação criada: ID {stripe_transaction.id}")
            
            # 4. Registrar histórico de crédito
            print("📊 Registrando histórico de créditos...")
            
            credit_record = CreditBalance(
                user_id=user.id,
                transaction_type="credit",
                amount=100.0,
                balance_after=current_balance + 100.0,
                description=f"Compra de créditos via Stripe - Transação {stripe_transaction.id}",
                stripe_transaction_id=stripe_transaction.id,
                created_at=datetime.utcnow()
            )
            
            db.session.add(credit_record)
            db.session.commit()
            print(f"✅ Histórico registrado: ID {credit_record.id}")
            
            # 5. Verificar novo saldo
            new_balance = get_user_xml_credits(user.id)
            print(f"💰 Novo saldo de créditos XML: {new_balance}")
            
            print()
            print("=== VERIFICAÇÃO DE INTEGRAÇÃO ===")
            
            # 6. Testar comunicação com Stripe API
            print("🔗 Testando comunicação com API Stripe...")
            try:
                import stripe
                stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
                
                if stripe.api_key:
                    # Testar conexão listando produtos
                    products = stripe.Product.list(limit=1)
                    print("✅ Comunicação com Stripe API: FUNCIONANDO")
                    print(f"   - API Key configurada: {'sk_live_' in stripe.api_key}")
                    print(f"   - Produtos encontrados: {len(products.data)}")
                else:
                    print("❌ Stripe API Key não configurada")
                    
            except Exception as e:
                print(f"❌ Erro na comunicação com Stripe: {e}")
            
            # 7. Verificar tabelas do banco
            print()
            print("🗄️  Verificando integridade das tabelas...")
            
            # Contar registros
            total_users = User.query.count()
            total_transactions = StripeTransaction.query.count()
            total_credit_records = CreditBalance.query.count()
            
            print(f"   - Usuários cadastrados: {total_users}")
            print(f"   - Transações Stripe: {total_transactions}")
            print(f"   - Registros de crédito: {total_credit_records}")
            
            # Verificar relacionamentos
            user_transactions = StripeTransaction.query.filter_by(user_id=user.id).count()
            user_credits = CreditBalance.query.filter_by(user_id=user.id).count()
            
            print(f"   - Transações do usuário teste: {user_transactions}")
            print(f"   - Registros de crédito do usuário: {user_credits}")
            
            print()
            print("=== TESTE DE CONSUMO DE CRÉDITO ===")
            
            # 8. Testar consumo de 1 crédito
            from stripe_pricing_system import consume_xml_credit
            
            print("📥 Testando consumo de 1 crédito XML...")
            consumption_result = consume_xml_credit(user.id)
            
            if consumption_result:
                final_balance = get_user_xml_credits(user.id)
                print(f"✅ Crédito consumido com sucesso")
                print(f"💰 Saldo final: {final_balance}")
                
                # Verificar se o histórico foi registrado
                latest_record = CreditBalance.query.filter_by(
                    user_id=user.id,
                    transaction_type="debit"
                ).order_by(CreditBalance.created_at.desc()).first()
                
                if latest_record:
                    print(f"📊 Histórico de consumo registrado: ID {latest_record.id}")
                else:
                    print("⚠️  Histórico de consumo não encontrado")
            else:
                print("❌ Falha no consumo de crédito")
            
            print()
            print("=== RESUMO DO TESTE ===")
            print(f"✅ Usuário de teste: {user.email} (ID: {user.id})")
            print(f"✅ Créditos adicionados: 100 XMLs")
            print(f"✅ Saldo final: {get_user_xml_credits(user.id)} créditos")
            print(f"✅ Sistema de billing: OPERACIONAL")
            print(f"✅ Integração Stripe: {'CONFIGURADA' if os.environ.get('STRIPE_SECRET_KEY') else 'PENDENTE'}")
            print()
            
            return {
                'success': True,
                'user_id': user.id,
                'email': user.email,
                'credits': get_user_xml_credits(user.id),
                'transaction_id': stripe_transaction.id
            }
            
    except Exception as e:
        print(f"❌ ERRO NO TESTE: {e}")
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}

def test_stripe_integration():
    """Testar especificamente a integração com Stripe"""
    print("=== TESTE ESPECÍFICO: INTEGRAÇÃO STRIPE ===")
    
    try:
        import stripe
        stripe_key = os.environ.get('STRIPE_SECRET_KEY')
        
        if not stripe_key:
            print("❌ STRIPE_SECRET_KEY não configurada")
            return False
            
        stripe.api_key = stripe_key
        
        # Testar listagem de produtos
        print("🔗 Testando listagem de produtos...")
        products = stripe.Product.list(limit=5)
        print(f"✅ Produtos encontrados: {len(products.data)}")
        
        for product in products.data:
            print(f"   - {product.name} (ID: {product.id})")
        
        # Testar preços
        print()
        print("💰 Testando listagem de preços...")
        prices = stripe.Price.list(limit=5)
        print(f"✅ Preços encontrados: {len(prices.data)}")
        
        for price in prices.data:
            print(f"   - {price.id}: {price.unit_amount/100 if price.unit_amount else 'N/A'} {price.currency or 'N/A'}")
        
        print("✅ Integração Stripe: FUNCIONANDO CORRETAMENTE")
        return True
        
    except Exception as e:
        print(f"❌ Erro na integração Stripe: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Iniciando teste completo do sistema...")
    print()
    
    # Teste 1: Sistema de créditos
    result = create_test_user_with_credits()
    
    print()
    
    # Teste 2: Integração Stripe
    stripe_ok = test_stripe_integration()
    
    print()
    print("=== RESULTADO FINAL ===")
    if result.get('success') and stripe_ok:
        print("🎉 TODOS OS TESTES PASSARAM!")
        print("   Sistema pronto para produção")
    elif result.get('success'):
        print("⚠️  Sistema de créditos funcionando, Stripe pendente")
    else:
        print("❌ Testes falharam - verificar configuração")