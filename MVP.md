# RifaMaster - MVP Documentation

## 📋 Visão Geral

RifaMaster é uma plataforma web completa para gerenciamento de rifas online com integração de pagamento PIX via Efí (Gerencianet). O sistema permite que administradores criem e gerenciem rifas, enquanto usuários podem comprar bilhetes de forma segura com pagamento instantâneo via PIX.

## 🎯 Funcionalidades Principais

### 👥 Sistema de Usuários

#### Registro e Autenticação
- Cadastro de usuários com validação de CPF
- Login/Logout seguro com sessões Flask
- Recuperação de senha
- Perfil de usuário editável (nome, email, telefone, CPF)
- Validação algorítmica de CPF (dígitos verificadores)
- Máscaras automáticas para CPF e telefone

#### Controle de Acesso
- Usuários comuns: compra de bilhetes
- Administradores: gerenciamento completo de rifas

### 🎫 Sistema de Rifas

#### Criação e Gerenciamento (Admin)
- Criação de rifas com:
  - Título e descrição
  - Imagem/banner
  - Preço base
  - Número total de bilhetes
  - Tipo: Manual ou Fazendinha
- Sistema de promoções com prazo
- Edição de rifas ativas
- Exclusão de rifas (apenas sem bilhetes vendidos)
- Sorteio automático de vencedores

#### Tipos de Compra

**Manual:**
- Usuário escolhe números específicos
- Visualização em grade de disponibilidade
- Seleção múltipla de bilhetes
- Números reservados durante checkout

**Fazendinha (Aleatória):**
- Sistema gera números aleatórios
- Compra rápida por quantidade
- Números atribuídos após confirmação de pagamento

### 💳 Sistema de Pagamento PIX

#### Integração Efí (Gerencianet)
- Geração de cobranças PIX dinâmicas
- QR Code gerado localmente (biblioteca `qrcode`)
- Código "Copia e Cola" para pagamento
- Expiração de 15 minutos por cobrança
- Suporte a ambientes Sandbox e Produção

#### Fluxo de Pagamento

**Fazendinha:**
1. Usuário seleciona quantidade
2. Sistema calcula valor (com promoções)
3. Gera PIX sem criar bilhetes
4. Cria registro na tabela `payment`
5. Após confirmação → gera bilhetes automaticamente

**Manual:**
1. Usuário seleciona números
2. Bilhetes criados como `pending`
3. Gera PIX e vincula ao `payment_txid`
4. Após confirmação → atualiza status para `paid`

#### Confirmação de Pagamento
- **Webhook**: Efí notifica pagamentos automaticamente
- **Polling**: Frontend consulta status a cada 5 segundos
- Processamento idempotente (evita duplicações)

### ⏰ Sistema de Pagamento Pendente

#### Timer de Expiração
- Bilhetes pendentes têm **1 hora** para pagamento
- Countdown em tempo real no dashboard
- Visual diferenciado (amarelo pulsante)
- Limpeza automática de bilhetes expirados

#### Retry de Pagamento
- Botão "💳 Pagar" ao passar o mouse
- Gera novo PIX para bilhete pendente
- Modal com QR Code e código copia-cola
- Polling automático para confirmação

### 📊 Dashboard do Usuário

#### Meus Bilhetes
- Listagem agrupada por rifa
- Status visual dos bilhetes:
  - ✅ Pago (verde/branco)
  - ⏳ Pendente (amarelo pulsante)
  - ⏱️ Com timer (restante até expiração)
- Informação de vencedores
- Números da sorte destacados
- Opção de comprar mais bilhetes

### 🎨 Interface do Usuário

#### Design
- Theme escuro moderno
- Glassmorphism
- Animações suaves
- Responsivo (mobile-first)
- Cores vibrantes com gradientes

#### Componentes
- Cards de rifas com imagens
- Grids de números interativos
- Modais para checkout e pagamento
- Alerts e notificações (flash messages)
- Scrollbars customizadas

## 🏗️ Arquitetura Técnica

### Backend (Flask)

#### Stack
```
- Python 3.13
- Flask 3.0.0
- Flask-Login 0.6.3
- SQLite3
- Requests 2.31.0
```

#### Estrutura de Arquivos
```
/
├── app.py                  # Aplicação principal
├── database.py            # Configuração SQLite
├── efi_service.py         # Integração Efí/PIX
├── templates/             # Templates HTML
│   ├── base.html
│   ├── index.html
│   ├── raffle_detail.html
│   ├── checkout.html
│   ├── dashboard.html
│   ├── admin_panel.html
│   └── ...
├── static/
│   ├── style.css
│   └── uploads/
├── certs/                 # Certificados Efí
│   ├── homologacao.pem
│   └── producao.pem
└── rifamaster.db          # Banco de dados
```

#### Banco de Dados

**Schema Principal:**

```sql
-- Usuários
CREATE TABLE user (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    cpf TEXT UNIQUE,
    phone TEXT,
    is_admin BOOLEAN DEFAULT 0
);

-- Rifas
CREATE TABLE raffle (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    promo_price REAL,
    promo_end TIMESTAMP,
    total_numbers INTEGER NOT NULL,
    type TEXT NOT NULL,
    status TEXT DEFAULT 'active',
    image_url TEXT,
    winner_ticket_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bilhetes
CREATE TABLE ticket (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    raffle_id INTEGER NOT NULL,
    number INTEGER,
    status TEXT DEFAULT 'pending',
    payment_status TEXT DEFAULT 'pending',
    payment_txid TEXT,
    total_price REAL,
    created_at TIMESTAMP,
    paid_at TIMESTAMP,
    pix_qrcode TEXT,
    pix_copy_paste TEXT,
    payment_expiration TEXT,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (raffle_id) REFERENCES raffle(id)
);

-- Pagamentos
CREATE TABLE payment (
    id INTEGER PRIMARY KEY,
    txid TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL,
    raffle_id INTEGER NOT NULL,
    amount REAL NOT NULL,
    status TEXT DEFAULT 'pending',
    ticket_count INTEGER DEFAULT 0,
    type TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES user(id),
    FOREIGN KEY (raffle_id) REFERENCES raffle(id)
);
```

### Frontend

#### Tecnologias
- HTML5 Semântico
- TailwindCSS (via CDN)
- Vanilla JavaScript
- Jinja2 Templates

#### Features JavaScript
- Polling assíncrono de pagamentos
- Countdown timers em tempo real
- Modais dinâmicos
- Validação de formulários
- Máscaras de input (CPF, telefone)

## 🔐 Segurança

### Autenticação
- Senhas com hash (werkzeug.security)
- Sessões seguras Flask
- Decoradores `@login_required`
- CSRF protection (Flask-WTF)

### Validações
- CPF: validação algorítmica completa
- Email: formato RFC válido
- Unicidade: username, email, CPF

### Pagamentos
- Certificados SSL (.pem) para Efí
- Validação de webhook signature
- Tokens OAuth com scopes específicos
- Ambiente Sandbox para testes

## 🚀 Configuração e Deploy

### Variáveis de Ambiente (.env)
```env
# Flask
SECRET_KEY=your_secret_key_here

# Efí/Gerencianet
EFI_ENVIRONMENT=sandbox  # ou production
EFI_SANDBOX_CLIENT_ID=your_client_id
EFI_SANDBOX_CLIENT_SECRET=your_client_secret
EFI_SANDBOX_CERTIFICATE_PATH=certs/homologacao.p12
EFI_SANDBOX_PIX_KEY=your_pix_key_uuid

# Production (quando aplicável)
EFI_PRODUCTION_CLIENT_ID=...
EFI_PRODUCTION_CLIENT_SECRET=...
EFI_PRODUCTION_CERTIFICATE_PATH=certs/producao.p12
EFI_PRODUCTION_PIX_KEY=...
```

### Instalação

```bash
# 1. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 2. Instalar dependências
pip install -r requirements.txt

# 3. Converter certificados Efí (se necessário)
python convert_certs.py

# 4. Criar tabelas do banco
python -c "import database; database.init_db()"

# 5. Executar migrações (se necessário)
python add_created_at_column.py
python migrate_ticket_table.py
python create_payment_table.py

# 6. Iniciar servidor
python app.py
```

### Certificados Efí

Os certificados `.p12` fornecidos pela Efí devem ser convertidos para `.pem`:

```bash
python convert_certs.py
```

Isso gera:
- `certs/homologacao.pem` (Sandbox)
- `certs/producao.pem` (Produção)

## 📈 Roadmap Futuro

### Melhorias Planejadas
- [ ] Sistema de notificações por email
- [ ] Histórico completo de transações
- [ ] Relatórios administrativos
- [ ] Filtros e busca avançada
- [ ] Sistema de cupons/desconto
- [ ] Compartilhamento social
- [ ] API REST para integrações
- [ ] App mobile (React Native)

### Otimizações
- [ ] Cache de consultas frequentes
- [ ] Compressão de imagens
- [ ] CDN para assets estáticos
- [ ] Rate limiting
- [ ] Background jobs (Celery)

## 📝 Licença e Créditos

**Desenvolvido para**: Gestão de rifas online com foco em simplicidade e segurança

**Tecnologias principais**:
- Flask (Backend)
- SQLite (Database)
- Efí/Gerencianet (Pagamentos PIX)
- TailwindCSS (UI)

**Status**: MVP Funcional ✅

---

## 🆘 Suporte e Documentação

Para dúvidas sobre:
- **Efí/Gerencianet**: https://dev.efipay.com.br/
- **Flask**: https://flask.palletsprojects.com/
- **PIX**: https://www.bcb.gov.br/estabilidadefinanceira/pix

## 📊 Métricas do MVP

- **Linhas de código**: ~1000+ (backend)
- **Templates**: 10+
- **Rotas Flask**: 25+
- **Tabelas DB**: 4
- **Dependent**: 8 bibliotecas principais
- **Tempo de desenvolvimento**: ~3 sessões
- **Status de testes**: ✅ Funcional em Sandbox
