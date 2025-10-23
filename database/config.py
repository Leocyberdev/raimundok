import os
from urllib.parse import urlparse

def get_database_config():
    """
    Retorna a configuração do banco de dados baseada no ambiente.
    SQLite para desenvolvimento local e PostgreSQL para produção (Render).
    """
    # Verifica se está rodando no Render (variável de ambiente DATABASE_URL)
    database_url = os.environ.get('DATABASE_URL')
    
    if database_url:
        # Produção - PostgreSQL no Render
        # O Render fornece a URL no formato postgres://, mas SQLAlchemy 1.4+ requer postgresql://
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        return {
            'SQLALCHEMY_DATABASE_URI': database_url,
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SQLALCHEMY_ENGINE_OPTIONS': {
                'pool_pre_ping': True,
                'pool_recycle': 300,
            }
        }
    else:
        # Desenvolvimento local - SQLite
        base_dir = os.path.dirname(os.path.dirname(__file__))
        db_path = os.path.join(base_dir, 'database', 'app.db')
        
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        return {
            'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
            'SQLALCHEMY_TRACK_MODIFICATIONS': False
        }

def is_production():
    """Verifica se está rodando em produção (Render)."""
    return os.environ.get('DATABASE_URL') is not None

