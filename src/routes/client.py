from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from functools import wraps
from src.models.user import db, User, Order, OrderObservation
from datetime import datetime, timedelta
import pytz

client_bp = Blueprint('client', __name__)

def client_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login'))
        if not current_user.is_client():
            flash('Acesso negado. Área exclusiva para clientes.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


@client_bp.route('/client/dashboard')
@login_required
@client_required
def dashboard():
    br_tz = pytz.timezone('America/Sao_Paulo')
    now = datetime.now(br_tz)
    
    client_orders = Order.query.filter_by(client_id=current_user.id).all()
    
    total_orders = len(client_orders)
    orders_pending = len([o for o in client_orders if o.status == 'pendente'])
    orders_in_production = len([o for o in client_orders if o.status == 'em_producao'])
    orders_ready = len([o for o in client_orders if o.status == 'pronto'])
    orders_delivered = len([o for o in client_orders if o.status == 'entregue'])
    
    recent_orders = sorted(
        client_orders, 
        key=lambda x: x.created_at, 
        reverse=True
    )[:5]
    
    upcoming_deliveries = [
        o for o in client_orders 
        if o.delivery_date >= now.date() and o.status != 'entregue'
    ]
    upcoming_deliveries = sorted(upcoming_deliveries, key=lambda x: x.delivery_date)[:5]
    
    return render_template(
        'client/dashboard.html',
        total_orders=total_orders,
        orders_pending=orders_pending,
        orders_in_production=orders_in_production,
        orders_ready=orders_ready,
        orders_delivered=orders_delivered,
        recent_orders=recent_orders,
        upcoming_deliveries=upcoming_deliveries
    )


@client_bp.route('/client/orders')
@login_required
@client_required
def orders():
    status_filter = request.args.get('status', 'all')
    
    query = Order.query.filter_by(client_id=current_user.id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    client_orders = query.order_by(Order.created_at.desc()).all()
    
    return render_template(
        'client/orders.html',
        orders=client_orders,
        status_filter=status_filter
    )


@client_bp.route('/client/order/<int:order_id>')
@login_required
@client_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    
    if order.client_id != current_user.id:
        flash('Você não tem permissão para visualizar este pedido.', 'danger')
        return redirect(url_for('client.orders'))
    
    observations = OrderObservation.query.filter_by(order_id=order.id).order_by(
        OrderObservation.created_at.desc()
    ).all()
    
    return render_template(
        'client/order_detail.html',
        order=order,
        observations=observations
    )


@client_bp.route('/client/profile')
@login_required
@client_required
def profile():
    return render_template('client/profile.html', user=current_user)


@client_bp.route('/client/profile/edit', methods=['POST'])
@login_required
@client_required
def edit_profile():
    try:
        current_user.cnpj = request.form.get('cnpj', current_user.cnpj)
        current_user.email = request.form.get('email', current_user.email)
        current_user.phone = request.form.get('phone', current_user.phone)
        current_user.address = request.form.get('address', current_user.address)
        
        db.session.commit()
        flash('Perfil atualizado com sucesso!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erro ao atualizar perfil: {str(e)}', 'danger')
    
    return redirect(url_for('client.profile'))


@client_bp.route('/client/change-password', methods=['POST'])
@login_required
@client_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not current_user.check_password(current_password):
        flash('Senha atual incorreta.', 'danger')
        return redirect(url_for('client.profile'))
    
    if new_password != confirm_password:
        flash('As senhas não coincidem.', 'danger')
        return redirect(url_for('client.profile'))
    
    if len(new_password) < 6:
        flash('A nova senha deve ter pelo menos 6 caracteres.', 'danger')
        return redirect(url_for('client.profile'))
    
    current_user.set_password(new_password)
    db.session.commit()
    
    flash('Senha alterada com sucesso!', 'success')
    return redirect(url_for('client.profile'))


@client_bp.route('/client/api/orders/stats')
@login_required
@client_required
def orders_stats():
    client_orders = Order.query.filter_by(client_id=current_user.id).all()
    
    status_counts = {
        'pendente': 0,
        'em_producao': 0,
        'pronto': 0,
        'entregue': 0
    }
    
    for order in client_orders:
        if order.status in status_counts:
            status_counts[order.status] += 1
    
    return jsonify(status_counts)
