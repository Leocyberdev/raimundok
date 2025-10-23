from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from models.user import User, db

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    # Se já estiver autenticado, redirecionar
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        else:
            return redirect(url_for('employee.dashboard'))
    
    if request.method == 'POST':
        if request.is_json:
            # API request
            data = request.get_json()
            username = data.get('username')
            password = data.get('password')
        else:
            # Form request
            username = request.form.get('username')
            password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            # Fazer login com remember=True para manter a sessão
            session.permanent = True
            login_user(user, remember=True)
            
            if request.is_json:
                return jsonify({
                    'success': True,
                    'user_type': user.user_type,
                    'redirect_url': url_for('admin.dashboard') if user.is_admin() else url_for('employee.dashboard')
                })
            else:
                if user.is_admin():
                    return redirect(url_for('admin.dashboard'))
                else:
                    return redirect(url_for('employee.dashboard'))
        else:
            if request.is_json:
                return jsonify({'success': False, 'message': 'Usuário ou senha inválidos'}), 401
            else:
                flash('Usuário ou senha inválidos', 'error')
    
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))

@auth_bp.route('/check-auth')
def check_auth():
    if current_user.is_authenticated:
        return jsonify({
            'authenticated': True,
            'user_type': current_user.user_type,
            'username': current_user.username
        })
    return jsonify({'authenticated': False})

