"""
Teste de segurança do sistema Google OAuth
Valida todas as verificações de segurança implementadas
"""

import os
import sys
from datetime import datetime, timedelta

# Configurar path para importar módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from models import User, db
from new_app import app

def test_oauth_security():
    """Testa todas as verificações de segurança OAuth"""
    
    with app.app_context():
        print("🔐 TESTE DE SEGURANÇA GOOGLE OAUTH")
        print("=" * 50)
        
        # Limpar dados de teste
        test_users = User.query.filter(User.email.like('%test%')).all()
        for user in test_users:
            db.session.delete(user)
        db.session.commit()
        
        print("✅ Dados de teste limpos")
        
        # Teste 1: Criar usuário com Google ID único
        print("\n1. Testando criação de usuário com Google ID...")
        user1 = User()
        user1.email = "test1@exemplo.com"
        user1.name = "Usuário Teste 1"
        user1.provider = 'google'
        user1.google_user_id = "google_123456789"
        user1.trial_start_date = datetime.utcnow()
        user1.trial_end_date = datetime.utcnow() + timedelta(days=7)
        user1.active = True
        
        db.session.add(user1)
        db.session.commit()
        print(f"✅ Usuário criado com ID: {user1.id}, Google ID: {user1.google_user_id}")
        
        # Teste 2: Verificar que Google ID é único
        print("\n2. Testando unicidade do Google ID...")
        try:
            user2 = User()
            user2.email = "test2@exemplo.com"
            user2.name = "Usuário Teste 2"
            user2.provider = 'google'
            user2.google_user_id = "google_123456789"  # Mesmo Google ID
            user2.trial_start_date = datetime.utcnow()
            user2.trial_end_date = datetime.utcnow() + timedelta(days=7)
            user2.active = True
            
            db.session.add(user2)
            db.session.commit()
            print("❌ ERRO: Google ID duplicado foi aceito!")
        except Exception as e:
            print("✅ Unicidade do Google ID protegida corretamente")
            db.session.rollback()
        
        # Teste 3: Verificar busca por Google ID
        print("\n3. Testando busca por Google ID...")
        found_user = User.query.filter_by(google_user_id="google_123456789").first()
        if found_user and found_user.id == user1.id:
            print("✅ Busca por Google ID funcionando")
        else:
            print("❌ Erro na busca por Google ID")
        
        # Teste 4: Criar usuário com email mas sem Google ID
        print("\n4. Testando usuário local (sem Google ID)...")
        user3 = User()
        user3.email = "test3@exemplo.com"
        user3.name = "Usuário Local"
        user3.provider = 'local'
        user3.password_hash = "hash_senha_local"
        user3.trial_start_date = datetime.utcnow()
        user3.trial_end_date = datetime.utcnow() + timedelta(days=7)
        user3.active = True
        
        db.session.add(user3)
        db.session.commit()
        print(f"✅ Usuário local criado com ID: {user3.id}")
        
        # Teste 5: Verificar busca combinada
        print("\n5. Testando buscas combinadas...")
        
        # Buscar por Google ID existente
        google_user = User.query.filter_by(google_user_id="google_123456789").first()
        print(f"✅ Busca Google ID: Usuário {google_user.id if google_user else 'não encontrado'}")
        
        # Buscar por email do usuário Google
        email_user = User.query.filter_by(email="test1@exemplo.com").first()
        print(f"✅ Busca email Google: Usuário {email_user.id if email_user else 'não encontrado'}")
        
        # Buscar por email do usuário local
        local_user = User.query.filter_by(email="test3@exemplo.com").first()
        print(f"✅ Busca email local: Usuário {local_user.id if local_user else 'não encontrado'}")
        
        # Teste 6: Simular cenários de conflito
        print("\n6. Testando detecção de conflitos...")
        
        # Cenário: mesmo Google ID com emails diferentes (deve ser impossível devido à constraint)
        # Cenário: mesmo email com Google IDs diferentes (deve ser detectado na lógica)
        
        user_by_google = User.query.filter_by(google_user_id="google_123456789").first()
        user_by_email = User.query.filter_by(email="test1@exemplo.com").first()
        
        if user_by_google and user_by_email and user_by_google.id == user_by_email.id:
            print("✅ Consistência: Google ID e email pertencem ao mesmo usuário")
        else:
            print("❌ Inconsistência detectada!")
        
        # Teste 7: Verificar campos obrigatórios
        print("\n7. Verificando estrutura de campos...")
        
        fields_to_check = ['google_user_id', 'provider', 'email', 'name', 'active']
        
        for field in fields_to_check:
            if hasattr(User, field):
                print(f"✅ Campo {field} existe")
            else:
                print(f"❌ Campo {field} não encontrado")
        
        # Teste 8: Verificar índices e constraints
        print("\n8. Testando constraints do banco...")
        
        # Verificar se a coluna google_user_id foi criada
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        
        if 'google_user_id' in columns:
            print("✅ Coluna google_user_id existe na tabela")
        else:
            print("❌ Coluna google_user_id não encontrada")
        
        # Limpar dados de teste
        print("\n9. Limpeza final...")
        test_users = User.query.filter(User.email.like('%test%')).all()
        for user in test_users:
            db.session.delete(user)
        db.session.commit()
        print("✅ Dados de teste removidos")
        
        print("\n" + "=" * 50)
        print("🎉 TESTE DE SEGURANÇA CONCLUÍDO")
        print("=" * 50)

if __name__ == "__main__":
    test_oauth_security()