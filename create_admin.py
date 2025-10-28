
#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user import User, db
from main import app
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

def create_admin_users():
    """Criar ou atualizar usuários administradores"""
    with app.app_context():
        try:
            # Lista de usuários para criar/atualizar
            users_data = [
                {'username': 'Nonato', 'password': '123456'},
                {'username': 'Gleissa', 'password': '123456'},
                {'username': 'admin', 'password': 'admin123'}
            ]
            
            for user_data in users_data:
                username = user_data['username']
                password = user_data['password']
                
                # Verificar se usuário já existe
                existing_user = User.query.filter_by(username=username).first()
                
                if existing_user:
                    print(f"Usuário '{username}' já existe. Atualizando senha...")
                    # Usar método mais simples para hash
                    existing_user.password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
                    existing_user.is_active = True
                    print(f"Senha do usuário '{username}' atualizada.")
                else:
                    # Criar novo usuário
                    new_user = User(
                        username=username,
                        user_type='admin',
                        is_active=True
                    )
                    # Usar método mais simples para hash
                    new_user.password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
                    db.session.add(new_user)
                    print(f"Usuário '{username}' criado com sucesso.")
            
            db.session.commit()
            print("\n✅ Todos os usuários foram processados com sucesso!")
            print("\nUsuários disponíveis:")
            for user_data in users_data:
                print(f"- Username: {user_data['username']}, Password: {user_data['password']}")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erro ao processar usuários: {e}")
            print("Tentando com hash ainda mais simples...")
            
            # Tentar com hash mais simples
            try:
                for user_data in users_data:
                    username = user_data['username']
                    password = user_data['password']
                    
                    existing_user = User.query.filter_by(username=username).first()
                    if existing_user:
                        # Hash mais simples
                        existing_user.password_hash = generate_password_hash(password, method='pbkdf2:sha1', salt_length=4)
                        existing_user.is_active = True
                        print(f"Usuário '{username}' atualizado com hash simples.")
                
                db.session.commit()
                print("✅ Usuários atualizados com hash mais simples!")
                
            except Exception as e2:
                db.session.rollback()
                print(f"❌ Erro mesmo com hash simples: {e2}")

if __name__ == "__main__":
    create_admin_users()
