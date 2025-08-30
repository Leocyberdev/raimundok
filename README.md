# Sistema de Gestão de Pedidos

Sistema completo de gestão de pedidos desenvolvido em Flask + Jinja2 com funcionalidades responsivas e painéis diferenciados para administradores e funcionários.

## 🚀 Funcionalidades

### 🔐 Sistema de Autenticação
- Login diferenciado para admin e funcionários com imagem de fundo personalizada
- Redirecionamento automático baseado no tipo de usuário
- Sessões seguras com Flask-Login

### 👨‍💼 Painel Administrativo
- **Dashboard**: Visão geral com estatísticas dos pedidos
- **Adicionar Pedidos**: Formulário completo com upload de foto da empresa
- **Gerenciar Pedidos**: Lista, aprovação e exclusão de pedidos
- **Status**: Controle de status (Em Produção, Pronto, Entregue)
- **Funcionários**: Cadastro e gestão de funcionários
- **Pedidos Entregues**: Histórico completo de entregas
- **Calendário**: Visualização de prazos e entregas
- **Estatísticas**: Gráficos e relatórios detalhados
- **Configurações**: Alterar senha e configurações do sistema

### 👷‍♂️ Painel do Funcionário
- **Dashboard**: Pedidos em produção e estatísticas pessoais
- **Notificações**: Sistema de notificações em tempo real
- **Pedidos**: Lista de pedidos aprovados para produção
- **Calendário**: Visualização de prazos e entregas
- **Estatísticas**: Métricas de performance pessoal
- **Perfil**: Informações da conta e preferências

### 📝 Sistema de Observações
- Funcionários e admins podem adicionar observações aos pedidos
- Histórico completo de observações
- Interface responsiva para mobile

### 🔔 Sistema de Notificações
- Notificações automáticas para novos pedidos aprovados
- Marcação de lidas/não lidas
- Interface moderna com diferentes tipos de notificação

### 📊 Calendário e Estatísticas
- Calendário interativo com filtros
- Gráficos de performance
- Estatísticas em tempo real
- Relatórios exportáveis

## 🛠️ Tecnologias Utilizadas

- **Backend**: Flask, SQLAlchemy, Flask-Login
- **Frontend**: HTML5, CSS3, JavaScript, Bootstrap 5
- **Banco de Dados**: SQLite (desenvolvimento) / PostgreSQL (produção)
- **Gráficos**: Chart.js
- **Calendário**: FullCalendar
- **Ícones**: Font Awesome
- **Deploy**: Render

## 📋 Pré-requisitos

- Python 3.11+
- pip (gerenciador de pacotes Python)

## 🚀 Instalação e Execução Local

1. **Clone ou acesse o diretório do projeto**:
   ```bash
   cd sistema-pedidos-fixed
   ```

2. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Execute o sistema**:
   ```bash
   python src/main.py
   ```

4. **Acesse o sistema**:
   - Abra seu navegador e vá para: `http://localhost:5003`

## 🌐 Deploy no Render

Para deploy em produção no Render, consulte o arquivo `DEPLOY_RENDER.md` para instruções detalhadas.

### Configuração de Banco de Dados
- **Desenvolvimento Local**: SQLite (arquivo `src/database/app.db`)
- **Produção (Render)**: PostgreSQL (configurado via `DATABASE_URL`)
- A aplicação detecta automaticamente o ambiente

## 👥 Usuários Padrão

### Administradores
- **Usuário**: `Nonato` | **Senha**: `123456`
- **Usuário**: `Gleissa` | **Senha**: `123456`

### Funcionários
- Criados pelo administrador através do painel admin

## 📱 Responsividade

O sistema foi desenvolvido com design responsivo, funcionando perfeitamente em:
- 💻 Desktop
- 📱 Tablets
- 📱 Smartphones

## 🎨 Design

- Interface moderna e intuitiva
- Tela de login com imagem de fundo personalizada
- Cores e gradientes profissionais
- Animações suaves
- Feedback visual para ações do usuário
- Dark sidebar com navegação clara

## 📂 Estrutura do Projeto

```
sistema-pedidos-fixed/
├── src/
│   ├── main.py              # Arquivo principal
│   ├── database/
│   │   └── config.py        # Configuração de banco de dados
│   ├── models/
│   │   ├── user.py          # Modelo de usuário
│   │   ├── order.py         # Modelo de pedido
│   │   └── observation.py   # Modelo de observação
│   ├── routes/
│   │   ├── auth.py          # Rotas de autenticação
│   │   ├── admin.py         # Rotas do admin
│   │   └── employee.py      # Rotas do funcionário
│   ├── templates/           # Templates HTML
│   └── static/              # Arquivos estáticos
├── requirements.txt         # Dependências Python
├── render.yaml             # Configuração do Render
├── Procfile                # Comando de inicialização
├── runtime.txt             # Versão do Python
├── DEPLOY_RENDER.md        # Guia de deploy
└── README.md               # Este arquivo
```

## 🔧 Funcionalidades Avançadas

### Upload de Arquivos
- Upload de fotos de empresas nos pedidos
- Validação de tipos de arquivo
- Redimensionamento automático

### Filtros e Pesquisa
- Filtros por status, data, funcionário
- Pesquisa em tempo real
- Ordenação customizável

### Notificações em Tempo Real
- Sistema de notificações push
- Contadores de não lidas
- Marcação automática como lida

### Calendário Interativo
- Visualização mensal, semanal e diária
- Filtros por status
- Detalhes do pedido ao clicar

### Estatísticas Avançadas
- Gráficos de pizza e linha
- Métricas de performance
- Relatórios exportáveis

## 🛡️ Segurança

- Senhas hasheadas com Werkzeug
- Proteção CSRF
- Validação de entrada
- Controle de acesso baseado em roles
- Configuração segura para produção

## 📈 Performance

- Carregamento otimizado de assets
- Lazy loading de imagens
- Compressão de arquivos estáticos
- Cache de consultas frequentes
- Configuração otimizada para PostgreSQL

## 🐛 Solução de Problemas

### Porta em uso
Se a porta 5003 estiver em uso, altere no arquivo `src/main.py` ou defina a variável `PORT`.

### Banco de dados
- **Local**: O banco SQLite é criado automaticamente na primeira execução
- **Produção**: Configure a variável `DATABASE_URL` no Render

### Dependências
Se houver problemas com dependências:
```bash
pip install -r requirements.txt
```

## 📞 Suporte

Para dúvidas ou problemas:
1. Verifique se todas as dependências estão instaladas
2. Confirme se o Python 3.11+ está sendo usado
3. Verifique se a porta não está em uso
4. Para produção, verifique as variáveis de ambiente no Render

## 🎯 Próximas Melhorias

- [ ] API REST para integração
- [ ] Relatórios em PDF
- [ ] Backup automático
- [ ] Integração com email
- [ ] App mobile nativo
- [ ] Dashboard em tempo real
- [ ] Storage externo para uploads (S3)

---

**Desenvolvido com ❤️ usando Flask + Jinja2**

*Sistema completo e responsivo para gestão eficiente de pedidos com deploy no Render*

