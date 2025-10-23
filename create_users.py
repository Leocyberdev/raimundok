import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from models.user import db, User
from main import app

with app.app_context():
    # Verificar usuários existentes
    users = User.query.all()
    print(f"Usuários existentes: {len(users)}")
    for user in users:
        print(f"  - {user.username} ({user.user_type})")
    
    # Criar usuários se não existirem
    if not User.query.filter_by(username='Nonato').first():
        admin1 = User(username='Nonato', user_type='admin')
        admin1.set_password('123456')
        db.session.add(admin1)
        print("Criando usuário Nonato...")
    
    if not User.query.filter_by(username='Gleissa').first():
        admin2 = User(username='Gleissa', user_type='admin')
        admin2.set_password('123456')
        db.session.add(admin2)
        print("Criando usuário Gleissa...")
    
    db.session.commit()
    print("\nUsuários criados com sucesso!")
    
    # Verificar novamente
    users = User.query.all()
    print(f"\nTotal de usuários: {len(users)}")
    for user in users:
        print(f"  - {user.username} ({user.user_type})")
