from flask_sqlalchemy import SQLAlchemy



from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import pytz

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    user_type = db.Column(db.String(20), nullable=False)  # 'admin' ou 'funcionario'
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(pytz.timezone("America/Sao_Paulo"))
    )
    profile_picture = db.Column(db.String(200), nullable=True)  # Nome do arquivo da foto de perfil
    is_active = db.Column(db.Boolean, default=True)    
    # Relacionamentos
    orders_created = db.relationship('Order', foreign_keys='Order.created_by_id', backref='created_by', lazy='dynamic')
    
    
    observations = db.relationship('OrderObservation', back_populates='author', foreign_keys='OrderObservation.author_id', lazy='dynamic')


    status_permissions = db.relationship('StatusPermission', backref='user', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.user_type == 'admin'

    def is_employee(self):
        return self.user_type == 'funcionario'

    def __repr__(self):
        return f'<User {self.username}>'

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'user_type': self.user_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'profile_picture': self.profile_picture
        }

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(200), nullable=False)
    subtitle = db.Column(db.String(300))
    description = db.Column(db.Text)
    company_logo = db.Column(db.String(200))
    order_date = db.Column(db.Date, nullable=False)
    delivery_date = db.Column(db.Date, nullable=False)
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(pytz.timezone("America/Sao_Paulo"))
    )
    status = db.Column(db.String(50), default='pendente')
    approved = db.Column(db.Boolean, default=False)
    delivered_at = db.Column(db.DateTime)
    is_urgent = db.Column(db.Boolean, default=False)

    # ==================================================================
    # RELACIONAMENTOS CORRIGIDOS E CENTRALIZADOS
    # ==================================================================
    # Quando um Order é deletado, todos os registros filhos abaixo
    # também serão deletados automaticamente pelo banco de dados.

    # Relacionamento com OrderObservation (já estava correto)
    observations = db.relationship('OrderObservation', backref='order', lazy='dynamic', cascade='all, delete-orphan')

    # Relacionamento com ServiceOrder (NOVO)
    service_orders = db.relationship('ServiceOrder', backref='order', lazy='dynamic', cascade='all, delete-orphan')

    # Relacionamento com StatusHistory (NOVO)
    status_history = db.relationship('StatusHistory', backref='order', lazy='dynamic', cascade='all, delete-orphan')

    # Relacionamento com DeliveryOption (NOVO)
    delivery_options = db.relationship('DeliveryOption', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    # ==================================================================

    def __repr__(self):
        return f'<Order {self.company_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'company_name': self.company_name,
            'subtitle': self.subtitle,
            'description': self.description,
            'company_logo': self.company_logo,
            'order_date': self.order_date.isoformat() if self.order_date else None,
            'delivery_date': self.delivery_date.isoformat() if self.delivery_date else None,
            'created_by': self.created_by.username if self.created_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'status': self.status,
            'approved': self.approved,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'is_urgent': self.is_urgent
        }


class OrderObservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(pytz.timezone("America/Sao_Paulo"))
            )
    author = db.relationship('User', back_populates='observations')

    def __repr__(self):
                return f'<OrderObservation {self.id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'author': self.author.username if self.author else None,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(pytz.timezone("America/Sao_Paulo"))
    )


    def __repr__(self):
        return f'<Notification {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'message': self.message,
            'read': self.read,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# Tabela de associação entre ServiceOrder e funcionários
service_order_employees = db.Table('service_order_employees',
    db.Column('service_order_id', db.Integer, db.ForeignKey('service_order.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True)
)

class ServiceOrder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file1_filename = db.Column(db.String(200))  # primeiro arquivo
    file2_filename = db.Column(db.String(200))  # segundo arquivo
    file3_filename = db.Column(db.String(200))  # terceiro arquivo
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(pytz.timezone("America/Sao_Paulo"))
    )
    status = db.Column(db.String(50), default='ativa')  # ativa, concluida, cancelada

    # Relacionamentos
    created_by = db.relationship('User', foreign_keys=[created_by_id], backref='service_orders_created')
    assigned_employees = db.relationship('User', secondary=service_order_employees, 
                                       backref=db.backref('assigned_service_orders', lazy='dynamic'))

    def __repr__(self):
        return f'<ServiceOrder {self.title}>'

    def get_files_list(self):
        """Retorna lista de arquivos não nulos"""
        files = []
        if self.file1_filename:
            files.append(self.file1_filename)
        if self.file2_filename:
            files.append(self.file2_filename)
        if self.file3_filename:
            files.append(self.file3_filename)
        return files

    def get_files_list_with_size(self):
        """Retorna lista de arquivos com nome e tamanho"""
        from flask import current_app
        import os
        files_with_size = []
        files_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'service_orders')
        for filename in self.get_files_list():
            file_path = os.path.join(files_dir, filename)
            if os.path.exists(file_path):
                size = os.path.getsize(file_path)
                files_with_size.append({'filename': filename, 'size': size})
        return files_with_size

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'title': self.title,
            'description': self.description,
            'file1_filename': self.file1_filename,
            'file2_filename': self.file2_filename,
            'file3_filename': self.file3_filename,
            'created_by': self.created_by.username if self.created_by else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'status': self.status,
            'assigned_employees': [emp.username for emp in self.assigned_employees]
        }


class StatusPermission(db.Model):
    """Modelo para gerenciar permissões de status por funcionário"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(db.String(50), nullable=False)  # aprovado, em_producao, pronto, entregue
    can_change = db.Column(db.Boolean, default=False)
    created_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(pytz.timezone("America/Sao_Paulo"))
    )

    # Constraint para evitar duplicatas
    __table_args__ = (db.UniqueConstraint('user_id', 'status', name='unique_user_status'),)

    def __repr__(self):
        return f'<StatusPermission {self.user.username if self.user else "Unknown"} - {self.status}: {self.can_change}>'

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'status': self.status,
            'can_change': self.can_change,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class StatusHistory(db.Model):
    """Modelo para registrar histórico de alterações de status"""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    old_status = db.Column(db.String(50))  # Status anterior
    new_status = db.Column(db.String(50), nullable=False)  # Novo status
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone("America/Sao_Paulo")))

    # Relacionamentos
    user = db.relationship('User', backref='status_history_entries')

    def __repr__(self):
        return f'<StatusHistory {self.order_id}: {self.old_status} -> {self.new_status}>'

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'user': self.user.username if self.user else None,
            'old_status': self.old_status,
            'new_status': self.new_status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class DeliveryOption(db.Model):
    """Modelo para opções de entrega"""
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    fonte = db.Column(db.Boolean, default=False)
    gabarito = db.Column(db.Boolean, default=False)
    com_pistao = db.Column(db.Boolean, default=False)
    placa_cristal = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(pytz.timezone("America/Sao_Paulo")))
    created_by_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relacionamentos
    created_by = db.relationship('User', backref='delivery_options_created')

    def __repr__(self):
        return f'<DeliveryOption {self.order_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'order_id': self.order_id,
            'fonte': self.fonte,
            'gabarito': self.gabarito,
            'com_pistao': self.com_pistao,
            'placa_cristal': self.placa_cristal,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'created_by': self.created_by.username if self.created_by else None
        }

    def get_selected_options(self):
        """Retorna lista das opções selecionadas"""
        options = []
        if self.fonte:
            options.append('Fonte')
        if self.gabarito:
            options.append('Gabarito')
        if self.com_pistao:
            options.append('Com Pistão')
        if self.placa_cristal:
            options.append('Placa Cristal')
        return options

    def has_any_option_selected(self):
        """Verifica se pelo menos uma opção foi selecionada"""
        return any([self.fonte, self.gabarito, self.com_pistao, self.placa_cristal])


