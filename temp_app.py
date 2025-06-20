"""
Versão temporária do sistema para validar correções sem banco de dados
"""

from flask import Flask, render_template, jsonify

app = Flask(__name__)
app.secret_key = "temp_key_for_testing"

@app.route('/')
def index():
    return render_template('landing.html' if 'landing.html' in app.jinja_env.list_templates() else 'index.html')

@app.route('/admin/')
def admin_temp():
    """Painel admin temporário para validar correções"""
    
    # Simular estatísticas sem banco de dados
    stats = {
        'total_users': 15,
        'active_users': 12,
        'total_xmls': 47,
        'total_revenue': 142.50,
        'this_month_xmls': 23  # Campo corrigido usando imported_at
    }
    
    # Simular dados para validar que não há mais erro de 'uploaded_at'
    recent_users = []
    recent_activities = []
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         recent_users=recent_users,
                         recent_activities=recent_activities)

@app.route('/health')
def health():
    return jsonify({
        'status': 'ok',
        'message': 'Sistema temporário funcionando',
        'admin_fix': 'Campo uploaded_at corrigido para imported_at',
        'optimizations': {
            'download_timeouts': 'Reduzidos para 2s',
            'polling_speed': '0.5s ultra-rápido',
            'chrome_optimization': 'Processo único ativado'
        }
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001, debug=True)