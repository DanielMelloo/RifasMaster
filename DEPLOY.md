# Configuração de Deploy para EC2 com Nginx

## 📝 Resumo
Esta aplicação Flask será servida em **danielmello.store/Rifa** usando Nginx como reverse proxy.

## 🔧 Configuração Necessária

### 1. Variáveis de Ambiente (.env)

Adicione no servidor EC2:

```bash
# Subpath configuration
APPLICATION_ROOT=/Rifa

# Outras variáveis existentes
SECRET_KEY=your_production_secret_key_here
EFI_ENVIRONMENT=production
# ... resto das configurações Efí
```

### 2. Nginx Configuration

Copie o arquivo `nginx_config.conf` para `/etc/nginx/sites-available/` no EC2:

```bash
sudo cp nginx_config.conf /etc/nginx/sites-available/rifamaster
sudo ln -s /etc/nginx/sites-available/rifamaster /etc/nginx/sites-enabled/
```

**IMPORTANTE**: Edite o arquivo e ajuste:
- Caminho para os arquivos estáticos: `/caminho/para/Rifas/static/`
- Configuração do site principal (seção `location /`)

Teste e recarregue o Nginx:
```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 3. Gunicorn (Produção)

Instale o Gunicorn:
```bash
pip install gunicorn
```

Crie um arquivo systemd service (`/etc/systemd/system/rifamaster.service`):

```ini
[Unit]
Description=RifaMaster Flask App
After=network.target

[Service]
User=seu_usuario
WorkingDirectory=/caminho/para/Rifas
Environment="PATH=/caminho/para/Rifas/venv/bin"
ExecStart=/caminho/para/Rifas/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:5000 app:app

[Install]
WantedBy=multi-user.target
```

Ative e inicie o serviço:
```bash
sudo systemctl enable rifamaster
sudo systemctl start rifamaster
sudo systemctl status rifamaster
```

### 4. Verificação

Após configurar, acesse:
- **http://danielmello.store/Rifa** → Página inicial do RifaMaster
- **http://danielmello.store** → Seu site principal (inalterado)

## 🚨 Importante

### Rotas
✅ **NÃO precisa alterar as rotas manualmente!**

O Flask já usa `url_for()` em todos os templates, que automaticamente adiciona o prefixo `/Rifa` quando `APPLICATION_ROOT` está configurado.

### Assets Estáticos
Os arquivos CSS, JS e imagens já estão usando `url_for('static', filename='...')`, então também funcionarão automaticamente.

### Webhook Efí
⚠️ Configure o webhook da Efí para:
```
https://danielmello.store/Rifa/efi_webhook
```

## 🧪 Teste Local

Para testar localmente com o prefixo:

```bash
# Adicione ao .env
APPLICATION_ROOT=/Rifa

# Execute normalmente
python app.py
```

Acesse: `http://localhost:5000/Rifa`

## 📦 Checklist de Deploy

- [ ] Copiar arquivos para EC2
- [ ] Criar venv e instalar dependências
- [ ] Configurar `.env` com `APPLICATION_ROOT=/Rifa`
- [ ] Converter certificados Efí (.p12 para .pem)
- [ ] Executar migrações do banco
- [ ] Configurar Nginx (ajustar caminhos)
- [ ] Criar serviço systemd para Gunicorn
- [ ] Testar acesso: danielmello.store/Rifa
- [ ] Atualizar webhook URL na Efí
- [ ] Verificar logs: `sudo journalctl -u rifamaster -f`

## 🔍 Troubleshooting

### Erro 404 em assets
- Verifique o caminho `alias` no Nginx
- Certifique-se que `APPLICATION_ROOT` está no .env

### Redirecionamentos quebrados
- Todos os `url_for()` devem funcionar automaticamente
- Se algum link estiver hardcoded, substitua por `url_for()`

### Webhook não funciona
- Verifique se a URL pública está acessível
- Confirme que o Nginx está fazendo proxy correto
- Valide os certificados SSL (use HTTPS)

## 📚 Referências

- [Flask Application Dispatching](https://flask.palletsprojects.com/en/latest/patterns/appdispatch/)
- [Nginx Reverse Proxy](https://docs.nginx.com/nginx/admin-guide/web-server/reverse-proxy/)
- [Gunicorn Deployment](https://docs.gunicorn.org/en/stable/deploy.html)
