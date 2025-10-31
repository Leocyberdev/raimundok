from flask import Blueprint, render_template, abort, current_app, url_for
from src.models.user import Order, OrderObservation
import os

public_bp = Blueprint('public', __name__)

@public_bp.route('/rastrear/<uuid:tracking_token>')
def track_order(tracking_token):
    """
    Rota pública para rastrear o status de um pedido usando o token de rastreamento.
    """
    # Converte o UUID para string para a consulta
    tracking_token_str = str(tracking_token)
    
    # Busca o pedido pelo token de rastreamento
    order = Order.query.filter_by(tracking_token=tracking_token_str).first()
    
    if not order:
        abort(404) # Pedido não encontrado
    
    # Obtém as observações do pedido (se necessário para o rastreamento)
    observations = OrderObservation.query.filter_by(order_id=order.id).order_by(OrderObservation.created_at.desc()).all()
    
    # Cria o link público completo para o cliente
    public_link = url_for('public.track_order', tracking_token=tracking_token_str, _external=True)

    # Lógica para determinar o status amigável
    status_map = {
        'pendente': 'Aguardando Aprovação',
        'aprovado': 'Em Produção',
        'em_producao': 'Em Produção',
        'pronto': 'Pronto para Entrega',
        'entregue': 'Entregue',
        'cancelado': 'Cancelado'
    }
    
    # O status amigável é o que o cliente verá
    friendly_status = status_map.get(order.status, 'Status Desconhecido')
    
    # Define o arquivo da logo para o template
    logo_url = None
    if order.company_logo:
        logo_url = url_for('static', filename='uploads/' + order.company_logo)

    return render_template('public/track_order.html', 
                           order=order, 
                           friendly_status=friendly_status,
                           observations=observations,
                           logo_url=logo_url,
                           public_link=public_link)

@public_bp.app_errorhandler(404)
def page_not_found(e):
    return render_template('public/404.html'), 404

@public_bp.route('/public/logo/<filename>')
def serve_logo(filename):
    """Serve a logo da empresa de forma pública e segura."""
    # Garante que apenas logos sejam servidas
    if '..' in filename or filename.startswith('/'):
        abort(404)
    
    # O caminho completo para o arquivo
    logo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    
    # Verifica se o arquivo existe
    if not os.path.exists(logo_path):
        abort(404)
        
    # Retorna o arquivo
    return send_from_directory(current_app.config['UPLOAD_FOLDER'], filename)
