#!/usr/bin/env python3
import os
import sys

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from src.models.user import User, db
from src.main import app

def create_admin():
    with app.app_context():
        # Verificar se admin já existe
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', user_type='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('Usuário admin criado com sucesso! Login: admin, Senha: admin123')
        else:
            print('Usuário admin já existe')
            # Atualizar senha
            admin.set_password('admin123')
            db.session.commit()
            print('Senha do admin atualizada para admin123')

if __name__ == '__main__':
    create_admin()

