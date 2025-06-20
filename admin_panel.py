"""
Painel de Administração
Sistema completo para gerenciar clientes, faturas, módulos e configurações
"""

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from functools import wraps

logger = logging.getLogger(__name__)

# Blueprint para rotas administrativas
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator para verificar se usuário é admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # TODO: Implementar verificação real de admin
        # Por enquanto, simular admin logado
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@admin_required
def dashboard():
    """Dashboard principal do admin"""
    from models import User, XMLFile, UsageRecord, Charge, ServiceModule
    
    # Estatísticas gerais
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(active=True).count(),
        'total_xmls': XMLFile.query.count(),
        'total_revenue': 0,  # Calcular baseado em cobranças
        'this_month_xmls': XMLFile.query.filter(
            XMLFile.uploaded_at >= datetime.now().replace(day=1)
        ).count()
    }
    
    # Receita total
    charges = Charge.query.filter_by(status='RECEIVED').all()
    stats['total_revenue'] = sum(charge.amount for charge in charges)
    
    # Usuários recentes
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Atividade recente
    recent_usage = UsageRecord.query.order_by(UsageRecord.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         recent_users=recent_users,
                         recent_usage=recent_usage)

@admin_bp.route('/users')
@admin_required
def users():
    """Gerenciar usuários"""
    from models import User
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    
    query = User.query
    
    if search:
        query = query.filter(
            User.name.contains(search) | 
            User.email.contains(search)
        )
    
    users = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/users.html', users=users, search=search)

@admin_bp.route('/users/<int:user_id>')
@admin_required
def user_detail(user_id):
    """Detalhes de um usuário específico"""
    from models import User, XMLFile, UsageRecord, Charge
    
    user = User.query.get_or_404(user_id)
    
    # Estatísticas do usuário
    user_stats = {
        'total_xmls': XMLFile.query.filter_by(user_id=user_id).count(),
        'total_usage': UsageRecord.query.filter_by(user_id=user_id).count(),
        'total_charges': Charge.query.filter_by(user_id=user_id).count(),
        'total_spent': sum(
            usage.cost for usage in UsageRecord.query.filter_by(user_id=user_id).all()
        )
    }
    
    # Atividade recente
    recent_xmls = XMLFile.query.filter_by(user_id=user_id).order_by(
        XMLFile.uploaded_at.desc()
    ).limit(10).all()
    
    recent_charges = Charge.query.filter_by(user_id=user_id).order_by(
        Charge.created_at.desc()
    ).limit(5).all()
    
    return render_template('admin/user_detail.html',
                         user=user,
                         user_stats=user_stats,
                         recent_xmls=recent_xmls,
                         recent_charges=recent_charges)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Editar usuário"""
    from models import db, User
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        try:
            user.name = request.form.get('name')
            user.email = request.form.get('email')
            user.current_balance = float(request.form.get('current_balance', 0))
            user.active = request.form.get('active') == 'on'
            user.is_admin = request.form.get('is_admin') == 'on'
            
            # Atualizar trial se especificado
            trial_days = request.form.get('trial_days')
            if trial_days:
                trial_days = int(trial_days)
                user.trial_expires_at = datetime.utcnow() + timedelta(days=trial_days)
            
            db.session.commit()
            flash('Usuário atualizado com sucesso!', 'success')
            return redirect(url_for('admin.user_detail', user_id=user_id))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar usuário: {str(e)}', 'error')
    
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/modules')
@admin_required
def modules():
    """Gerenciar módulos de serviço"""
    from models import ServiceModule
    
    modules = ServiceModule.query.all()
    return render_template('admin/modules.html', modules=modules)

@admin_bp.route('/modules/create', methods=['GET', 'POST'])
@admin_required
def create_module():
    """Criar novo módulo"""
    from models import db, ServiceModule
    
    if request.method == 'POST':
        try:
            module = ServiceModule(
                name=request.form.get('name'),
                description=request.form.get('description'),
                cost_per_use=float(request.form.get('cost_per_use', 0)),
                is_active=request.form.get('is_active') == 'on'
            )
            
            db.session.add(module)
            db.session.commit()
            
            flash('Módulo criado com sucesso!', 'success')
            return redirect(url_for('admin.modules'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao criar módulo: {str(e)}', 'error')
    
    return render_template('admin/create_module.html')

@admin_bp.route('/modules/<int:module_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_module(module_id):
    """Editar módulo"""
    from models import db, ServiceModule
    
    module = ServiceModule.query.get_or_404(module_id)
    
    if request.method == 'POST':
        try:
            module.name = request.form.get('name')
            module.description = request.form.get('description')
            module.cost_per_use = float(request.form.get('cost_per_use', 0))
            module.is_active = request.form.get('is_active') == 'on'
            
            db.session.commit()
            flash('Módulo atualizado com sucesso!', 'success')
            return redirect(url_for('admin.modules'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao atualizar módulo: {str(e)}', 'error')
    
    return render_template('admin/edit_module.html', module=module)

@admin_bp.route('/charges')
@admin_required
def charges():
    """Gerenciar cobranças"""
    from models import Charge, User
    
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '')
    
    query = Charge.query.join(User)
    
    if status:
        query = query.filter(Charge.status == status)
    
    charges = query.order_by(Charge.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('admin/charges.html', charges=charges, status=status)

@admin_bp.route('/usage')
@admin_required
def usage():
    """Relatórios de uso"""
    from models import UsageRecord, User, ServiceModule
    
    page = request.args.get('page', 1, type=int)
    module_id = request.args.get('module_id', type=int)
    
    query = UsageRecord.query.join(User).join(ServiceModule)
    
    if module_id:
        query = query.filter(UsageRecord.module_id == module_id)
    
    usage_records = query.order_by(UsageRecord.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Estatísticas de uso
    from models import ServiceModule
    modules = ServiceModule.query.all()
    
    usage_stats = {}
    for module in modules:
        stats = {
            'total_uses': UsageRecord.query.filter_by(module_id=module.id).count(),
            'total_revenue': sum(
                usage.cost for usage in UsageRecord.query.filter_by(module_id=module.id).all()
            ),
            'unique_users': len(set(
                usage.user_id for usage in UsageRecord.query.filter_by(module_id=module.id).all()
            ))
        }
        usage_stats[module.name] = stats
    
    return render_template('admin/usage.html', 
                         usage_records=usage_records,
                         modules=modules,
                         usage_stats=usage_stats,
                         selected_module=module_id)

@admin_bp.route('/settings')
@admin_required
def settings():
    """Configurações do sistema"""
    from models import SystemSettings
    
    settings = SystemSettings.query.all()
    return render_template('admin/settings.html', settings=settings)

@admin_bp.route('/settings/update', methods=['POST'])
@admin_required
def update_settings():
    """Atualizar configurações"""
    from models import db, SystemSettings
    
    try:
        for key, value in request.form.items():
            if key.startswith('setting_'):
                setting_key = key.replace('setting_', '')
                SystemSettings.set_setting(setting_key, value)
        
        db.session.commit()
        flash('Configurações atualizadas com sucesso!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar configurações: {str(e)}', 'error')
    
    return redirect(url_for('admin.settings'))

@admin_bp.route('/api/stats')
@admin_required
def api_stats():
    """API para estatísticas em tempo real"""
    from models import User, XMLFile, UsageRecord, Charge
    
    # Estatísticas dos últimos 30 dias
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    stats = {
        'users_this_month': User.query.filter(User.created_at >= thirty_days_ago).count(),
        'xmls_this_month': XMLFile.query.filter(XMLFile.uploaded_at >= thirty_days_ago).count(),
        'revenue_this_month': sum(
            charge.amount for charge in Charge.query.filter(
                Charge.created_at >= thirty_days_ago,
                Charge.status == 'RECEIVED'
            ).all()
        ),
        'active_users': User.query.filter_by(active=True).count(),
        'total_users': User.query.count()
    }
    
    return jsonify(stats)

@admin_bp.route('/api/users/<int:user_id>/balance', methods=['POST'])
@admin_required
def update_user_balance(user_id):
    """Atualizar saldo do usuário via API"""
    from models import db, User
    
    try:
        user = User.query.get_or_404(user_id)
        action = request.json.get('action')  # 'add' or 'set'
        amount = float(request.json.get('amount', 0))
        
        if action == 'add':
            user.add_balance(amount)
        elif action == 'set':
            user.current_balance = amount
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'new_balance': user.current_balance
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400

def init_default_modules():
    """Inicializar módulos padrão do sistema"""
    from models import db, ServiceModule
    
    default_modules = [
        {
            'name': 'Download XML',
            'description': 'Download automatizado de XMLs de notas fiscais',
            'cost_per_use': 0.10,
            'is_active': True
        },
        {
            'name': 'Geração DANFE',
            'description': 'Geração de DANFE em PDF a partir do XML',
            'cost_per_use': 0.00,  # Gratuito
            'is_active': True
        },
        {
            'name': 'Etiquetas de Transporte',
            'description': 'Geração de etiquetas de transporte personalizadas',
            'cost_per_use': 49.90,  # Taxa única
            'is_active': True
        },
        {
            'name': 'API Access',
            'description': 'Acesso via API REST para automação',
            'cost_per_use': 0.10,  # Mesmo valor do download web
            'is_active': True
        }
    ]
    
    for module_data in default_modules:
        existing = ServiceModule.query.filter_by(name=module_data['name']).first()
        if not existing:
            module = ServiceModule(**module_data)
            db.session.add(module)
    
    try:
        db.session.commit()
        logger.info("Módulos padrão inicializados")
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao inicializar módulos: {str(e)}")

def init_admin_panel(app):
    """Inicializar painel administrativo"""
    app.register_blueprint(admin_bp)
    
    # Inicializar dados padrão
    with app.app_context():
        init_default_modules()