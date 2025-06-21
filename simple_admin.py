"""
Painel Admin Simplificado
Rota temporária para listar usuários cadastrados
"""

from flask import render_template_string
from new_app import app, db
from models import User, XMLFile, CreditBalance
from sqlalchemy import func

@app.route('/admin-simples')
def admin_simples():
    """Lista simples de usuários cadastrados"""
    
    # Buscar todos os usuários
    users = User.query.order_by(User.created_at.desc()).all()
    
    # Para cada usuário, calcular dados reais
    users_data = []
    for user in users:
        # Contar XMLs
        total_xmls = XMLFile.query.filter_by(user_id=user.id).count()
        
        # Calcular saldo de créditos
        credits_query = db.session.query(func.sum(
            CreditBalance.amount * (
                1 if CreditBalance.transaction_type == 'credit' else -1
            )
        )).filter_by(user_id=user.id)
        credit_balance = credits_query.scalar() or 0
        
        users_data.append({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'created_at': user.created_at,
            'total_xmls': total_xmls,
            'credit_balance': credit_balance
        })
    
    # Template HTML simples
    template = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin - Usuários Cadastrados</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            table { border-collapse: collapse; width: 100%; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background-color: #f2f2f2; }
            .header { background-color: #4CAF50; color: white; padding: 10px; margin-bottom: 20px; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Usuários Cadastrados no Sistema</h1>
            <p>Total de usuários: {{ users_data|length }}</p>
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>ID</th>
                    <th>Nome</th>
                    <th>Email</th>
                    <th>XMLs Baixados</th>
                    <th>Créditos XML</th>
                    <th>Data Cadastro</th>
                </tr>
            </thead>
            <tbody>
                {% for user in users_data %}
                <tr>
                    <td>{{ user.id }}</td>
                    <td>{{ user.name }}</td>
                    <td>{{ user.email }}</td>
                    <td>{{ user.total_xmls }}</td>
                    <td>{{ user.credit_balance }}</td>
                    <td>{{ user.created_at.strftime('%d/%m/%Y %H:%M') }}</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>
        
        <div style="margin-top: 20px;">
            <a href="/dashboard" style="background-color: #008CBA; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px;">
                Voltar ao Dashboard
            </a>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(template, users_data=users_data)