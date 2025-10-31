from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
import pytz
from src.models.user import db, User, Order, OrderObservation, Notification, StatusHistory, DeliveryOption, StatusPermission, ServiceOrder
from src.utils.date_utils import get_delivery_status_text, get_weekday_name_pt, get_elapsed_days_text, is_delivery_urgent


employee_bp = Blueprint('employee', __name__)

def employee_required(f):
    """Decorator para verificar se o usuário é funcionário"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_employee():
            flash('Acesso negado. Apenas funcionários podem acessar esta página.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@employee_bp.route('/funcionario')
@login_required
@employee_required
def dashboard():
    """Dashboard principal do funcionário"""
    # Pedidos em produção
    in_production = Order.query.filter_by(status='em_producao', approved=True).count()
    ready_orders = Order.query.filter_by(status='pronto', approved=True).count()
    # Total aprovados excluindo entregues
    total_approved = Order.query.filter(Order.approved == True, Order.status != 'entregue').count()

    # Pedidos recentes aprovados (excluindo entregues)
    recent_orders = Order.query.filter(Order.approved == True, Order.status != 'entregue').order_by(Order.created_at.desc()).limit(5).all()

    # Notificações não lidas
    unread_notifications = Notification.query.filter_by(user_id=current_user.id, read=False).count()

    # Pedidos com prazo próximo (próximos 3 dias)
    from datetime import timedelta
    upcoming_deadline = date.today() + timedelta(days=3)
    urgent_orders = Order.query.filter(
        Order.approved == True,
        Order.is_urgent == True, # Adicionado para verificar a flag is_urgent
        Order.status.in_(['aprovado', 'em_producao', 'pronto'])
    ).count()

    return render_template('employee/dashboard.html',
                         in_production=in_production,
                         ready_orders=ready_orders,
                         total_approved=total_approved,
                         recent_orders=recent_orders,
                         unread_notifications=unread_notifications,
                         urgent_orders=urgent_orders, date=date)

@employee_bp.route('/funcionario/pedidos')
@login_required
@employee_required
def orders():
    """Lista de pedidos aprovados (excluindo entregues)"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')

    query = Order.query.filter(Order.approved == True, Order.status != 'entregue')
    if status_filter and status_filter != 'entregue':
        query = query.filter_by(status=status_filter)

    orders = query.order_by(Order.delivery_date.asc()).paginate(
        page=page, per_page=10, error_out=False)

    return render_template('employee/orders.html', orders=orders, status_filter=status_filter)

@employee_bp.route('/funcionario/pedidos/<int:order_id>')
@login_required
@employee_required
def order_detail(order_id):
    """Detalhes de um pedido específico"""
    from src.models.user import StatusHistory, DeliveryOption

    order = Order.query.get_or_404(order_id)

    if not order.approved:
        flash('Este pedido ainda não foi aprovado.', 'warning')
        return redirect(url_for('employee.orders'))

    # Buscar observações do pedido
    observations = OrderObservation.query.filter_by(order_id=order_id).order_by(OrderObservation.created_at.desc()).all()

    # Buscar histórico de status
    status_history = StatusHistory.query.filter_by(order_id=order_id).order_by(StatusHistory.created_at.desc()).all()

    # Buscar opções de entrega (se existirem)
    delivery_options = DeliveryOption.query.filter_by(order_id=order_id).order_by(DeliveryOption.created_at.desc()).all()

    # Calcular informações de data
    order_data = {
        'delivery_status': get_delivery_status_text(order.delivery_date),
        'elapsed_days': get_elapsed_days_text(order.order_date),
        'weekday_name': get_weekday_name_pt(order.order_date),
        'is_urgent': is_delivery_urgent(order.delivery_date)
    }

    return render_template('employee/order_detail.html', 
                         order=order, 
                         observations=observations,
                         status_history=status_history,
                         delivery_options=delivery_options,
                         order_data=order_data)

@employee_bp.route('/funcionario/pedidos/<int:order_id>/observacao', methods=['POST'])
@login_required
@employee_required
def add_observation(order_id):
    """Adicionar observação a um pedido"""
    from src.models.user import OrderObservation

    order = Order.query.get_or_404(order_id)
    observation_text = request.form.get('observation', '').strip()

    if observation_text:
        observation = OrderObservation(
            order_id=order_id,
            author_id=current_user.id,
            content=observation_text
        )

        db.session.add(observation)
        db.session.commit()
        flash('Observação adicionada com sucesso!', 'success')
    else:
        flash('Observação não pode estar vazia!', 'error')

    # Redirecionar de volta para a página anterior
    return redirect(request.referrer or url_for('employee.orders'))

@employee_bp.route('/funcionario/notificacoes')
@login_required
@employee_required
def notifications():
    """Lista de notificações do funcionário"""
    page = request.args.get('page', 1, type=int)

    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(
        Notification.created_at.desc()).paginate(page=page, per_page=15, error_out=False)

    # Calcular quantas notificações são de hoje ou depois (data sem hora)
    today = date.today()
    today_count = sum(1 for n in notifications.items if n.created_at.date() >= today)
    return render_template('employee/notifications.html', notifications=notifications, today_count=today_count)

@employee_bp.route('/funcionario/notificacoes/<int:notification_id>/marcar-lida', methods=['POST'])
@login_required
@employee_required
def mark_notification_read(notification_id):
    """Marcar notificação como lida"""
    notification = Notification.query.get_or_404(notification_id)

    if notification.user_id != current_user.id:
        flash('Acesso negado.', 'error')
        return redirect(url_for('employee.notifications'))
    db.session.delete(notification)
    db.session.commit()

    return jsonify({"success": True, "message": "Notificação marcada como lida e excluída."})

@employee_bp.route('/funcionario/notificacoes/marcar-todas-lidas', methods=['POST'])
@login_required
@employee_required
def mark_all_notifications_read():
    """Marcar todas as notificações como lidas e excluí-las"""
    Notification.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()

    flash("Todas as notificações lidas foram excluídas.", "success")
    return redirect(url_for("employee.notifications"))

@employee_bp.route('/funcionario/calendario')
@login_required
@employee_required
def calendar():
    """Calendário de pedidos para funcionário"""
    return render_template('employee/calendar.html')

@employee_bp.route('/funcionario/api/calendario')
@login_required
@employee_required
def calendar_api():
    """API para dados do calendário do funcionário"""
    # Apenas pedidos aprovados (excluindo entregues)
    orders = Order.query.filter(Order.approved == True, Order.status != 'entregue').all()
    events = []

    for order in orders:
        # Cor baseada no status
        color_map = {
            'aprovado': '#3788d8',
            'em_producao': '#8b4513',
            'pronto': '#10b981',
            'entregue': '#4f5553'
        }

        # Evento para data de entrega
        events.append({
            'id': f'delivery_{order.id}',
            'title': f'{order.company_name}',
            'start': order.delivery_date.isoformat(),
            'backgroundColor': color_map.get(order.status, '#6b7280'),
            'borderColor': color_map.get(order.status, '#6b7280'),
            'extendedProps': {
                'type': 'delivery',
                'order_id': order.id,
                'company_name': order.company_name,
                'status': order.status,
                'order_date': order.order_date.isoformat()
            }
        })

    return jsonify(events)

@employee_bp.route('/funcionario/estatisticas')
@login_required
@employee_required
def statistics():
    """Estatísticas para o funcionário"""
    from sqlalchemy import func, extract

    # Estatísticas básicas (excluindo entregues dos contadores principais)
    total_orders = Order.query.filter(Order.approved == True, Order.status != 'entregue').count()
    in_production = Order.query.filter_by(status='em_producao', approved=True).count()
    completed = Order.query.filter_by(status='entregue', approved=True).count()

    # Pedidos por status (incluindo entregues para visualização completa)
    status_counts = db.session.query(
        Order.status,
        func.count(Order.id).label('count')
    ).filter_by(approved=True).group_by(Order.status).all()

    # Pedidos por mês (apenas aprovados)
    monthly_orders = db.session.query(
        extract('month', Order.created_at).label('month'),
        func.count(Order.id).label('count')
    ).filter_by(approved=True).group_by(extract('month', Order.created_at)).all()

    return render_template('employee/statistics.html',
                         total_orders=total_orders,
                         in_production=in_production,
                         completed=completed,
                         status_counts=status_counts,
                         monthly_orders=monthly_orders)

@employee_bp.route('/funcionario/api/notificacoes-nao-lidas')
@login_required
@employee_required
def unread_notifications_count():
    """API para contar notificações não lidas"""
    count = Notification.query.filter_by(user_id=current_user.id, read=False).count()
    return jsonify({'count': count})

@employee_bp.route('/funcionario/perfil')
@login_required
@employee_required
def profile():
    """Perfil do funcionário"""
    # Estatísticas pessoais
    observations_count = OrderObservation.query.filter_by(author_id=current_user.id).count()

    return render_template('employee/profile.html', observations_count=observations_count)

@employee_bp.route('/funcionario/perfil/foto', methods=['POST'])
@login_required
@employee_required
def upload_profile_picture():
    """Upload da foto de perfil do funcionário"""
    from werkzeug.utils import secure_filename
    import os

    if 'profile_picture' not in request.files:
        flash('Nenhum arquivo selecionado!', 'error')
        return redirect(url_for('employee.profile'))

    file = request.files['profile_picture']

    if file.filename == '':
        flash('Nenhum arquivo selecionado!', 'error')
        return redirect(url_for('employee.profile'))

    # Verificar se é uma imagem válida
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''

    if file_extension not in allowed_extensions:
        flash('Formato de arquivo inválido! Use PNG, JPG, JPEG, GIF ou WEBP.', 'error')
        return redirect(url_for('employee.profile'))

    try:
        from flask import current_app

        # Remover foto anterior se existir
        if current_user.profile_picture:
            old_photo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles', current_user.profile_picture)
            if os.path.exists(old_photo_path):
                os.remove(old_photo_path)

        # Criar diretório de perfis se não existir
        profile_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles')
        os.makedirs(profile_dir, exist_ok=True)

        # Salvar nova foto
        filename = secure_filename(file.filename)
        timestamp = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%Y%m%d_%H%M%S_")
        profile_filename = f"{timestamp}profile_{current_user.id}_{filename}"

        file_path = os.path.join(profile_dir, profile_filename)
        file.save(file_path)

        # Atualizar banco de dados
        current_user.profile_picture = profile_filename
        db.session.commit()

        flash('Foto de perfil atualizada com sucesso!', 'success')

    except Exception as e:
        flash(f'Erro ao fazer upload da foto: {str(e)}', 'error')

    return redirect(url_for('employee.profile'))


# ===== ROTAS PARA ORDEM DE SERVIÇO =====

@employee_bp.route('/funcionario/ordens-servico')
@login_required
@employee_required
def service_orders():
    """Lista ordens de serviço atribuídas ao funcionário"""
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Buscar ordens de serviço atribuídas ao funcionário atual, excluindo as entregues
    service_orders = ServiceOrder.query.join(Order).filter(
        ServiceOrder.assigned_employees.contains(current_user),
        Order.status != 'entregue'
    ).order_by(ServiceOrder.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return render_template('employee/service_orders.html', 
                         service_orders=service_orders)

@employee_bp.route('/funcionario/ordem-servico/<int:service_order_id>')
@login_required
@employee_required
def service_order_detail(service_order_id):
    """Visualizar detalhes de uma ordem de serviço"""
    service_order = ServiceOrder.query.get_or_404(service_order_id)

    # Verificar se o funcionário tem acesso a esta ordem de serviço
    if current_user not in service_order.assigned_employees:
        flash('Você não tem acesso a esta ordem de serviço.', 'error')
        return redirect(url_for('employee.service_orders'))

    return render_template('employee/service_order_detail.html', 
                         service_order=service_order)

@employee_bp.route('/funcionario/ordem-servico/<int:service_order_id>/download-pdf')
@login_required
@employee_required
def download_service_order_pdf(service_order_id):
    """Download do primeiro arquivo da ordem de serviço (compatibilidade)"""
    service_order = ServiceOrder.query.get_or_404(service_order_id)

    # Verificar se o funcionário tem acesso a esta ordem de serviço
    if current_user not in service_order.assigned_employees:
        flash('Você não tem acesso a esta ordem de serviço.', 'error')
        return redirect(url_for('employee.service_orders'))

    # Buscar o primeiro arquivo disponível
    first_file = None
    if service_order.file1_filename:
        first_file = service_order.file1_filename
    elif service_order.file2_filename:
        first_file = service_order.file2_filename
    elif service_order.file3_filename:
        first_file = service_order.file3_filename

    if not first_file:
        flash('Esta ordem de serviço não possui arquivos.', 'error')
        return redirect(url_for('employee.service_order_detail', service_order_id=service_order_id))

    return download_service_order_file(service_order_id, first_file)

@employee_bp.route('/funcionario/ordem-servico/<int:service_order_id>/download/<filename>')
@login_required
@employee_required
def download_service_order_file(service_order_id, filename):
    """Download de arquivo específico da ordem de serviço"""
    from flask import send_from_directory, current_app
    import os

    service_order = ServiceOrder.query.get_or_404(service_order_id)

    # Verificar se o funcionário tem acesso a esta ordem de serviço
    if current_user not in service_order.assigned_employees:
        flash('Você não tem acesso a esta ordem de serviço.', 'error')
        return redirect(url_for('employee.service_orders'))

    # Verificar se o arquivo existe na ordem de serviço
    valid_files = service_order.get_files_list()
    if filename not in valid_files:
        flash('Arquivo não encontrado nesta ordem de serviço.', 'error')
        return redirect(url_for('employee.service_order_detail', service_order_id=service_order_id))

    # Caminho do arquivo
    files_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'service_orders')
    file_path = os.path.join(files_dir, filename)

    # Verificar se o arquivo existe fisicamente
    if not os.path.exists(file_path):
        flash('Arquivo não encontrado no servidor.', 'error')
        return redirect(url_for('employee.service_order_detail', service_order_id=service_order_id))

    try:
        return send_from_directory(files_dir, filename, as_attachment=True)
    except Exception as e:
        flash('Erro ao baixar o arquivo.', 'error')
        return redirect(url_for('employee.service_order_detail', service_order_id=service_order_id))


# ===== ROTAS PARA ALTERAÇÃO DE STATUS COM PERMISSÕES =====

@employee_bp.route('/funcionario/pedidos/<int:order_id>/alterar-status', methods=['POST'])
@login_required
@employee_required
def change_order_status(order_id):
    """Alterar status do pedido com verificação de permissões"""
    from src.models.user import StatusPermission, StatusHistory, DeliveryOption

    order = Order.query.get_or_404(order_id)

    if not order.approved:
        return jsonify({'success': False, 'message': 'Este pedido ainda não foi aprovado.'})

    new_status = request.form.get('status')
    if not new_status:
        return jsonify({'success': False, 'message': 'Status não informado.'})

    # Verificar se o funcionário tem permissão para alterar para este status
    permission = StatusPermission.query.filter_by(
        user_id=current_user.id, 
        status=new_status
    ).first()

    if not permission or not permission.can_change:
        return jsonify({
            'success': False, 
            'message': f'Você não tem permissão para alterar o status para "{new_status}".'
        })

    old_status = order.status

    # Se o status for 'entregue', verificar se as opções de entrega foram fornecidas
    if new_status == 'entregue':
        fonte = request.form.get('fonte') in ['true', 'on']
        gabarito = request.form.get('gabarito') in ['true', 'on']
        com_pistao = request.form.get('com_pistao') in ['true', 'on']
        placa_cristal = request.form.get('placa_cristal') in ['true', 'on']

        # Verificar se pelo menos uma opção foi selecionada
        if not any([fonte, gabarito, com_pistao, placa_cristal]):
            return jsonify({'success': False, 'message': 'Selecione pelo menos uma opção de entrega'})

        # Criar registro de opções de entrega
        delivery_option = DeliveryOption(
            order_id=order_id,
            fonte=fonte,
            gabarito=gabarito,
            com_pistao=com_pistao,
            placa_cristal=placa_cristal,
            created_by_id=current_user.id
        )
        db.session.add(delivery_option)

    try:
        # Registrar histórico de alteração
        status_history = StatusHistory(
            order_id=order_id,
            user_id=current_user.id,
            old_status=old_status,
            new_status=new_status
        )
        db.session.add(status_history)

        # Atualizar status
        order.status = new_status

        # Se o status for 'entregue', marcar data de entrega
        if new_status == 'entregue':
            # Corrigir o fuso horário para UTC antes de salvar
            tz_saopaulo = pytz.timezone('America/Sao_Paulo')
            now_saopaulo = datetime.now(tz_saopaulo)
            order.delivered_at = now_saopaulo.astimezone(pytz.utc)

        db.session.commit()

        # Criar notificação para administradores
        admins = User.query.filter_by(user_type='admin').all()
        for admin in admins:
            notification = Notification(
                user_id=admin.id,
                title='Status de pedido alterado',
                message=f'{current_user.username} alterou o status do pedido da empresa {order.company_name} de "{old_status}" para "{new_status}".'
            )
            db.session.add(notification)

        db.session.commit()

        return jsonify({
            'success': True, 
            'message': f'Status alterado para "{new_status}" com sucesso!',
            'new_status': new_status
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao alterar status: {str(e)}'})

# ===== ROTAS PARA PEDIDOS POR STATUS =====

@employee_bp.route('/funcionario/pedidos/status')
@login_required
@employee_required
def status_orders():
    """Pedidos por status"""
    status = request.args.get('status', 'aprovado')
    page = request.args.get('page', 1, type=int)

    # Mapear nomes de status
    status_config = {
        'aprovado': {
            'name': 'Aprovados',
            'icon': 'fas fa-thumbs-up',
            'color': 'info'
        },
        'em_producao': {
            'name': 'Em Produção',
            'icon': 'fas fa-cogs',
            'color': 'primary'
        },
        'pronto': {
            'name': 'Prontos',
            'icon': 'fas fa-check-double',
            'color': 'success'
        },
        'entregue': {
            'name': 'Entregues',
            'icon': 'fas fa-check-circle',
            'color': 'success'
        }
    }

    # Validar status
    if status not in status_config:
        status = 'aprovado'

    # Garantir que a página seja pelo menos 1
    if page < 1:
        page = 1

    try:
        orders = Order.query.filter_by(status=status, approved=True).order_by(Order.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False
        )
    except Exception as e:
        # Em caso de erro na paginação, redirecionar para a primeira página
        flash('Erro na paginação. Redirecionando para a primeira página.', 'warning')
        return redirect(url_for('employee.status_orders', status=status, page=1))

    # Processar observações para cada pedido
    for order in orders.items:
        order.last_observations = list(order.observations)[-3:]

    config = status_config[status]

    return render_template('employee/status_orders.html', 
                         orders=orders, 
                         status=status,
                         status_name=config['name'],
                         status_icon=config['icon'],
                         status_color=config['color'],
                         today=date.today)

@employee_bp.route('/funcionario/pedidos/aprovados')
@login_required
@employee_required
def approved_orders():
    """Pedidos aprovados"""
    page = request.args.get('page', 1, type=int)

    # Garantir que a página seja pelo menos 1
    if page < 1:
        page = 1

    try:
        orders = Order.query.filter_by(status='aprovado', approved=True).order_by(Order.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False
        )
    except Exception as e:
        # Em caso de erro na paginação, redirecionar para a primeira página
        flash('Erro na paginação. Redirecionando para a primeira página.', 'warning')
        return redirect(url_for('employee.approved_orders', page=1))

    # Processar observações para cada pedido
    for order in orders.items:
        order.last_observations = list(order.observations)[-3:]

    return render_template('employee/status_orders.html', 
                         orders=orders, 
                         status='aprovado',
                         status_name='Aprovados',
                         status_icon='fas fa-check',
                         status_color='info',
                         today=date.today)

@employee_bp.route('/funcionario/pedidos/em-producao')
@login_required
@employee_required
def in_production_orders():
    """Pedidos em produção"""
    page = request.args.get('page', 1, type=int)

    # Garantir que a página seja pelo menos 1
    if page < 1:
        page = 1

    try:
        orders = Order.query.filter_by(status='em_producao', approved=True).order_by(Order.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False
        )
    except Exception as e:
        # Em caso de erro na paginação, redirecionar para a primeira página
        flash('Erro na paginação. Redirecionando para a primeira página.', 'warning')
        return redirect(url_for('employee.in_production_orders', page=1))

    # Processar observações para cada pedido
    for order in orders.items:
        order.last_observations = list(order.observations)[-3:]

    return render_template('employee/status_orders.html', 
                         orders=orders, 
                         status='em_producao',
                         status_name='Em Produção',
                         status_icon='fas fa-cogs',
                         status_color='primary',
                         today=date.today)

@employee_bp.route('/funcionario/pedidos/prontos')
@login_required
@employee_required
def ready_orders():
    """Pedidos prontos"""
    page = request.args.get('page', 1, type=int)

    # Garantir que a página seja pelo menos 1
    if page < 1:
        page = 1

    try:
        orders = Order.query.filter_by(status='pronto', approved=True).order_by(Order.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False
        )
    except Exception as e:
        # Em caso de erro na paginação, redirecionar para a primeira página
        flash('Erro na paginação. Redirecionando para a primeira página.', 'warning')
        return redirect(url_for('employee.ready_orders', page=1))

    # Processar observações para cada pedido
    for order in orders.items:
        order.last_observations = list(order.observations)[-3:]

    return render_template('employee/status_orders.html', 
                         orders=orders, 
                         status='pronto',
                         status_name='Prontos',
                         status_icon='fas fa-check-double',
                         status_color='success',
                         today=date.today)

@employee_bp.route('/funcionario/pedidos/entregues')
@login_required
@employee_required
def delivered_orders():
    """Pedidos entregues"""
    page = request.args.get('page', 1, type=int)

    # Apenas pedidos com status 'entregue' e que tenham data de entrega registrada
    orders = Order.query.filter(
        Order.status == 'entregue',
        Order.delivered_at.isnot(None),
        Order.approved == True
    ).order_by(Order.delivered_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )

    # Conta pedidos entregues no prazo
    on_time = sum(
        1 for o in orders.items
        if o.delivered_at and o.delivery_date >= o.delivered_at.date()
    )

    return render_template(
        'employee/delivered.html',
        orders=orders,
        on_time=on_time,
        now=datetime.now()
    )

@employee_bp.route('/funcionario/api/permissoes-status')
@login_required
@employee_required
def get_status_permissions():
    """API para obter permissões de status do funcionário atual"""
    from src.models.user import StatusPermission

    permissions = StatusPermission.query.filter_by(user_id=current_user.id).all()

    allowed_statuses = []
    for permission in permissions:
        if permission.can_change:
            allowed_statuses.append({
                'status': permission.status,
                'display_name': {
                    'aprovado': 'Aprovado',
                    'em_producao': 'Em Produção',
                    'pronto': 'Pronto',
                    'entregue': 'Entregue'
                }.get(permission.status, permission.status.title())
            })

    return jsonify({'allowed_statuses': allowed_statuses})

# Rota alternativa para compatibilidade com o template
@employee_bp.route('/funcionario/get_status_permissions')
@login_required
@employee_required
def get_status_permissions_alt():
    """Rota alternativa para permissões de status"""
    from src.models.user import StatusPermission

    permissions = StatusPermission.query.filter_by(user_id=current_user.id).all()

    allowed_statuses = []
    for permission in permissions:
        if permission.can_change:
            allowed_statuses.append({
                'status': permission.status,
                'display_name': {
                    'aprovado': 'Aprovado',
                    'em_producao': 'Em Produção',
                    'pronto': 'Pronto',
                    'entregue': 'Entregue'
                }.get(permission.status, permission.status.title())
            })

    return jsonify({'allowed_statuses': allowed_statuses})

@employee_bp.route('/funcionario/ordem-servico/<int:service_order_id>/download-files')
@login_required
@employee_required
def download_service_order_files(service_order_id):
    """Download de todos os arquivos da ordem de serviço em um ZIP"""
    from flask import send_file, current_app
    import os
    import zipfile
    import tempfile

    service_order = ServiceOrder.query.get_or_404(service_order_id)

    # Verificar se o funcionário tem acesso a esta ordem de serviço
    if current_user not in service_order.assigned_employees:
        flash('Você não tem acesso a esta ordem de serviço.', 'error')
        return redirect(url_for('employee.service_orders'))

    # Obter lista de arquivos
    files_list = service_order.get_files_list()

    if not files_list:
        flash('Esta ordem de serviço não possui arquivos.', 'error')
        return redirect(url_for('employee.service_order_detail', service_order_id=service_order_id))

    try:
        # Criar arquivo ZIP temporário
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')

        with zipfile.ZipFile(temp_zip.name, 'w') as zip_file:
            files_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'service_orders')

            for filename in files_list:
                file_path = os.path.join(files_dir, filename)
                if os.path.exists(file_path):
                    # Adicionar arquivo ao ZIP com nome limpo
                    zip_file.write(file_path, filename)

        # Nome do arquivo ZIP para download
        zip_filename = f"OS_{service_order_id}_{service_order.title.replace(' ', '_')}.zip"

        return send_file(
            temp_zip.name,
            as_attachment=True,
            download_name=zip_filename,
            mimetype='application/zip'
        )

    except Exception as e:
        flash('Erro ao criar arquivo ZIP.', 'error')
        return redirect(url_for('employee.service_order_detail', service_order_id=service_order_id))
    finally:
        # Limpar arquivo temporário após o download
        try:
            os.unlink(temp_zip.name)
        except:
            pass

@employee_bp.route('/funcionario/debug/permissoes')
@login_required
@employee_required
def debug_permissions():
    """Rota para debug das permissões do usuário"""
    from src.models.user import StatusPermission

    print(f"=== DEBUG PERMISSÕES ===")
    print(f"Usuário: {current_user.username} (ID: {current_user.id})")
    print(f"Tipo: {current_user.user_type}")
    print(f"Ativo: {current_user.is_active}")

    # Buscar todas as permissões do usuário
    all_permissions = StatusPermission.query.filter_by(user_id=current_user.id).all()
    print(f"Total de permissões encontradas: {len(all_permissions)}")

    for perm in all_permissions:
        print(f"  - Status: {perm.status}, Pode alterar: {perm.can_change}")

    # Verificar se o usuário não tem permissões, criar básicas
    if not all_permissions:
        print("Usuário sem permissões! Criando permissões básicas...")

        # Criar permissões básicas para funcionário
        basic_permissions = [
            ('aprovado', True),
            ('em_producao', True),
            ('pronto', True),
            ('entregue', False)  # Por padrão, funcionários não podem marcar como entregue
        ]

        for status, can_change in basic_permissions:
            permission = StatusPermission(
                user_id=current_user.id,
                status=status,
                can_change=can_change
            )
            db.session.add(permission)
            print(f"  Criada permissão: {status} = {can_change}")

        try:
            db.session.commit()
            print("Permissões criadas com sucesso!")
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao criar permissões: {e}")

    # Buscar novamente para confirmar
    updated_permissions = StatusPermission.query.filter_by(user_id=current_user.id).all()

    result = {
        'user_id': current_user.id,
        'username': current_user.username,
        'user_type': current_user.user_type,
        'is_active': current_user.is_active,
        'permissions_count': len(updated_permissions),
        'permissions': [
            {
                'status': p.status,
                'can_change': p.can_change,
                'created_at': p.created_at.isoformat() if p.created_at else None
            }
            for p in updated_permissions
        ]
    }

    return jsonify(result)