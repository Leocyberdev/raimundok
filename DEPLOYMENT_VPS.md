# Guia de Deployment para VPS PostgreSQL

## 🚀 Como Fazer Deploy das Atualizações na VPS

### 1. Faça o Push para o GitHub

No seu ambiente de desenvolvimento (aqui no Replit ou local):

```bash
git add .
git commit -m "Atualização: Campo CNPJ da Empresa"
git push origin main
```

### 2. Conecte na VPS e Atualize o Código

Na sua VPS, acesse o diretório do projeto e faça o pull:

```bash
cd /caminho/do/seu/projeto
git pull origin main
```

### 3. Reinicie o Servidor Flask

Dependendo de como você está rodando o servidor:

**Opção 1 - Se estiver usando systemd/service:**
```bash
sudo systemctl restart nome-do-seu-servico
```

**Opção 2 - Se estiver usando pm2:**
```bash
pm2 restart nome-do-app
```

**Opção 3 - Se estiver usando gunicorn diretamente:**
```bash
pkill gunicorn
gunicorn --bind 0.0.0.0:5000 src.main:app
```

### 4. ✅ Pronto! As Migrações Acontecerão Automaticamente

Quando o servidor Flask iniciar, o sistema automaticamente:

1. **Detectará o PostgreSQL** via variável de ambiente `DATABASE_URL`
2. **Criará todas as tabelas** (se não existirem)
3. **Adicionará todas as colunas faltantes** automaticamente:
   - ✅ `user.full_name` (usado como CNPJ)
   - ✅ `user.email`
   - ✅ `user.phone`
   - ✅ `user.address`
   - ✅ `user.profile_picture`
   - ✅ `order.client_id`
   - ✅ `order.is_urgent`
   - ✅ `order.subtitle`
   - ✅ `order.description`
   - ✅ Todas as outras colunas necessárias

### 5. Verificar os Logs

Para confirmar que as migrações foram aplicadas com sucesso:

```bash
# Ver logs do sistema
journalctl -u nome-do-seu-servico -f

# Ou se estiver usando pm2
pm2 logs nome-do-app

# Ou ver o output direto
tail -f /caminho/dos/logs/app.log
```

Você deve ver mensagens como:
```
Todas as migrações foram verificadas/aplicadas!
Banco de dados inicializado com sucesso! Ambiente: Produção (PostgreSQL)
```

## 📋 Checklist Pré-Deployment

Antes de fazer o deploy, certifique-se que sua VPS tem:

- [ ] Python 3.8+ instalado
- [ ] PostgreSQL instalado e rodando
- [ ] Variável de ambiente `DATABASE_URL` configurada
- [ ] Todas as dependências do `requirements.txt` instaladas
- [ ] Gunicorn ou outro WSGI server configurado

## 🔧 Configuração da Variável DATABASE_URL

A variável `DATABASE_URL` deve estar no formato:

```bash
DATABASE_URL=postgresql://usuario:senha@localhost:5432/nome_do_banco
```

### Como configurar:

**Opção 1 - Variável de ambiente permanente:**
```bash
# Adicione no /etc/environment ou ~/.bashrc
export DATABASE_URL="postgresql://usuario:senha@localhost:5432/nome_do_banco"
```

**Opção 2 - No arquivo de serviço (systemd):**
```ini
[Service]
Environment="DATABASE_URL=postgresql://usuario:senha@localhost:5432/nome_do_banco"
```

**Opção 3 - Com pm2 (ecosystem.config.js):**
```javascript
module.exports = {
  apps: [{
    name: 'flask-app',
    script: 'gunicorn',
    args: '--bind 0.0.0.0:5000 src.main:app',
    env: {
      DATABASE_URL: 'postgresql://usuario:senha@localhost:5432/nome_do_banco'
    }
  }]
}
```

## 🛠️ Troubleshooting

### Se as migrações não rodarem:

1. **Verifique se DATABASE_URL está configurada:**
   ```bash
   echo $DATABASE_URL
   ```

2. **Verifique os logs de erro:**
   - Procure por mensagens de erro relacionadas ao banco de dados
   - Confirme que o PostgreSQL está rodando

3. **Execute manualmente (se necessário):**
   ```bash
   python3 src/main.py
   # Você verá o output das migrações diretamente no terminal
   ```

### Se der erro de conexão com PostgreSQL:

```bash
# Verifique se o PostgreSQL está rodando
sudo systemctl status postgresql

# Teste a conexão manualmente
psql -h localhost -U usuario -d nome_do_banco
```

## 📝 Notas Importantes

1. **Backup do Banco de Dados**: Sempre faça backup antes de fazer deploy:
   ```bash
   pg_dump nome_do_banco > backup_$(date +%Y%m%d).sql
   ```

2. **Sistema de Migração Automática**: O arquivo `src/main.py` (linhas 184-254) gerencia todas as migrações automaticamente. Você **NÃO** precisa executar scripts SQL manualmente.

3. **Compatibilidade**: O campo `cnpj` usa a coluna `full_name` no banco de dados para manter compatibilidade com dados existentes.

4. **Zero Downtime**: As migrações são não-destrutivas (apenas adicionam colunas), então não há perda de dados.

## 🎯 Resumo

```bash
# 1. Push para GitHub
git push origin main

# 2. Na VPS
cd /caminho/do/projeto
git pull origin main

# 3. Reiniciar servidor
sudo systemctl restart seu-servico
# ou
pm2 restart seu-app

# 4. Verificar logs
journalctl -u seu-servico -f

# ✅ Pronto! Sistema atualizado com CNPJ da Empresa
```

---

**Desenvolvido com ❤️ | Sistema de Gestão de Pedidos**
