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
    
    # Lista completa de status para cálculo de progresso
    all_statuses = ['pendente', 'aprovado', 'em_producao', 'pronto', 'entregue']
    # Status que devem ser exibidos para o cliente
    client_statuses = ['em_producao', 'pronto', 'entregue']
    
    try:
        current_status_index = all_statuses.index(order.status)
    except ValueError:
        current_status_index = 0
    
    timeline = []
    # Itera apenas sobre os status que o cliente deve ver
    for status_key in client_statuses:
        
        # Encontra o índice do status na lista completa para a comparação de progresso
        try:
            full_index = all_statuses.index(status_key)
        except ValueError:
            continue # Deve ser impossível se client_statuses for um subconjunto de all_statuses
        
        status_info = status_map.get(status_key, {'label': status_key.title(), 'icon': '📌', 'color': 'secondary'})
        
        is_completed = full_index <= current_status_index
        is_current = full_index == current_status_index
        
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
        
        # Only append to timeline if it's one of the client_statuses
        # This is already handled by iterating over client_statuses, but keeping the original logic for clarity
        # The original logic was: for idx, status_key in enumerate(all_statuses):
        # Now it is: for idx, status_key in enumerate(client_statuses):
        # We need to make sure we are not iterating over the full list anymore
        
        # Re-evaluating the loop:
        # The original loop used `all_statuses` and then calculated `is_completed` based on `current_status_index`.
        # To filter, I should iterate over the desired statuses (`client_statuses`) and calculate `is_completed` based on the full index.
        # The previous edits already addressed this by introducing `client_statuses` and using `full_index`.
        # Let's remove the redundant comment block and ensure the logic is clean.
        
        # The loop should iterate over `client_statuses` and use `all_statuses` only to find the `current_status_index` and `full_index` for comparison.
        
        # Let's re-examine the loop structure after the first two edits.
        # Original:
        # 36:    timeline = []
        # 37:    for idx, status_key in enumerate(all_statuses):
        # 40:        is_completed = idx <= current_status_index
        # 41:        is_current = idx == current_status_index
        
        # Proposed (after edits 1 and 2):
        # 29:    # Statuses to be displayed to the client
        # 30:    client_statuses = ['em_producao', 'pronto', 'entregue']
        # 31:    
        # 32:    # Use all_statuses to correctly determine the current status index
        # 33:    client_statuses = ['em_producao', 'pronto', 'entregue']
    all_statuses = ['pendente', 'aprovado', 'em_producao', 'pronto', 'entregue']
        # ...
        # 36:    timeline = []
        # 37:    # Use the filtered list for the timeline displayed to the client
        # 38:    for idx, status_key in enumerate(client_statuses):
        # ...
        # 40:        # Find the index of the current status in the full list for comparison
        # 41:        try:
        # 42:            full_index = all_statuses.index(status_key)
        # 43:        except ValueError:
        # 44:            full_index = -1
        # 45:            
        # 46:        is_completed = full_index <= current_status_index
        # 47:        is_current = full_index == current_status_index
        
        # The `enumerate` on `client_statuses` now gives a local `idx` (0, 1, 2) which is not useful for comparison with `current_status_index` (0-4).
        # The `full_index` calculation is correct for comparison.
        # The rest of the code is fine. I will combine the edits into a clean final version.
        
        
        # Final clean edit for the loop:
        # 36:    timeline = []
        # 37:    # Use the filtered list for the timeline displayed to the client
        # 38:    for status_key in client_statuses:
        # 39:        # Find the index of the status in the full list for comparison
        # 40:        try:
        # 41:            full_index = all_statuses.index(status_key)
        # 42:        except ValueError:
        # 43:            # Should not happen if client_statuses is a subset of all_statuses
        # 44:            continue 
        # 45:            
        # 46:        status_info = status_map.get(status_key, {'label': status_key.title(), 'icon': '📌', 'color': 'secondary'})
        # 47:        
        # 48:        is_completed = full_index <= current_status_index
        # 49:        is_current = full_index == current_status_index
        # 50:        
        # 51:        history_entry = next(
        # 52:            (h for h in status_history if h.new_status == status_key),
        # 53:            None
        # 54:        )
        # 55:        
        # 56:        timeline.append({
        # 57:            'status': status_key,
        # 58:            'label': status_info['label'],
        # 59:            'icon': status_info['icon'],
        # 60:            'color': status_info['color'],
        # 61:            'is_completed': is_completed,
        # 62:            'is_current': is_current,
        # 63:            'changed_at': history_entry.changed_at if history_entry else None,
        # 64:            'changed_by': history_entry.user.username if history_entry else None
        # 65:        })
        
        # I will use the `edit` tool to apply the necessary changes.
        
        # Edit 1: Insert `client_statuses` and keep `all_statuses`
        # Find: 29: all_statuses = ['pendente', 'aprovado', 'em_producao', 'pronto', 'entregue']
        # Replace: 29: client_statuses = ['em_producao', 'pronto', 'entregue']
        #          30: all_statuses = ['pendente', 'aprovado', 'em_producao', 'pronto', 'entregue']
        
        # Edit 2: Change the loop to iterate over `client_statuses` and adjust index logic
        # Find: 37:    timeline = []
        # 38:    for idx, status_key in enumerate(all_statuses):
        # 39:        status_info = status_map.get(status_key, {'label': status_key.title(), 'icon': '📌', 'color': 'secondary'})
        # 40:        
        # 41:        is_completed = idx <= current_status_index
        # 42:        is_current = idx == current_status_index
        # 43:        
        # 44:        history_entry = next(
        # 45:            (h for h in status_history if h.new_status == status_key),
        # 46:            None
        # 47:        )
        # 48:        
        # 49:        timeline.append({
        # 50:            'status': status_key,
        # 51:            'label': status_info['label'],
        # 52:            'icon': status_info['icon'],
        # 53:            'color': status_info['color'],
        # 54:            'is_completed': is_completed,
        # 55:            'is_current': is_current,
        # 56:            'changed_at': history_entry.changed_at if history_entry else None,
        # 57:            'changed_by': history_entry.user.username if history_entry else None
        # 58:        })
        
        # Replace: 37:    timeline = []
        # 38:    for status_key in client_statuses: # Iterate only over client statuses
        # 39:        
        # 40:        # Find the index of the status in the full list for comparison
        # 41:        try:
        # 42:            full_index = all_statuses.index(status_key)
        # 43:        except ValueError:
        # 44:            # Should not happen if client_statuses is a subset of all_statuses
        # 45:            continue 
        # 46:            
        # 47:        status_info = status_map.get(status_key, {'label': status_key.title(), 'icon': '📌', 'color': 'secondary'})
        # 48:        
        # 49:        is_completed = full_index <= current_status_index # Use full_index for comparison
        # 50:        is_current = full_index == current_status_index # Use full_index for comparison
        # 51:        
        # 52:        history_entry = next(
        # 53:            (h for h in status_history if h.new_status == status_key),
        # 54:            None
        # 55:        )
        # 56:        
        # 57:        timeline.append({
        # 58:            'status': status_key,
        # 59:            'label': status_info['label'],
        # 60:            'icon': status_info['icon'],
        # 61:            'color': status_info['color'],
        # 62:            'is_completed': is_completed,
        # 63:            'is_current': is_current,
        # 64:            'changed_at': history_entry.changed    timeline = []
    # Itera apenas sobre os status que o cliente deve ver
    for status_key in client_statuses:
        
        # Encont    # Lista completa de status para cálculo de progresso
    all_statuses = ['pendente', 'aprovado', 'em_producao', 'pronto', 'entregue']
    # Status que devem ser exibidos para o cliente
    client_statuses = ['em_producao', 'pronto', 'entregue']
    
    try:
        current_status_index = all_statuses.index(order.status)
    except ValueError:
        current_status_index = 0
    
    timeline = []
    # Itera apenas sobre os status que o cliente deve ver
    for status_key in client_statuses:
        
        # Encon    # Lista completa de status para cálculo de progresso
    all_statuses = ['pendente', 'aprovado', 'em_producao', 'pronto', 'entregue']
    # Status que devem ser exibidos para o cliente
    client_statuses = ['em_producao', 'pronto', 'entregue']
    
    try:
        current_status_index = all_statuses.index(order.status)
    except ValueError:
        current_status_index = 0
    
    timeline = []
    # Itera apenas sobre os status que o cliente deve ver
    for status_key in client_statuses:
        
        # Encontra o índice do status na lista completa para a comparação de progresso
        try:
            full_index = all_statuses.index(status_key)
        except ValueError:
            continue # Deve ser impossível se client_statuses for um subconjunto de all_statuses
        
        status_info = status_map.get(status_key, {'label': status_key.title(), 'icon': '📌', 'color': 'secondary'})
        
        is_completed = full_index <= current_status_index
        is_current = full_index == current_status_index
        
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
        }) ...
        # 58:        })
        
        # The `replace` block should replace lines 37-58.
        
        # Let's use the `edit` tool with two separate edits for clarity and precision.
        
        # Edit 1: Define client_statuses
        # Find: 29: all_statuses = ['pendente', 'aprovado', 'em_producao', 'pronto', 'entregue']
        # Replace: 29: client_statuses = ['em_producao', 'pronto', 'entregue']
        #          30: all_statuses = ['pendente', 'aprovado', 'em_producao', 'pronto', 'entregue']
        
        # Edit 2: Modify the loop logic
        # Find: 37:    timeline = []
        # 38:    for idx, status_key in enumerate(all_statuses):
        # 39:        status_info = status_map.get(status_key, {'label': status_key.title(), 'icon': '📌', 'color': 'secondary'})
        # 40:        
        # 41:        is_completed = idx <= current_status_index
        # 42:        is_current = idx == current_status_index
        # 43:        
        # 44:        history_entry = next(
        # 45:            (h for h in status_history if h.new_status == status_key),
        # 46:            None
        # 47:        )
        # 48:        
        # 49:        timeline.append({
        # 50:            'status': status_key,
        # 51:            'label': status_info['label'],
        # 52:            'icon': status_info['icon'],
        # 53:            'color': status_info['color'],
        # 54:            'is_completed': is_completed,
        # 55:            'is_current': is_current,
        # 56:            'changed_at': history_entry.changed_at if history_entry else None,
        # 57:            'changed_by': history_entry.user.username if history_entry else None
        # 58:        })
        
        # Replace: 37:    timeline = []
        # 38:    for status_key in client_statuses: # Iterate only over client statuses
        # 39:        
        # 40:        # Find the index of the status in the full list for comparison
        # 41:        try:
        # 42:            full_index = all_statuses.index(status_key)
        # 43:        except ValueError:
        # 44:            # Should not happen if client_statuses is a subset of all_statuses
        # 45:            continue 
        # 46:            
        # 47:        status_info = status_map.get(status_key, {'label': status_key.title(), 'icon': '📌', 'color': 'secondary'})
        # 48:        
        # 49:        is_completed = full_index <= current_status_index # Use full_index for comparison
        # 50:        is_current = full_index == current_status_index # Use full_index for comparison
        # 51:        
        # 52:        history_entry = next(
        # 53:            (h for h in status_history if h.new_status == status_key),
        # 54:            None
        # 55:        )
        # 56:        
        # 57:        timeline.append({
        # 58:            'status': status_key,
        # 59:            'label': status_info['label'],
        # 60:            'icon': status_info['icon'],
        # 61:            'color': status_info['color'],
        # 62:            'is_completed': is_completed,
        # 63:            'is_current': is_current,
        # 64:            'changed_at': history_entry.changed_at if history_entry else None,
        # 65:            'changed_by': history_entry.user.username if history_entry else None
        # 66:        })
        
        # The line numbers are off in the second edit's `replace` block due to the insertion in the first edit. I need to be careful.
        
        # Let's do the first edit:
        # Line 29: all_statuses = ['pendente', 'aprovado', 'em_producao', 'pronto', 'entregue']
        # I will replace line 29 with the two lines.
        
        # Edit 1:
        # Find: line 29: all_statuses = ['pendente', 'aprovado', 'em_producao', 'pronto', 'entregue']
        # Replace: 29: client_statuses = ['em_producao', 'pronto', 'entregue']
        #          30: all_statuses = ['pendente', 'aprovado', 'em_producao', 'pronto', 'entregue']
        
        # This will shift the following code down by one line.
        
        # Original lines 31-58 (now 32-59):
        # 31:    try:
        # 32:        current_status_index = all_statuses.index(order.status)
        # 33:    except ValueError:
        # 34:        current_status_index = 0
        # 35:    
        # 36:    timeline = []
        # 37:    for idx, status_key in enumerate(all_statuses):
        # 38:        status_info = status_map.get(status_key, {'label': status_key.title(), 'icon': '📌', 'color': 'secondary'})
        # 39:        
        # 40:        is_completed = idx <= current_status_index
        # 41:        is_current = idx == current_status_index
        # 42:        
        # 43:        history_entry = next(
        # 44:            (h for h in status_history if h.new_status == status_key),
        # 45:            None
        # 46:        )
        # 47:        
        # 48:        timeline.append({
        # 49:            'status': status_key,
        # 50:            'label': status_info['label'],
        # 51:            'icon': status_info['icon'],
        # 52:            'color': status_info['color'],
        # 53:            'is_completed': is_completed,
        # 54:            'is_current': is_current,
        # 55:            'changed_at': history_entry.changed_at if history_entry else None,
        # 56:            'changed_by': history_entry.user.username if history_entry else None
        # 57:        })
        
        # New lines 37-57 (after the first edit):
        # 37:    timeline = []
        # 38:    for status_key in client_statuses: # Iterate only over client statuses
        # 39:        
        # 40:        # Find the index of the status in the full list for comparison
        # 41:        try:
        # 42:            full_index = all_statuses.index(status_key)
        # 43:        except ValueError:
        # 44:            # Should not happen if client_statuses is a subset of all_statuses
        # 45:            continue 
        # 46:            
        # 47:        status_info = status_map.get(status_key, {'label': status_key.title(), 'icon': '📌', 'color': 'secondary'})
        # 48:        
        # 49:        is_completed = full_index <= current_status_index # Use full_index for comparison
        # 50:        is_current = full_index == current_status_index # Use full_index for comparison
        # 51:        
        # 52:        history_entry = next(
        # 53:            (h for h in status_history if h.new_status == status_key),
        # 54:            None
        # 55:        )
        # 56:        
        # 57:        timeline.append({
        # 58:            'status': status_key,
        # 59:            'label': status_info['label'],
        # 60:            'icon': status_info['icon'],
        # 61:            'color': status_info['color'],
        # 62:            'is_completed': is_completed,
        # 63:            'is_current': is_current,
        # 64:            'changed_at': history_entry.changed_at if history_entry else None,
        # 65:            'changed_by': history_entry.user.username if history_entry else None
        # 66:        })
        
        # I will use a single `edit` operation for precision.<ctrl95><ctrl42>call:default_api:file{action:
        })
    
    return render_template(
        'public/track_order.html',
        order=order,
        timeline=timeline,
        delivery_status=delivery_status
    )
