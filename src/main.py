import os
import sys

# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory, redirect, url_for
from flask_login import LoginManager
from src.models.user import db, User, AuditLog, FileReference
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.admin import admin_bp
from src.routes.employee import employee_bp
from src.database.config import get_database_config, is_production
from datetime import date
from pytz import timezone
import pytz
from datetime import datetime



# =====================
# Configuração do Flask
# =====================
app = Flask(
    __name__,
    static_folder=os.path.join(os.path.dirname(__file__), 'static'),
    template_folder=os.path.join(os.path.dirname(__file__), 'templates')
)

# ===================================================================
# FILTROS GLOBAIS PARA TEMPLATES (JINJA2)
# ===================================================================
# Importa a função de utilidade que já criamos
from src.utils.date_utils import format_date_pt, format_bytes

@app.template_filter("format_bytes")
def format_bytes_filter(value):
    return format_bytes(value)

@app.template_filter('format_date')
def format_date_filter(value):
    """
    Formata uma data como dd/mm/YYYY.
    Uso no template: {{ minha_data | format_date }}
    """
    if not value:
        return ""
    # Usa a função de utilidade que já lida com date e datetime
    return format_date_pt(value, format_type='full')


# Definição corrigida
@app.template_filter('format_datetime')
def format_datetime_filter(value, format=None):
    """
    Formata data e hora. Aceita um formato customizado.
    Uso: {{ meu_datetime | format_datetime }}
         {{ meu_datetime | format_datetime("%H:%M") }}
    """
    if not value:
        return ""

    # Se nenhum formato for passado, usa o padrão.
    if format is None:
        if isinstance(value, datetime):
            format = '%d/%m/%Y %H:%M'
        else:
            format = '%d/%m/%Y'

    # Tenta formatar com o formato especificado (ou o padrão)
    try:
        return value.strftime(format)
    except (ValueError, AttributeError):
        # Se falhar, retorna o valor original como string
        return str(value)


# Criamos um "apelido" para o filtro que o seu template `service_order_detail.html` estava pedindo.
# Ambos 'format_date' e 'format_date_sp' agora funcionarão e farão a mesma coisa.
app.jinja_env.filters['format_date_sp'] = app.jinja_env.filters['format_date']
# ===================================================================




app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'sistema-pedidos-secret-key-2025')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')

# Configuração dinâmica do banco de dados
db_config = get_database_config()
app.config.update(db_config)

# =====================
# Variáveis globais no template
# =====================
@app.context_processor
def inject_date():
    from datetime import datetime, timedelta
    return {
        'date': date,
        'now': datetime.now(),
        'timedelta': timedelta,
        'timezone': pytz.timezone
    }


# =====================
# Configuração do Login
# =====================
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor, faça login para acessar esta página.'
login_manager.login_message_category = 'info'

# Filtros Jinja2 personalizados
# =====================
@app.template_filter('format_datetime_br')
def format_datetime_br(value, format='%d/%m/%Y às %H:%M'):
    """Formatar datetime para padrão brasileiro"""
    if value is None:
        return ''

    if hasattr(value, 'astimezone'):
        # Se tem timezone, converter para America/Sao_Paulo
        br_tz = pytz.timezone('America/Sao_Paulo')
        if value.tzinfo is None:
            value = br_tz.localize(value)
        else:
            value = value.astimezone(br_tz)

    return value.strftime(format)

@app.template_filter('format_datetime')
def format_datetime(value, format='%d/%m/%Y às %H:%M'):
    """Formatar datetime padrão"""
    if value is None:
        return ''

    if hasattr(value, 'astimezone'):
        # Se tem timezone, converter para America/Sao_Paulo
        br_tz = pytz.timezone('America/Sao_Paulo')
        if value.tzinfo is None:
            value = br_tz.localize(value)
        else:
            value = value.astimezone(br_tz)

    return value.strftime(format)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# =====================
# Registrar Blueprints
# =====================
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/')
app.register_blueprint(employee_bp, url_prefix='/')


# =====================
# Banco de dados
# =====================
db.init_app(app)
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

with app.app_context():
    try:
        # Verificar se precisa migrar (adicionar colunas novas)
        try:
            from sqlalchemy import text, inspect
            inspector = inspect(db.engine)

            # Migrar coluna is_urgent
            if 'is_urgent' not in [col['name'] for col in inspector.get_columns('order')]:
                print("Adicionando coluna is_urgent...")
                db.session.execute(text('ALTER TABLE "order" ADD COLUMN is_urgent BOOLEAN DEFAULT FALSE'))
                db.session.commit()
                print("Coluna is_urgent adicionada com sucesso!")

            # Migrar coluna subtitle
            if 'subtitle' not in [col['name'] for col in inspector.get_columns('order')]:
                print("Adicionando coluna subtitle...")
                db.session.execute(text('ALTER TABLE "order" ADD COLUMN subtitle VARCHAR(300)'))
                db.session.commit()
                print("Coluna subtitle adicionada com sucesso!")

            # Migrar coluna description
            if 'description' not in [col['name'] for col in inspector.get_columns('order')]:
                print("Adicionando coluna description...")
                db.session.execute(text('ALTER TABLE "order" ADD COLUMN description TEXT'))
                db.session.commit()
                print("Coluna description adicionada com sucesso!")

        except Exception as e:
            print(f"Erro ao verificar/adicionar colunas da tabela 'order': {e}")

        # Migração automática
        try:
            # Verificar e adicionar colunas se necessário
            with app.app_context():
                inspector = inspect(db.engine)

                # Verificar tabela service_order
                if 'service_order' in inspector.get_table_names():
                    columns = [col['name'] for col in inspector.get_columns('service_order')]

                    # Adicionar colunas de arquivo se não existirem
                    with db.engine.connect() as conn:
                        if 'file1_filename' not in columns:
                            conn.execute(text('ALTER TABLE service_order ADD COLUMN file1_filename VARCHAR(200)'))
                            conn.commit()
                        if 'file2_filename' not in columns:
                            conn.execute(text('ALTER TABLE service_order ADD COLUMN file2_filename VARCHAR(200)'))
                            conn.commit()
                        if 'file3_filename' not in columns:
                            conn.execute(text('ALTER TABLE service_order ADD COLUMN file3_filename VARCHAR(200)'))
                            conn.commit()

                    print("Colunas de arquivo verificadas/adicionadas com sucesso!")
        except Exception as e:
            print(f"Erro ao verificar/adicionar colunas: {e}")
            # Continuar mesmo com erro de migração

        db.create_all()

        # Criar tabelas para AuditLog e FileReference se não existirem
        if 'audit_log' not in inspector.get_table_names():
            print("Criando tabela audit_log...")
            AuditLog.__table__.create(db.engine)
            print("Tabela audit_log criada com sucesso!")

        if 'file_reference' not in inspector.get_table_names():
            print("Criando tabela file_reference...")
            FileReference.__table__.create(db.engine)
            print("Tabela file_reference criada com sucesso!")

        # Criar usuários admin padrão se não existirem
        try:
            if not User.query.filter_by(username='Nonato').first():
                admin1 = User(username='Nonato', user_type='admin')
                admin1.set_password('123456')
                db.session.add(admin1)

            if not User.query.filter_by(username='Gleissa').first():
                admin2 = User(username='Gleissa', user_type='admin')
                admin2.set_password('123456')
                db.session.add(admin2)
        except Exception as e:
            print(f"Erro ao criar usuário: {e}")
            db.session.rollback()

        db.session.commit()
        print(f"Banco de dados inicializado com sucesso! Ambiente: {'Produção (PostgreSQL)' if is_production() else 'Desenvolvimento (SQLite)'}")

    except Exception as e:
        print(f"Erro ao inicializar banco de dados: {e}")
        db.session.rollback()


# =====================
# Rotas estáticas
# =====================
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path == '':
        return redirect(url_for('auth.login'))

    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404


# =====================
# Iniciar servidor
# =====================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))  # Use port 8080 as default
    debug = not is_production()
    app.run(host='0.0.0.0', port=port, debug=debug)

import locale

try:
    # Tenta usar o locale em português do Brasil
    locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
except locale.Error:
    # Se não estiver disponível (ex.: Render), usa C.UTF-8
    locale.setlocale(locale.LC_ALL, 'C.UTF-8')