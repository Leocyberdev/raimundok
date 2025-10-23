from flask import Blueprint, render_template, abort, request
from models.user import Order, StatusHistory
from utils.date_utils import get_delivery_status_text
from datetime import datetime
import pytz

public_bp = Blueprint('public', __name__)

@public_bp.route('/rastreamento/<token>')
def track_order(token):
    """Página pública de rastreamento de pedido"""
    order = Order.query.filter_by(tracking_token=token).first()
    
    if not order:
        abort(404)
    
    status_history = StatusHistory.query.filter_by(order_id=order.id).order_by(StatusHistory.changed_at.asc()).all()
    
    delivery_status = get_delivery_status_text(order.delivery_date)
    
    status_map = {
        'pendente': {'label': 'Pendente', 'icon': '⏳', 'color': 'warning'},
        'aprovado': {'label': 'Aprovado', 'icon': '✅', 'color': 'success'},
        'em_producao': {'label': 'Em Produção', 'icon': '🔨', 'color': 'info'},
        'pronto': {'label': 'Pronto', 'icon': '📦', 'color': 'primary'},
        'entregue': {'label': 'Entregue', 'icon': '🎉', 'color': 'success'}
    }
    
    all_statuses = ['pendente', 'aprovado', 'em_producao', 'pronto', 'entregue']
    
    try:
        current_status_index = all_statuses.index(order.status)
    except ValueError:
        current_status_index = 0
    
    timeline = []
    for idx, status_key in enumerate(all_statuses):
        status_info = status_map.get(status_key, {'label': status_key.title(), 'icon': '📌', 'color': 'secondary'})
        
        is_completed = idx <= current_status_index
        is_current = idx == current_status_index
        
        history_entry = next(
            (h for h in status_history if h.new_status == status_key),
            None
        )
        
        timeline.append({
            'status': status_key,
            'label': status_info['label'],
            'icon': status_info['icon'],
            'color': status_info['color'],
            'is_completed': is_completed,
            'is_current': is_current,
            'changed_at': history_entry.changed_at if history_entry else None,
            'changed_by': history_entry.user.username if history_entry else None
        })
    
    return render_template(
        'public/track_order.html',
        order=order,
        timeline=timeline,
        delivery_status=delivery_status
    )
