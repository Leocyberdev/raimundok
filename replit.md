# Sistema de Gestão de Pedidos

## Overview
Sistema completo de gestão de pedidos (Order Management System) desenvolvido em Flask com painéis diferenciados para administradores, funcionários e clientes. O sistema gerencia pedidos, ordens de serviço, notificações, calendário, estatísticas e permite que clientes acompanhem seus pedidos em tempo real.

## Current State
- ✅ Flask application running on port 5000
- ✅ PostgreSQL database configured (Helium)
- ✅ All dependencies installed
- ✅ Login system working with 3 user types (admin, employee, client)
- ✅ Admin and employee panels available
- ✅ Client panel fully functional
- ✅ File upload system configured
- ✅ Database migrations automated
- ✅ Customer management system (CRUD operations)

## Project Architecture

### Backend (Flask)
- **Framework**: Flask 3.1.1 with Flask-Login for authentication
- **Database**: SQLAlchemy ORM with PostgreSQL (production) / SQLite (development)
- **File Storage**: Local file uploads in `src/static/uploads/`
- **Templates**: Jinja2 templates with responsive design

### Key Components
1. **Authentication System** (`src/routes/auth.py`)
   - Login diferenciado para admin, funcionários e clientes
   - Sessões seguras com Flask-Login
   - Redirecionamento automático para painel apropriado

2. **Admin Panel** (`src/routes/admin.py`)
   - Dashboard, adicionar/gerenciar pedidos
   - Gestão de funcionários e clientes
   - Controle de status e configurações
   - Alocação de pedidos a clientes

3. **Employee Panel** (`src/routes/employee.py`)
   - Dashboard pessoal
   - Notificações em tempo real
   - Visualização de pedidos e calendário

4. **Client Panel** (`src/routes/client.py`) **[NOVO]**
   - Dashboard com visão geral dos pedidos
   - Acompanhamento de status em tempo real
   - Detalhes completos de cada pedido
   - Gerenciamento de perfil pessoal

5. **Database Models** (`src/models/user.py`)
   - User (admin/employee/client) - estendido com campos de contato
   - Order (pedidos) - com relacionamento opcional a cliente
   - ServiceOrder (ordens de serviço)
   - AuditLog (auditoria)
   - FileReference (referências de arquivos)

### Database Configuration
- **Production**: PostgreSQL via DATABASE_URL environment variable
- **Development**: SQLite in `src/database/app.db`
- Auto-detection via `src/database/config.py`

### Automatic Database Migrations
O sistema possui **migração automática de banco de dados** implementada em `src/main.py` (linhas 184-254):

1. **No startup, o sistema automaticamente:**
   - Cria todas as tabelas necessárias (`db.create_all()`)
   - Verifica se as colunas obrigatórias existem em cada tabela
   - **Adiciona automaticamente** qualquer coluna faltante via ALTER TABLE

2. **Colunas gerenciadas automaticamente:**
   - **Tabela `order`**: `is_urgent`, `subtitle`, `description`, `client_id`
   - **Tabela `user`**: `full_name` (usado como `cnpj`), `email`, `phone`, `address`, `profile_picture`
   - **Tabela `service_order`**: `file1_filename`, `file2_filename`, `file3_filename`

3. **Deployment para VPS PostgreSQL:**
   - ✅ Basta fazer `git pull` na VPS
   - ✅ O sistema detecta automaticamente o PostgreSQL via variável `DATABASE_URL`
   - ✅ Na primeira execução, todas as colunas serão criadas automaticamente
   - ✅ Não é necessário executar scripts SQL manualmente
   - ✅ Alterações futuras de schema serão aplicadas automaticamente

### Default Users
- **Admin**: `Nonato` / `123456`
- **Admin**: `Gleissa` / `123456`
- **Funcionários**: Criados pelo administrador
- **Clientes**: Criados pelo administrador com campos de contato (nome completo, email, telefone, endereço)

## Recent Changes
- 2025-11-16: **Atualização: Campo CNPJ da Empresa**
  - Substituído campo "Nome Completo" por "CNPJ da Empresa" em todos os formulários e templates
  - Campo `cnpj` no modelo User (reutiliza coluna `full_name` no banco para compatibilidade)
  - Máscaras automáticas aplicadas: CNPJ (00.000.000/0000-00) e Telefone
  - Atualização em: add_client.html, client_details.html, clients.html, add_order.html, profile.html, dashboard.html, base.html
  - Rotas atualizadas: admin.py e client.py agora usam campo `cnpj`

- 2025-11-12: **Sistema de Clientes Implementado**
  - Adicionado novo tipo de usuário 'cliente' com campos de contato
  - Criado painel completo para clientes (dashboard, pedidos, detalhes, perfil)
  - Implementado gerenciamento de clientes no painel admin (listar, adicionar, editar, excluir)
  - Adicionada seleção de cliente nos formulários de pedidos
  - Relacionamento Order-Cliente configurado no banco de dados
  - Migrations automáticas para novas colunas (client_id, full_name, email, phone, address)
  
- 2025-11-12: Imported from GitHub and configured for Replit
  - Configured port 5000 for webview
  - Fixed database initialization to work with PostgreSQL
  - Installed all Python dependencies
  - Created .gitignore for Python projects
  - Configured deployment with Gunicorn

## Dependencies
See `requirements.txt` for full list:
- Flask 3.1.1 (web framework)
- Flask-SQLAlchemy 3.1.1 (ORM)
- Flask-Login 0.6.3 (authentication)
- Pillow (image processing)
- psycopg2-binary (PostgreSQL driver)
- gunicorn (WSGI server for production)

## File Structure
```
/
├── src/
│   ├── main.py                 # Main application file
│   ├── database/
│   │   ├── config.py          # Database configuration
│   │   └── app.db             # SQLite database (dev)
│   ├── models/
│   │   └── user.py            # Database models
│   ├── routes/
│   │   ├── auth.py            # Authentication routes
│   │   ├── admin.py           # Admin panel routes
│   │   ├── employee.py        # Employee panel routes
│   │   ├── client.py          # Client panel routes [NEW]
│   │   └── user.py            # User API routes
│   ├── templates/             # Jinja2 templates
│   │   ├── admin/             # Admin templates
│   │   ├── employee/          # Employee templates
│   │   └── client/            # Client templates [NEW]
│   ├── static/                # Static files
│   │   ├── uploads/           # File uploads
│   │   ├── style.css
│   │   └── background_login.jpg
│   └── utils/
│       └── date_utils.py      # Date formatting utilities
├── requirements.txt           # Python dependencies
├── Procfile                   # Deployment command
└── .gitignore                 # Git ignore rules
```

## Running the Application
The application runs automatically via the configured workflow:
- **Development**: `python src/main.py` on port 5000
- **Production**: Gunicorn WSGI server on port 5000

## Features
- 🔐 Sistema de autenticação diferenciado (admin/funcionário/cliente)
- 👨‍💼 Painel administrativo completo
- 👷‍♂️ Painel do funcionário
- 👤 **Painel do cliente** (acompanhamento de pedidos em tempo real) **[NOVO]**
- 🏢 **Gerenciamento completo de clientes** (CRUD, campos de contato) **[NOVO]**
- 🔗 **Alocação de pedidos a clientes** **[NOVO]**
- 📝 Sistema de observações
- 🔔 Notificações em tempo real
- 📊 Calendário e estatísticas
- 📱 Design responsivo
- 🛡️ Segurança com senhas hasheadas
- 📈 Performance otimizada

## Environment Variables
- `DATABASE_URL`: PostgreSQL connection string (auto-configured)
- `PORT`: Server port (default: 5000)
- `SECRET_KEY`: Flask secret key (has default value)

## Notes
- The application automatically creates admin users on first run
- Database migrations run automatically on startup
- File uploads are stored in `src/static/uploads/`
- The app uses Brazilian Portuguese (pt-BR) for interface and dates
