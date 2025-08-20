from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from datetime import datetime, date
import os
from src.models.user import db, User, Order, OrderObservation, Notification, ServiceOrder
from datetime import date
import pytz
from src.utils.date_utils import get_delivery_status_text, get_weekday_name_pt


admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    """Decorator para verificar se o usuário é admin"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Acesso negado. Apenas administradores podem acessar esta página.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/admin')
@login_required
@admin_required
def dashboard():
    """Dashboard principal do admin"""
    # Estatísticas gerais (excluindo entregues do total)
    total_orders = Order.query.filter(Order.status != 'entregue').count()
    pending_orders = Order.query.filter_by(approved=False).count()
    in_production = Order.query.filter_by(status='em_producao').count()
    delivered_orders = Order.query.filter_by(status='entregue').count()

    # Pedidos recentes (excluindo entregues)
    recent_orders = Order.query.filter(Order.status != 'entregue').order_by(Order.created_at.desc()).limit(5).all()

    # Funcionários ativos
    employees = User.query.filter_by(user_type='funcionario', is_active=True).count()

    return render_template('admin/dashboard.html', 
                         total_orders=total_orders,
                         pending_orders=pending_orders,
                         in_production=in_production,
                         delivered_orders=delivered_orders,
                         recent_orders=recent_orders,
                         employees=employees)

@admin_bp.route('/admin/pedidos/adicionar', methods=['GET', 'POST'])
@login_required
@admin_required
def add_order():
    """Adicionar novo pedido"""
    if request.method == 'POST':
        try:
            company_name = request.form.get('company_name')
            subtitle = request.form.get('subtitle')
            description = request.form.get('description')
            order_date = datetime.strptime(request.form.get('order_date'), '%Y-%m-%d').date()
            delivery_date = datetime.strptime(request.form.get('delivery_date'), '%Y-%m-%d').date()

            # Upload da logo
            logo_filename = None
            if 'company_logo' in request.files:
                file = request.files['company_logo']
                if file and file.filename:
                    filename = secure_filename(file.filename)
                    # Adicionar timestamp para evitar conflitos
                    timestamp = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%Y%m%d_%H%M%S_")
                    logo_filename = timestamp + filename
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], logo_filename))

            # Criar pedido
            order = Order(
                company_name=company_name,
                subtitle=subtitle,
                description=description,
                company_logo=logo_filename,
                order_date=order_date,
                delivery_date=delivery_date,
                created_by_id=current_user.id
            )

            db.session.add(order)
            db.session.commit()

            flash('Pedido adicionado com sucesso!', 'success')
            return redirect(url_for('admin.orders'))

        except Exception as e:
            flash(f'Erro ao adicionar pedido: {str(e)}', 'error')

    # Preparar data/hora atual formatada para o template
    now = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%Y-%m-%dT%H:%M")  # formato para input datetime-local

    return render_template('admin/add_order.html', now=now)

@admin_bp.route('/admin/pedidos')
@login_required
@admin_required
def orders():
    """Lista de todos os pedidos (excluindo entregues)"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')

    # Garantir que a página seja pelo menos 1
    if page < 1:
        page = 1

    query = Order.query.filter(Order.status != 'entregue')
    if status_filter and status_filter != 'entregue':
        query = query.filter_by(status=status_filter)

    try:
        orders_pagination = query.order_by(Order.created_at.desc()).paginate(
            page=page, per_page=10, error_out=False)
    except Exception as e:
        # Em caso de erro na paginação, redirecionar para a primeira página
        flash('Erro na paginação. Redirecionando para a primeira página.', 'warning')
        return redirect(url_for('admin.orders', page=1, status=status_filter))

    # Adicionar informações de data calculadas para cada pedido
    orders_with_data = []
    for order in orders_pagination.items:
        order_data = {
            'order': order,
            'delivery_status': get_delivery_status_text(order.delivery_date)
        }
        orders_with_data.append(order_data)

    return render_template('admin/orders.html', 
                         orders=orders_pagination, 
                         orders_with_data=orders_with_data,
                         status_filter=status_filter)

@admin_bp.route('/admin/pedidos/<int:order_id>/aprovar', methods=['POST'])
@login_required
@admin_required
def approve_order(order_id):
    """Aprovar pedido"""
    order = Order.query.get_or_404(order_id)
    order.approved = True
    order.status = 'aprovado'

    # Notificar funcionários
    employees = User.query.filter_by(user_type='funcionario', is_active=True).all()
    for employee in employees:
        notification = Notification(
            user_id=employee.id,
            title='Novo pedido aprovado',
            message=f'O pedido da empresa {order.company_name} foi aprovado e está disponível para produção.'
        )
        db.session.add(notification)

    db.session.commit()
    flash('Pedido aprovado com sucesso!', 'success')
    return redirect(url_for('admin.orders'))

@admin_bp.route('/admin/pedidos/<int:order_id>/excluir', methods=['POST'])
@login_required
@admin_required
def delete_order(order_id):
    """Excluir pedido"""
    order = Order.query.get_or_404(order_id)

    # Remover arquivo de logo se existir
    if order.company_logo:
        logo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], order.company_logo)
        if os.path.exists(logo_path):
            os.remove(logo_path)

    db.session.delete(order)
    db.session.commit()
    flash('Pedido excluído com sucesso!', 'success')
    return redirect(url_for('admin.orders'))

@admin_bp.route('/admin/status')
@login_required
@admin_required
def status():
    """Gerenciar status dos pedidos"""
    orders = Order.query.filter_by(approved=True).order_by(Order.created_at.desc()).all()
    return render_template('admin/status.html', orders=orders)

@admin_bp.route('/admin/pedidos/<int:order_id>/status', methods=['POST'])
@login_required
@admin_required
def update_status(order_id):
    """Atualizar status do pedido"""
    from src.models.user import StatusHistory

    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    old_status = order.status

    # Registrar histórico de alteração
    status_history = StatusHistory(
        order_id=order_id,
        user_id=current_user.id,
        old_status=old_status,
        new_status=new_status
    )

    db.session.add(status_history)

    order.status = new_status

    if new_status == 'entregue':
        order.delivered_at = datetime.now(pytz.timezone("America/Sao_Paulo"))
        order.is_urgent = False

    db.session.commit()
    flash('Status atualizado com sucesso!', 'success')
    return redirect(url_for('admin.status'))

@admin_bp.route('/admin/pedidos/<int:order_id>/urgente', methods=['POST'])
@login_required
@admin_required
def toggle_urgent(order_id):
    """Marcar/desmarcar pedido como urgente"""
    order = Order.query.get_or_404(order_id)
    order.is_urgent = not order.is_urgent

    db.session.commit()

    status = 'marcado como urgente' if order.is_urgent else 'desmarcado como urgente'
    flash(f'Pedido {status} com sucesso!', 'success')

    # Retornar para a página anterior
    return redirect(request.referrer or url_for('admin.orders'))

@admin_bp.route('/admin/pedidos/<int:order_id>/status-rapido', methods=['POST'])
@login_required
@admin_required
def update_order_status_quick(order_id):
    """Atualizar status do pedido rapidamente"""
    from src.models.user import StatusHistory

    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    old_status = order.status

    if new_status not in ['aprovado', 'em_producao', 'pronto', 'entregue']:
        flash('Status inválido!', 'error')
        return redirect(request.referrer or url_for('admin.orders'))

    # Registrar histórico de alteração
    status_history = StatusHistory(
        order_id=order_id,
        user_id=current_user.id,
        old_status=old_status,
        new_status=new_status,
        created_at=datetime.now(pytz.timezone("America/Sao_Paulo"))
    )
    db.session.add(status_history)

    order.status = new_status

    # Ações específicas por status
    if new_status == 'entregue':
        order.delivered_at = datetime.now(pytz.timezone("America/Sao_Paulo"))
        order.is_urgent = False

        # Notificar funcionários sobre entrega
        employees = User.query.filter_by(user_type='funcionario', is_active=True).all()
        for employee in employees:
            notification = Notification(
                user_id=employee.id,
                title='Pedido Entregue',
                message=f'O pedido da empresa {order.company_name} foi entregue com sucesso.'
            )
            db.session.add(notification)

    db.session.commit()

    status_names = {
        'aprovado': 'aprovado',
        'em_producao': 'em produção', 
        'pronto': 'pronto',
        'entregue': 'entregue'
    }

    flash(f'Pedido marcado como {status_names[new_status]} com sucesso!', 'success')

    # Redirecionar baseado no novo status
    if new_status == 'entregue':
        return redirect(url_for('admin.delivered'))
    else:
        return redirect(request.referrer or url_for('admin.orders'))

@admin_bp.route('/admin/funcionarios')
@login_required
@admin_required
def employees():
    """Lista de funcionários"""
    employees = User.query.filter_by(user_type='funcionario').order_by(User.created_at.desc()).all()
    return render_template('admin/employees.html', employees=employees)

@admin_bp.route('/admin/funcionarios/adicionar', methods=['GET', 'POST'])
@login_required
@admin_required
def add_employee():
    """Adicionar funcionário"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Verificar se usuário já existe
        if User.query.filter_by(username=username).first():
            flash('Nome de usuário já existe!', 'error')
        else:
            employee = User(username=username, user_type='funcionario')
            employee.set_password(password)
            db.session.add(employee)
            db.session.commit()
            flash('Funcionário adicionado com sucesso!', 'success')
            return redirect(url_for('admin.employees'))

    return render_template('admin/add_employee.html')

@admin_bp.route('/admin/funcionarios/<int:employee_id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_employee(employee_id):
    """Ativar/desativar funcionário"""
    employee = User.query.get_or_404(employee_id)
    if employee.user_type != 'funcionario':
        flash('Operação não permitida!', 'error')
        return redirect(url_for('admin.employees'))

    employee.is_active = not employee.is_active
    db.session.commit()

    status = 'ativado' if employee.is_active else 'desativado'
    flash(f'Funcionário {status} com sucesso!', 'success')
    return redirect(url_for('admin.employees'))

@admin_bp.route('/admin/funcionarios/<int:employee_id>/promover-admin', methods=['POST'])
@login_required
@admin_required
def promote_to_admin(employee_id):
    """Promover funcionário a administrador"""
    employee = User.query.get_or_404(employee_id)

    if employee.user_type != 'funcionario':
        flash('Apenas funcionários podem ser promovidos a administrador!', 'error')
        return redirect(url_for('admin.employees'))

    # Confirmar se realmente quer promover
    if request.form.get('confirm') != 'true':
        flash('Confirmação necessária para promover funcionário!', 'error')
        return redirect(url_for('admin.employees'))

    # Promover funcionário
    employee.user_type = 'admin'
    employee.is_active = True  # Garantir que admin está ativo

    db.session.commit()

    flash(f'Funcionário {employee.username} foi promovido a administrador com sucesso!', 'success')
    return redirect(url_for('admin.employees'))

import pytz



@admin_bp.route('/admin/entregues')
@login_required
@admin_required
def delivered():
    """Pedidos entregues"""
    page = request.args.get('page', 1, type=int)

    # Apenas pedidos com status 'entregue' e que tenham data de entrega registrada
    orders = Order.query.filter(
        Order.status == 'entregue',
        Order.delivered_at.isnot(None)
    ).order_by(Order.delivered_at.desc()).paginate(
        page=page, per_page=10, error_out=False
    )

    # Conta pedidos entregues no prazo
    on_time = sum(
        1 for o in orders.items
        if o.delivered_at and o.delivery_date >= o.delivered_at.date()
    )

    return render_template(
        'admin/delivered.html',
        orders=orders,
        on_time=on_time,
        now=datetime.now()
    )


@admin_bp.route('/admin/configuracoes')
@login_required
@admin_required
def settings():
    """Configurações do admin"""
    return render_template('admin/settings.html')

@admin_bp.route('/admin/configuracoes/senha', methods=['POST'])
@login_required
@admin_required
def change_password():
    """Alterar senha do admin"""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')

    if not current_user.check_password(current_password):
        flash('Senha atual incorreta!', 'error')
    elif new_password != confirm_password:
        flash('Nova senha e confirmação não coincidem!', 'error')
    else:
        current_user.set_password(new_password)
        db.session.commit()
        flash('Senha alterada com sucesso!', 'success')

    return redirect(url_for('admin.settings'))

@admin_bp.route('/admin/calendario')
@login_required
@admin_required
def calendar():
    """Calendário de pedidos"""
    return render_template('admin/calendar.html')

@admin_bp.route('/admin/api/calendario')
@login_required
@admin_required
def calendar_api():
    """API para dados do calendário do admin"""
    orders = Order.query.filter(Order.status != 'entregue').all()
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

# Em src/routes/admin.py

from sqlalchemy import func, extract
# Não precisa mais importar o db aqui se ele já estiver disponível globalmente

@admin_bp.route('/admin/estatisticas')
@login_required
@admin_required
def statistics():
    """Estatísticas do sistema"""
    from sqlalchemy import func, extract

    # Estatísticas básicas
    total_orders = Order.query.filter_by(approved=True).count()
    in_production = Order.query.filter_by(status='em_producao', approved=True).count()
    completed = Order.query.filter_by(status='entregue', approved=True).count()

    # Pedidos por mês
    monthly_orders_rows = db.session.query(
        extract('month', Order.created_at).label('month'),
        func.count(Order.id).label('count')
    ).filter_by(approved=True).group_by(extract('month', Order.created_at)).order_by(extract('month', Order.created_at)).all()

    # Pedidos por status
    status_counts_rows = db.session.query(
        Order.status,
        func.count(Order.id).label('count')
    ).filter_by(approved=True).group_by(Order.status).all()

    # Converta os resultados do tipo Row para dicionários
    monthly_orders_data = [{'month': row.month, 'count': row.count} for row in monthly_orders_rows]
    status_counts_data = [{'status': row.status, 'count': row.count} for row in status_counts_rows]

    return render_template(
        'admin/statistics.html', 
        total_orders=total_orders,
        in_production=in_production,
        completed=completed,
        monthly_orders=monthly_orders_data,
        status_counts=status_counts_data
    )




# ===== ROTAS PARA ORDEM DE SERVIÇO =====

@admin_bp.route('/admin/ordem-servico')
@login_required
@admin_required
def service_orders():
    """Lista todos os pedidos para criar ordens de serviço"""
    page = request.args.get('page', 1, type=int)
    per_page = 10

    # Buscar todos os pedidos
    orders = Order.query.order_by(Order.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    # Buscar ordens de serviço existentes
    existing_service_orders = ServiceOrder.query.all()
    service_orders_by_order = {so.order_id: so for so in existing_service_orders}

    return render_template('admin/service_orders.html', 
                         orders=orders,
                         service_orders_by_order=service_orders_by_order)

@admin_bp.route('/admin/ordem-servico/criar/<int:order_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def create_service_order(order_id):
    """Criar ordem de serviço para um pedido específico"""
    order = Order.query.get_or_404(order_id)

    # Verificar se já existe uma ordem de serviço para este pedido
    existing_service_order = ServiceOrder.query.filter_by(order_id=order_id).first()

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        selected_employees = request.form.getlist('employees')

        if not title:
            flash('Título é obrigatório.', 'error')
            return redirect(url_for('admin.create_service_order', order_id=order_id))

        # Upload do PDF
        pdf_filename = None
        if 'pdf_file' in request.files:
            file = request.files['pdf_file']
            if file and file.filename and (file.filename.lower().endswith(('.pdf', '.cdr', '.dxf', '.zip', '.rar', '.xls', '.xlsx', '.ia', '.pptx')) or file.content_type in ['application/pdf', 'application/x-coreldraw', 'image/vnd.dxf', 'application/zip', 'application/x-rar-compressed', 'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'application/illustrator', 'application/vnd.openxmlformats-officedocument.presentationml.presentation']):
                filename = secure_filename(file.filename)
                # Adicionar timestamp para evitar conflitos
                timestamp = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%Y%m%d_%H%M%S_")
                pdf_filename = timestamp + filename

                # Criar diretório para PDFs se não existir
                pdf_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'service_orders')
                os.makedirs(pdf_dir, exist_ok=True)

                file_path = os.path.join(pdf_dir, pdf_filename)
                file.save(file_path)

        # Criar ou atualizar ordem de serviço
        if existing_service_order:
            service_order = existing_service_order
            service_order.title = title
            service_order.description = description
            if pdf_filename:
                service_order.pdf_filename = pdf_filename
        else:
            service_order = ServiceOrder(
                order_id=order_id,
                title=title,
                description=description,
                pdf_filename=pdf_filename,
                created_by_id=current_user.id
            )
            db.session.add(service_order)

        # Limpar funcionários anteriores e adicionar novos
        service_order.assigned_employees.clear()

        # Adicionar funcionários selecionados
        for emp_id in selected_employees:
            employee = User.query.get(int(emp_id))
            if employee and employee.is_employee():
                service_order.assigned_employees.append(employee)

                # Criar notificação para o funcionário
                notification = Notification(
                    user_id=employee.id,
                    title='Nova Ordem de Serviço',
                    message=f'Você recebeu uma nova ordem de serviço: {title}'
                )
                db.session.add(notification)

        db.session.commit()
        flash('Ordem de serviço criada/atualizada com sucesso!', 'success')
        return redirect(url_for('admin.service_orders'))

    # GET request - mostrar formulário
    employees = User.query.filter_by(user_type='funcionario', is_active=True).all()

    return render_template('admin/create_service_order.html', 
                         order=order,
                         employees=employees,
                         existing_service_order=existing_service_order)

@admin_bp.route('/admin/ordem-servico/detalhes/<int:service_order_id>')
@login_required
@admin_required
def service_order_details(service_order_id):
    """Visualizar detalhes de uma ordem de serviço"""
    service_order = ServiceOrder.query.get_or_404(service_order_id)

    return render_template('admin/service_order_details.html', 
                         service_order=service_order)

@admin_bp.route('/admin/ordem-servico/excluir/<int:service_order_id>', methods=['POST'])
@login_required
@admin_required
def delete_service_order(service_order_id):
    """Excluir uma ordem de serviço"""
    service_order = ServiceOrder.query.get_or_404(service_order_id)

    # Remover arquivo PDF se existir
    if service_order.pdf_filename:
        pdf_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'service_orders', service_order.pdf_filename)
        if os.path.exists(pdf_path):
            os.remove(pdf_path)

    db.session.delete(service_order)
    db.session.commit()

    flash('Ordem de serviço excluída com sucesso!', 'success')
    return redirect(url_for('admin.service_orders'))


import pytz



@admin_bp.route('/admin/pedidos/detalhes/<int:order_id>')
@login_required
@admin_required
def order_details(order_id):
    """Visualizar detalhes de um pedido"""
    from src.models.user import StatusHistory, DeliveryOption

    order = Order.query.get_or_404(order_id)

    # Buscar observações do pedido
    observations = OrderObservation.query.filter_by(order_id=order_id).order_by(OrderObservation.created_at.desc()).all()

    # Buscar histórico de status
    status_history = StatusHistory.query.filter_by(order_id=order_id).order_by(StatusHistory.created_at.desc()).all()

    # Buscar opções de entrega (se existirem)
    delivery_options = DeliveryOption.query.filter_by(order_id=order_id).order_by(DeliveryOption.created_at.desc()).all()

    # Calcular informações de data
    order_data = {
        'delivery_status': get_delivery_status_text(order.delivery_date),
        'weekday_name': get_weekday_name_pt(order.order_date)
    }

    return render_template('admin/order_detail.html', 
                         order=order, 
                         observations=observations,
                         status_history=status_history,
                         delivery_options=delivery_options,
                         order_data=order_data)

@admin_bp.route('/admin/pedidos/<int:order_id>/observacao', methods=['POST'])
@login_required
@admin_required
def add_observation(order_id):
    """Adicionar observação a um pedido"""
    order = Order.query.get_or_404(order_id)

    content = request.form.get('observation', '').strip()
    if not content:
        flash('O conteúdo da observação não pode estar vazio.', 'error')
        return redirect(request.referrer or url_for('admin.orders'))

    observation = OrderObservation(
        order_id=order_id,
        author_id=current_user.id,
        content=content
    )

    db.session.add(observation)
    db.session.commit()

    flash('Observação adicionada com sucesso!', 'success')
    return redirect(request.referrer or url_for('admin.orders'))

@admin_bp.route('/admin/pedidos/detalhes/<int:order_id>/atualizar-status', methods=['POST'])
@login_required
@admin_required
def update_order_status_detail(order_id):
    """Atualizar status do pedido na página de detalhes"""
    from src.models.user import StatusHistory

    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status')
    old_status = order.status

    # Registrar histórico de alteração
    status_history = StatusHistory(
        order_id=order_id,
        user_id=current_user.id,
        old_status=old_status,
        new_status=new_status
    )

    db.session.add(status_history)

    order.status = new_status

    if new_status == 'entregue':
        order.delivered_at = datetime.now(pytz.timezone("America/Sao_Paulo"))
        order.is_urgent = False

    db.session.commit()
    flash('Status atualizado com sucesso!', 'success')
    return redirect(url_for('admin.order_details', order_id=order_id))

@admin_bp.route('/admin/pedidos/editar/<int:order_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_order(order_id):
    """Editar um pedido existente"""
    order = Order.query.get_or_404(order_id)

    if request.method == 'POST':
        try:
            order.company_name = request.form.get('company_name')
            order.subtitle = request.form.get('subtitle')
            order.description = request.form.get('description')
            order.order_date = datetime.strptime(request.form.get('order_date'), '%Y-%m-%d').date()
            order.delivery_date = datetime.strptime(request.form.get('delivery_date'), '%Y-%m-%d').date()
            order.status = request.form.get('status')
            order.approved = True if request.form.get('approved') == 'on' else False

            # Lidar com o upload da nova logo
            if 'company_logo' in request.files:
                file = request.files['company_logo']
                if file and file.filename:
                    # Remover logo antiga se existir
                    if order.company_logo:
                        old_logo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], order.company_logo)
                        if os.path.exists(old_logo_path):
                            os.remove(old_logo_path)

                    filename = secure_filename(file.filename)
                    timestamp = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%Y%m%d_%H%M%S_")
                    logo_filename = timestamp + filename
                    file.save(os.path.join(current_app.config['UPLOAD_FOLDER'], logo_filename))
                    order.company_logo = logo_filename

            db.session.commit()
            flash('Pedido atualizado com sucesso!', 'success')
            return redirect(url_for('admin.orders'))

        except Exception as e:
            flash(f'Erro ao atualizar pedido: {str(e)}', 'error')

    return render_template('admin/edit_order.html', order=order)

# ===== ROTAS PARA PEDIDOS POR STATUS =====

@admin_bp.route('/admin/pedidos/status')
@login_required
@admin_required
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
        return redirect(url_for('admin.status_orders', status=status, page=1))

    # Processar observações para cada pedido
    for order in orders.items:
        order.last_observations = list(order.observations)[-3:]

    config = status_config[status]

    return render_template('admin/status_orders.html', 
                         orders=orders, 
                         status=status,
                         status_name=config['name'],
                         status_icon=config['icon'],
                         status_color=config['color'],
                         today=date.today)

@admin_bp.route('/admin/pedidos/aprovados')
@login_required
@admin_required
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
        return redirect(url_for('admin.approved_orders', page=1))

    # Processar observações para cada pedido
    for order in orders.items:
        order.last_observations = list(order.observations)[-3:]

    return render_template('admin/status_orders.html', 
                         orders=orders, 
                         status='aprovado',
                         status_name='Aprovados',
                         status_icon='fas fa-check',
                         status_color='info',
                         today=date.today)

@admin_bp.route('/admin/pedidos/em-producao')
@login_required
@admin_required
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
        return redirect(url_for('admin.in_production_orders', page=1))

    # Processar observações para cada pedido
    for order in orders.items:
        order.last_observations = list(order.observations)[-3:]

    return render_template('admin/status_orders.html', 
                         orders=orders, 
                         status='em_producao',
                         status_name='Em Produção',
                         status_icon='fas fa-cogs',
                         status_color='primary',
                         today=date.today)

@admin_bp.route('/admin/pedidos/prontos')
@login_required
@admin_required
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
        return redirect(url_for('admin.ready_orders', page=1))

    # Processar observações para cada pedido
    for order in orders.items:
        order.last_observations = list(order.observations)[-3:]

    return render_template('admin/status_orders.html', 
                         orders=orders, 
                         status='pronto',
                         status_name='Prontos',
                         status_icon='fas fa-check-double',
                         status_color='success',
                         today=date.today)

# ===== ROTAS PARA GERENCIAMENTO DE PERMISSÕES DE STATUS =====

@admin_bp.route('/admin/gerenciar-status')
@login_required
@admin_required
def manage_status_permissions():
    """Gerenciar permissões de status dos funcionários"""
    from src.models.user import StatusPermission

    # Buscar todos os funcionários ativos
    employees = User.query.filter_by(user_type='funcionario', is_active=True).all()

    # Status disponíveis
    available_statuses = ['aprovado', 'em_producao', 'pronto', 'entregue']

    # Buscar permissões existentes
    permissions = {}
    for employee in employees:
        permissions[employee.id] = {}
        for status in available_statuses:
            permission = StatusPermission.query.filter_by(user_id=employee.id, status=status).first()
            permissions[employee.id][status] = permission.can_change if permission else False

    return render_template('admin/manage_status_permissions.html', 
                         employees=employees, 
                         available_statuses=available_statuses,
                         permissions=permissions)

@admin_bp.route('/admin/gerenciar-status/atualizar', methods=['POST'])
@login_required
@admin_required
def update_status_permissions():
    """Atualizar permissões de status dos funcionários"""
    from src.models.user import StatusPermission

    try:
        # Obter dados do formulário
        employee_id = request.form.get('employee_id')
        status = request.form.get('status')
        can_change = request.form.get('can_change') == 'true'

        if not employee_id or not status:
            return jsonify({'success': False, 'message': 'Dados inválidos'})

        # Verificar se o funcionário existe
        employee = User.query.filter_by(id=employee_id, user_type='funcionario').first()
        if not employee:
            return jsonify({'success': False, 'message': 'Funcionário não encontrado'})

        # Buscar ou criar permissão
        permission = StatusPermission.query.filter_by(user_id=employee_id, status=status).first()
        if permission:
            permission.can_change = can_change
        else:
            permission = StatusPermission(user_id=employee_id, status=status, can_change=can_change)
            db.session.add(permission)

        db.session.commit()

        return jsonify({
            'success': True, 
            'message': f'Permissão {"habilitada" if can_change else "desabilitada"} para {employee.username} - {status}'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Erro ao atualizar permissão: {str(e)}'})

@admin_bp.route("/configuracoes/limpar_dados", methods=["POST"])
@login_required
@admin_required
def clear_system_data():
    try:
        from src.models.user import StatusPermission, StatusHistory, DeliveryOption
        
        # Desativar temporariamente o modo de verificação de chave estrangeira
        db.session.execute(db.text("PRAGMA foreign_keys = OFF"))

        # Limpar dados de todas as tabelas relevantes
        # Ordem de exclusão é importante devido a chaves estrangeiras
        
        # 1. Limpar tabelas de associação primeiro
        db.session.execute(db.text("DELETE FROM service_order_employees"))
        
        # 2. Limpar tabelas dependentes
        Notification.query.delete()
        OrderObservation.query.delete()
        StatusHistory.query.delete()
        StatusPermission.query.delete()
        DeliveryOption.query.delete()
        ServiceOrder.query.delete()
        
        # 3. Limpar pedidos
        Order.query.delete()
        
        # 4. Manter apenas usuários administradores
        User.query.filter(User.user_type != 'admin').delete()

        db.session.commit()

        # Reativar o modo de verificação de chave estrangeira
        db.session.execute(db.text("PRAGMA foreign_keys = ON"))

        flash("Todos os dados do sistema (exceto usuários administradores) foram limpos com sucesso!", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Erro ao limpar dados do sistema: {str(e)}", "error")
    return redirect(url_for("admin.settings"))




# ===== FUNCIONALIDADE DE BACKUP DO SISTEMA =====

import zipfile
import shutil
import tempfile
from flask import send_file

@admin_bp.route('/admin/backup-sistema', methods=['POST'])
@login_required
@admin_required
def backup_system():
    """Criar backup completo do sistema"""
    try:
        # Criar diretório temporário para o backup
        with tempfile.TemporaryDirectory() as temp_dir:
            backup_dir = os.path.join(temp_dir, 'backup_sistema')
            os.makedirs(backup_dir, exist_ok=True)
            
            # Nome do arquivo de backup com timestamp
            timestamp = datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%Y%m%d_%H%M%S")
            backup_filename = f"backup_sistema_{timestamp}.zip"
            backup_path = os.path.join(temp_dir, backup_filename)
            
            # Criar arquivo ZIP
            with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                
                # 1. Backup do banco de dados SQLite (se existir)
                from src.database.config import get_database_config, is_production
                
                if not is_production():
                    # Ambiente de desenvolvimento - backup do SQLite
                    config = get_database_config()
                    db_uri = config['SQLALCHEMY_DATABASE_URI']
                    if db_uri.startswith('sqlite:///'):
                        db_path = db_uri.replace('sqlite:///', '')
                        if os.path.exists(db_path):
                            zipf.write(db_path, 'database/app.db')
                            print(f"Banco de dados SQLite incluído no backup: {db_path}")
                        else:
                            print("Banco de dados SQLite não encontrado")
                else:
                    # Ambiente de produção - criar dump do PostgreSQL
                    # Nota: Em produção, seria necessário usar pg_dump
                    # Por enquanto, apenas registramos que é produção
                    info_content = f"""BACKUP DO SISTEMA - {timestamp}

Ambiente: Produção (PostgreSQL)
Data/Hora: {datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M:%S")}

NOTA: Este backup contém apenas os arquivos de upload.
Para backup completo do banco PostgreSQL, use ferramentas específicas como pg_dump.
"""
                    zipf.writestr('backup_info.txt', info_content)
                
                # 2. Backup dos arquivos de upload
                upload_folder = current_app.config.get('UPLOAD_FOLDER')
                if upload_folder and os.path.exists(upload_folder):
                    for root, dirs, files in os.walk(upload_folder):
                        for file in files:
                            file_path = os.path.join(root, file)
                            # Caminho relativo dentro do ZIP
                            arcname = os.path.join('uploads', os.path.relpath(file_path, upload_folder))
                            zipf.write(file_path, arcname)
                    print(f"Arquivos de upload incluídos no backup: {upload_folder}")
                
                # 3. Backup dos arquivos de configuração (opcional)
                src_dir = os.path.dirname(os.path.dirname(__file__))  # diretório src
                config_files = ['main.py']
                
                for config_file in config_files:
                    config_path = os.path.join(src_dir, config_file)
                    if os.path.exists(config_path):
                        zipf.write(config_path, f'config/{config_file}')
                
                # 4. Adicionar informações do backup
                backup_info = f"""BACKUP DO SISTEMA RAIMUNDO ACRÍLICOS
Data/Hora: {datetime.now(pytz.timezone("America/Sao_Paulo")).strftime("%d/%m/%Y %H:%M:%S")}
Versão: 1.0.0
Usuário: {current_user.username}

CONTEÚDO DO BACKUP:
- Banco de dados (SQLite ou informações sobre PostgreSQL)
- Arquivos de upload (logos, PDFs, etc.)
- Arquivos de configuração

INSTRUÇÕES PARA RESTAURAÇÃO:
1. Extrair o arquivo ZIP
2. Restaurar o banco de dados na pasta database/
3. Restaurar os arquivos de upload na pasta static/uploads/
4. Verificar configurações no arquivo main.py

IMPORTANTE: Este backup foi gerado automaticamente pelo sistema.
Mantenha este arquivo em local seguro.
"""
                zipf.writestr('LEIA-ME.txt', backup_info)
            
            # Retornar o arquivo para download
            return send_file(
                backup_path,
                as_attachment=True,
                download_name=backup_filename,
                mimetype='application/zip'
            )
            
    except Exception as e:
        flash(f'Erro ao criar backup: {str(e)}', 'error')
        return redirect(url_for('admin.settings'))


