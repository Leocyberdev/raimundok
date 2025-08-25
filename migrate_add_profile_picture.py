
#!/usr/bin/env python3
"""
Script para adicionar a coluna profile_picture na tabela User
Execute este script uma vez para atualizar o banco de dados existente
"""

import sys
import os

# Adicionar o diretório src ao path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.main import app
from src.models.user import db
from sqlalchemy import text

def migrate_database():
    with app.app_context():
        try:
            # Verificar se a coluna já existe
            result = db.session.execute(text("PRAGMA table_info(user)")).fetchall()
            columns = [row[1] for row in result]
            
            if 'profile_picture' not in columns:
                print("Adicionando coluna profile_picture à tabela user...")
                
                # Adicionar a coluna profile_picture
                db.session.execute(text('ALTER TABLE user ADD COLUMN profile_picture VARCHAR(200)'))
                db.session.commit()
                
                print("✅ Coluna profile_picture adicionada com sucesso!")
            else:
                print("ℹ️  Coluna profile_picture já existe na tabela user.")
                
        except Exception as e:
            print(f"❌ Erro ao migrar banco de dados: {e}")
            db.session.rollback()
            sys.exit(1)

if __name__ == '__main__':
    print("🔄 Iniciando migração do banco de dados...")
    migrate_database()
    print("✅ Migração concluída!")
