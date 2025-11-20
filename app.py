import os
from flask import Flask, render_template, redirect, url_for, flash, request, g, current_app, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import database
import random
import sqlite3
from datetime import datetime
from efi_service import efi_service

# Carregar variáveis de ambiente
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_key')
app.config['DATABASE'] = os.path.join(app.root_path, 'rifamaster.db')
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max-limit

# Garantir que pasta de uploads existe
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Inicializar DB
database.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, faça login para acessar essa página.'
login_manager.login_message_category = 'error'

# Classe User adaptada para Flask-Login com dados do SQLite
class User(UserMixin):
    def __init__(self, id, username, email, password_hash, is_admin, full_name=None, phone=None, pix_key=None, address=None, cpf=None):
        self.id = id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.is_admin = bool(is_admin)
        self.full_name = full_name
        self.phone = phone
        self.pix_key = pix_key
        self.address = address
        self.cpf = cpf

@login_manager.user_loader
def load_user(user_id):
    db = database.get_db()
    user_data = db.execute('SELECT * FROM user WHERE id = ?', (user_id,)).fetchone()
    if user_data:
        # sqlite3.Row does not support .get(), use keys directly or dict() conversion
        # Since we migrated, columns should exist. If they are NULL, we get None.
        return User(
            user_data['id'], 
            user_data['username'], 
            user_data['email'], 
            user_data['password_hash'], 
            user_data['is_admin'],
            user_data['full_name'] if 'full_name' in user_data.keys() else None,
            user_data['phone'] if 'phone' in user_data.keys() else None,
            user_data['pix_key'] if 'pix_key' in user_data.keys() else None,
            user_data['address'] if 'address' in user_data.keys() else None,
            user_data['cpf'] if 'cpf' in user_data.keys() else None
        )
    return None

# Context Processor
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# --- Rotas de Autenticação ---

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        db = database.get_db()
        user_data = db.execute('SELECT * FROM user WHERE email = ?', (email,)).fetchone()
        
        if user_data and check_password_hash(user_data['password_hash'], password):
            user = User(user_data['id'], user_data['username'], user_data['email'], user_data['password_hash'], user_data['is_admin'])
            login_user(user)
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Email ou senha incorretos.', 'error')
            
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        db = database.get_db()
        
        if db.execute('SELECT id FROM user WHERE email = ?', (email,)).fetchone():
            flash('Este email já está cadastrado.', 'error')
            return redirect(url_for('register'))
            
        hashed_password = generate_password_hash(password)
        
        # Verificar se é o primeiro usuário
        is_admin = False
        if db.execute('SELECT COUNT(*) as count FROM user').fetchone()['count'] == 0:
            is_admin = True
            
        try:
            db.execute(
                'INSERT INTO user (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                (username, email, hashed_password, is_admin)
            )
            db.commit()
            
            # Login automático após registro
            user_data = db.execute('SELECT * FROM user WHERE email = ?', (email,)).fetchone()
            user = User(user_data['id'], user_data['username'], user_data['email'], user_data['password_hash'], user_data['is_admin'])
            login_user(user)
            
            flash('Conta criada com sucesso! Por favor, complete seu perfil para poder receber prêmios.', 'success')
            return redirect(url_for('profile'))
        except sqlite3.Error as e:
            flash(f'Erro ao criar conta: {e}', 'error')
        
    return render_template('register.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        phone = request.form.get('phone')
        pix_key = request.form.get('pix_key')
        address = request.form.get('address')
        cpf = request.form.get('cpf')
        
        db = database.get_db()
        try:
            db.execute('''
                UPDATE user 
                SET full_name = ?, phone = ?, pix_key = ?, address = ?, cpf = ?
                WHERE id = ?
            ''', (full_name, phone, pix_key, address, cpf, current_user.id))
            db.commit()
            flash('Perfil atualizado com sucesso!', 'success')
            return redirect(url_for('profile'))
        except sqlite3.Error as e:
            flash(f'Erro ao atualizar perfil: {e}', 'error')
            
    return render_template('profile.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você saiu da sua conta.', 'success')
    return redirect(url_for('index'))

# --- Funções Auxiliares ---
def get_current_price(raffle):
    """Calcula o preço atual considerando promoções ativas"""
    now = datetime.now()
    if raffle['promo_price'] and raffle['promo_end']:
        promo_end = raffle['promo_end']
        
        # If it's a string, try to parse it (legacy support or if converter fails)
        if isinstance(promo_end, str):
            try:
                # Try parsing with seconds first (new format)
                promo_end = datetime.strptime(promo_end, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                try:
                    # Fallback to old format without seconds
                    promo_end = datetime.strptime(promo_end, '%Y-%m-%d %H:%M')
                except ValueError:
                    return raffle['price'] # Invalid format

        if isinstance(promo_end, datetime) and now < promo_end:
            return raffle['promo_price']
            
    return raffle['price']

# --- Rotas Principais ---

@app.route('/')
def index():
    db = database.get_db()
    # Buscar rifas
    raffles = db.execute("SELECT * FROM raffle WHERE status = 'active'").fetchall()
    
    # Processar dados para o template
    raffles_data = []
    for r in raffles:
        r_dict = dict(r)
        tickets_count = db.execute('SELECT COUNT(*) as count FROM ticket WHERE raffle_id = ? AND number IS NOT NULL', (r['id'],)).fetchone()['count']
        r_dict['tickets_count'] = tickets_count
        
        # Verificar promoção ativa
        r_dict['current_price'] = get_current_price(r_dict)
        r_dict['is_promo'] = r_dict['current_price'] < r_dict['price']
        
        raffles_data.append(r_dict)
        
    return render_template('index.html', raffles=raffles_data)

@app.route('/raffle/<int:raffle_id>')
def raffle_detail(raffle_id):
    db = database.get_db()
    raffle = db.execute('SELECT * FROM raffle WHERE id = ?', (raffle_id,)).fetchone()
    
    if not raffle:
        return "Rifa não encontrada", 404
        
    tickets = db.execute('SELECT * FROM ticket WHERE raffle_id = ? AND number IS NOT NULL', (raffle_id,)).fetchall()
    
    raffle_dict = dict(raffle)
    raffle_dict['tickets'] = tickets
    raffle_dict['current_price'] = get_current_price(raffle_dict)
    raffle_dict['is_promo'] = raffle_dict['current_price'] < raffle_dict['price']
    
    return render_template('raffle_detail.html', raffle=raffle_dict)

@app.route('/raffle/<int:raffle_id>/buy', methods=['POST'])
@login_required
def buy_ticket(raffle_id):
    db = database.get_db()
    raffle = db.execute('SELECT * FROM raffle WHERE id = ?', (raffle_id,)).fetchone()
    
    if not raffle or raffle['status'] != 'active':
        flash('Esta rifa já foi encerrada.', 'error')
        return redirect(url_for('index'))

    raffle_type = raffle['type']
    
    if raffle_type == 'manual':
        # Manual: criar tickets imediatamente (números específicos escolhidos)
        numbers = [int(n) for n in request.form.getlist('numbers')]
        if not numbers:
            flash('Selecione pelo menos um número.', 'error')
            return redirect(url_for('raffle_detail', raffle_id=raffle_id))
            
        # Verificar disponibilidade
        for num in numbers:
            existing = db.execute('SELECT id FROM ticket WHERE raffle_id = ? AND number = ?', (raffle_id, num)).fetchone()
            if existing:
                flash(f'O número {num} já foi vendido.', 'error')
                return redirect(url_for('raffle_detail', raffle_id=raffle_id))
        
        # Criar bilhetes pendentes para manual
        ticket_ids = []
        try:
            for num in numbers:
                cursor = db.execute(
                    'INSERT INTO ticket (user_id, raffle_id, number, status) VALUES (?, ?, ?, ?)',
                    (current_user.id, raffle_id, num, 'pending')
                )
                ticket_ids.append(cursor.lastrowid)
            db.commit()
        except sqlite3.Error as e:
            db.rollback()
            flash(f'Erro ao comprar bilhetes: {e}', 'error')
            return redirect(url_for('raffle_detail', raffle_id=raffle_id))
        
        # Manual usa URL com ticket_ids (números já escolhidos)
        return redirect(url_for('checkout', ticket_ids=','.join([str(id) for id in ticket_ids])))
    
    else:
        # Fazendinha/Random: usar SESSION (não criar tickets ainda)
        quantity = int(request.form.get('quantity', 0))
        if quantity <= 0:
            flash('Selecione a quantidade de bilhetes.', 'error')
            return redirect(url_for('raffle_detail', raffle_id=raffle_id))
            
        # Verificar se há números suficientes disponíveis
        sold_count = db.execute('SELECT COUNT(*) as count FROM ticket WHERE raffle_id = ? AND number IS NOT NULL', (raffle_id,)).fetchone()['count']
        available_count = raffle['total_numbers'] - sold_count
        
        if available_count < quantity:
            flash(f'Apenas {available_count} números disponíveis.', 'error')
            return redirect(url_for('raffle_detail', raffle_id=raffle_id))
        
        # Armazenar na sessão (não criar tickets ainda!)
        session['pending_purchase'] = {
            'raffle_id': raffle_id,
            'raffle_title': raffle['title'],
            'raffle_type': raffle_type,
            'quantity': quantity,
            'price': float(raffle['price']),
            'promo_price': float(raffle['promo_price']) if raffle['promo_price'] else None,
            'promo_end': raffle['promo_end']
        }
        
        # Redirecionar para checkout SEM ticket_ids na URL
        return redirect(url_for('checkout'))

@app.route('/checkout')
@login_required
def checkout():
    # Tentar obter de ticket_ids (manual) ou session (fazendinha)
    ticket_ids_str = request.args.get('ticket_ids', '')
    
    if ticket_ids_str:
        # Fluxo MANUAL: tem ticket_ids na URL
        try:
            ticket_ids = [int(id) for id in ticket_ids_str.split(',')]
        except ValueError:
            return redirect(url_for('index'))

        if not ticket_ids:
            return redirect(url_for('index'))
            
        placeholders = ','.join(['?'] * len(ticket_ids))
        query = f'''
            SELECT t.*, r.title as raffle_title, r.price as raffle_price, r.type as raffle_type,
                   r.promo_price, r.promo_end
            FROM ticket t 
            JOIN raffle r ON t.raffle_id = r.id 
            WHERE t.id IN ({placeholders}) AND t.user_id = ?
        '''
        params = ticket_ids + [current_user.id]
        
        db = database.get_db()
        tickets = db.execute(query, params).fetchall()
        
        if not tickets:
            return redirect(url_for('index'))
        
        tickets_dicts = []
        total_price = 0
        
        for t in tickets:
            td = dict(t)
            # Calcular preço efetivo (promoção ou normal)
            raffle_data = {
                'price': t['raffle_price'],
                'promo_price': t['promo_price'],
                'promo_end': t['promo_end']
            }
            effective_price = get_current_price(raffle_data)
            
            td['raffle'] = {
                'title': t['raffle_title'], 
                'price': t['raffle_price'], 
                'type': t['raffle_type'],
                'effective_price': effective_price
            }
            tickets_dicts.append(td)
            total_price += effective_price
        
        return render_template('checkout.html', tickets=tickets_dicts, total_price=total_price, ticket_ids=ticket_ids_str, from_session=False)
    
    elif 'pending_purchase' in session:
        # Fluxo FAZENDINHA: dados na sessão
        purchase = session['pending_purchase']
        
        # Calcular preço efetivo
        raffle_data = {
            'price': purchase['price'],
            'promo_price': purchase.get('promo_price'),
            'promo_end': purchase.get('promo_end')
        }
        effective_price = get_current_price(raffle_data)
        total_price = effective_price * purchase['quantity']
        
        # Criar estrutura similar para o template
        tickets_dicts = [{
            'raffle': {
                'title': purchase['raffle_title'],
                'price': purchase['price'],
                'type': purchase['raffle_type'],
                'effective_price': effective_price
            },
            'number': None  # Fazendinha não tem número ainda
        }] * purchase['quantity']
        
        return render_template('checkout.html', tickets=tickets_dicts, total_price=total_price, ticket_ids='', from_session=True)
    
    else:
        # Sem dados válidos
        flash('Carrinho vazio.', 'error')
        return redirect(url_for('index'))

@app.route('/process_payment', methods=['POST'])
@login_required
def process_payment():
    db = database.get_db()
    
    # Verificar se é compra da sessão (fazendinha) ou ticket_ids (manual)
    if 'pending_purchase' in session:
        # FAZENDINHA: Criar tickets AGORA (após pagamento)
        purchase = session['pending_purchase']
        raffle_id = purchase['raffle_id']
        quantity = purchase['quantity']
        
        try:
            # Buscar rifa para verificar disponibilidade
            raffle = db.execute('SELECT * FROM raffle WHERE id = ?', (raffle_id,)).fetchone()
            if not raffle or raffle['status'] != 'active':
                flash('Rifa não disponível.', 'error')
                return redirect(url_for('index'))
            
            # Buscar números já usados
            used_numbers_rows = db.execute('SELECT number FROM ticket WHERE raffle_id = ? AND number IS NOT NULL', (raffle_id,)).fetchall()
            used_numbers = {row['number'] for row in used_numbers_rows}
            
            available = [n for n in range(1, raffle['total_numbers'] + 1) if n not in used_numbers]
            
            if len(available) < quantity:
                raise Exception(f"Não há números suficientes disponíveis")
                
            selected_numbers = random.sample(available, quantity)
            
            # Criar tickets já com status='paid' e número atribuído
            for number in selected_numbers:
                db.execute(
                    'INSERT INTO ticket (user_id, raffle_id, number, status) VALUES (?, ?, ?, ?)',
                    (current_user.id, raffle_id, number, 'paid')
                )
            
            db.commit()
            
            # Limpar sessão
            session.pop('pending_purchase', None)
            
            flash('Pagamento confirmado! Seus números foram gerados.', 'success')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            db.rollback()
            flash(f'Erro ao processar pagamento: {e}', 'error')
            return redirect(url_for('index'))
    
    else:
        # MANUAL: Atualizar tickets existentes
        ticket_ids_str = request.form.get('ticket_ids')
        try:
            ticket_ids = [int(id) for id in ticket_ids_str.split(',')]
        except:
            return redirect(url_for('index'))
        
        if not ticket_ids:
            return redirect(url_for('index'))

        # Marcar como pagos
        placeholders = ','.join(['?'] * len(ticket_ids))
        try:
            db.execute(f'UPDATE ticket SET status = "paid" WHERE id IN ({placeholders}) AND user_id = ?', ticket_ids + [current_user.id])
            db.commit()
            flash('Pagamento confirmado!', 'success')
        except Exception as e:
            db.rollback()
            flash(f'Erro ao processar pagamento: {e}', 'error')
            return redirect(url_for('index'))
        
        return redirect(url_for('dashboard'))

@app.route('/dashboard')
@login_required
def dashboard():
    db = database.get_db()
    query = '''
        SELECT t.*, r.title as raffle_title, r.status as raffle_status, r.winner_ticket_id, r.image_url
        FROM ticket t
        JOIN raffle r ON t.raffle_id = r.id
        WHERE t.user_id = ?
        ORDER BY r.title ASC, t.number ASC
    '''
    tickets = db.execute(query, (current_user.id,)).fetchall()
    
    # Mapeamento de tradução de status
    status_map = {'active': 'Ativa', 'closed': 'Encerrada'}
    
    try:
        # Agrupar tickets por rifa
        grouped_tickets = {}
        for t in tickets:
            raffle_title = t['raffle_title']
            if raffle_title not in grouped_tickets:
                # Se houver vencedor, buscar o número vencedor
                winning_number = None
                if t['winner_ticket_id']:
                    wt = db.execute('SELECT number FROM ticket WHERE id = ?', (t['winner_ticket_id'],)).fetchone()
                    if wt:
                        winning_number = wt['number']

                grouped_tickets[raffle_title] = {
                    'raffle_id': t['raffle_id'],
                    'raffle_status': t['raffle_status'],
                    'raffle_status_text': status_map.get(t['raffle_status'], t['raffle_status']),
                    'winner_ticket_id': t['winner_ticket_id'],
                    'winning_number': winning_number,
                    'image_url': t['image_url'],
                    'tickets': []
                }
            
            grouped_tickets[raffle_title]['tickets'].append({
                'number': t['number'],
                'status': t['status'],
                'id': t['id']
            })

        return render_template('dashboard.html', grouped_tickets=grouped_tickets)
    except Exception as e:
        print(f"Erro no dashboard: {e}")
        flash('Erro ao carregar seus bilhetes. Por favor, contate o suporte.', 'error')
        return render_template('dashboard.html', grouped_tickets={})

# --- Rotas de Admin ---

@app.route('/admin')
@login_required
def admin_panel():
    if not current_user.is_admin:
        flash('Acesso não autorizado.', 'error')
        return redirect(url_for('index'))
        
    db = database.get_db()
    raffles_raw = db.execute('SELECT * FROM raffle').fetchall()
    
    # Mapeamento de tradução de status
    status_map = {'active': 'Ativa', 'closed': 'Encerrada'}
    
    # Adicionar contagem de tickets para cada rifa
    raffles_data = []
    for raffle in raffles_raw:
        raffle_dict = dict(raffle)
        # Contar TODOS os tickets (paid + pending) para validação de delete
        tickets_count = db.execute(
            'SELECT COUNT(*) as count FROM ticket WHERE raffle_id = ?', 
            (raffle['id'],)
        ).fetchone()['count']
        raffle_dict['tickets_count'] = tickets_count
        raffle_dict['status_text'] = status_map.get(raffle['status'], raffle['status'])
        raffles_data.append(raffle_dict)
    
    return render_template('admin_panel.html', raffles=raffles_data)

@app.route('/admin/create_raffle', methods=['POST'])
@login_required
def create_raffle():
    if not current_user.is_admin:
        return redirect(url_for('index'))
        
    title = request.form.get('title')
    description = request.form.get('description')
    price = float(request.form.get('price'))
    total_numbers = int(request.form.get('total_numbers'))
    type = request.form.get('type')
    
    # Promoção
    promo_price = request.form.get('promo_price')
    promo_end = request.form.get('promo_end')
    
    if promo_price:
        promo_price = float(promo_price)
    else:
        promo_price = None
        
    if not promo_end or promo_end.strip() == '':
        promo_end = None
    else:
        promo_end = promo_end.replace('T', ' ')
        if len(promo_end) == 16: # YYYY-MM-DD HH:MM
            promo_end += ':00'
    
    # Upload de imagem
    image_url = request.form.get('image_url') # Fallback URL
    if 'image_file' in request.files:
        file = request.files['image_file']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = url_for('static', filename=f'uploads/{filename}')

    db = database.get_db()
    db.execute(
        'INSERT INTO raffle (title, description, price, total_numbers, type, image_url, promo_price, promo_end) VALUES (?, ?, ?, ?, ?, ?, ?, ?)',
        (title, description, price, total_numbers, type, image_url, promo_price, promo_end)
    )
    db.commit()
    
    flash('Rifa criada com sucesso!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/edit_raffle/<int:raffle_id>', methods=['POST'])
@login_required
def edit_raffle(raffle_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
        
    title = request.form.get('title')
    description = request.form.get('description')
    price = float(request.form.get('price')) # Permitir edição de preço
    
    # Promoção
    promo_price = request.form.get('promo_price')
    promo_end = request.form.get('promo_end')
    
    if promo_price:
        promo_price = float(promo_price)
    else:
        promo_price = None
        
    if not promo_end or promo_end.strip() == '':
        promo_end = None
    else:
        promo_end = promo_end.replace('T', ' ')
        if len(promo_end) == 16: # YYYY-MM-DD HH:MM
            promo_end += ':00'
    
    image_url = request.form.get('image_url')
    if 'image_file' in request.files:
        file = request.files['image_file']
        if file and file.filename != '':
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = url_for('static', filename=f'uploads/{filename}')
            
    db = database.get_db()
    
    # Se image_url não foi enviado (campo vazio), manter o atual?
    # O form envia o valor atual se não alterado? O JS do modal deve preencher.
    # Se o usuário limpar o campo, assume-se que quer remover ou manter?
    # Vamos assumir que se vier vazio e não tiver arquivo, mantém o antigo.
    # Mas para simplificar, vamos atualizar tudo. Se o usuário quiser manter, o modal deve vir preenchido.
    
    # Query dinâmica seria melhor, mas vamos atualizar tudo que é editável
    db.execute('''
        UPDATE raffle 
        SET title = ?, description = ?, price = ?, promo_price = ?, promo_end = ?, image_url = ? 
        WHERE id = ?
    ''', (title, description, price, promo_price, promo_end, image_url, raffle_id))
    
    db.commit()
    
    flash('Rifa atualizada!', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/create_admin', methods=['POST'])
@login_required
def create_admin_user():
    if not current_user.is_admin:
        return redirect(url_for('index'))
        
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    
    hashed_password = generate_password_hash(password)
    
    db = database.get_db()
    try:
        db.execute(
            'INSERT INTO user (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
            (username, email, hashed_password, True)
        )
        db.commit()
        flash(f'Admin {username} criado com sucesso!', 'success')
    except sqlite3.Error:
        flash('Erro ao criar admin. Email pode já existir.', 'error')
        
    return redirect(url_for('admin_panel'))

@app.route('/admin/draw/<int:raffle_id>', methods=['POST'])
@login_required
def draw_winner(raffle_id):
    if not current_user.is_admin:
        return redirect(url_for('index'))
        
    db = database.get_db()
    
    sold_tickets = db.execute('SELECT * FROM ticket WHERE raffle_id = ? AND status = "paid" AND number IS NOT NULL', (raffle_id,)).fetchall()
    
    if not sold_tickets:
        flash('Não há bilhetes vendidos para realizar o sorteio.', 'error')
        return redirect(url_for('admin_panel'))
        
    winner_ticket = random.choice(sold_tickets)
    
    db.execute('UPDATE raffle SET status = "closed", winner_ticket_id = ? WHERE id = ?', (winner_ticket['id'], raffle_id))
    db.commit()
    
    winner_user = db.execute('SELECT username FROM user WHERE id = ?', (winner_ticket['user_id'],)).fetchone()
    
    flash(f'Sorteio realizado! O vencedor é {winner_user["username"]} com o número {winner_ticket["number"]}.', 'success')
    return redirect(url_for('admin_panel'))

@app.route('/admin/remove_promotion/<int:raffle_id>', methods=['POST'])
@login_required
def remove_promotion(raffle_id):
    """Remove a promoção de uma rifa"""
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    db = database.get_db()
    
    # Atualizar rifa removendo promoção
    db.execute('''
        UPDATE raffle 
        SET promo_price = NULL, promo_end = NULL 
        WHERE id = ?
    ''', (raffle_id,))
    db.commit()
    
    flash('Promoção removida com sucesso!', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/admin/set_promotion/<int:raffle_id>', methods=['POST'])
@login_required
def set_promotion(raffle_id):
    """Define uma promoção para uma rifa usando o modal dedicado"""
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    promo_price = request.form.get('promo_price')
    promo_end = request.form.get('promo_end')
    
    if not promo_price or not promo_end:
        flash('Preço promocional e data limite são obrigatórios.', 'error')
        return redirect(url_for('admin_panel'))
    
    try:
        promo_price = float(promo_price)
    except ValueError:
        flash('Preço promocional inválido.', 'error')
        return redirect(url_for('admin_panel'))
        
    db = database.get_db()
    
    # Validar se preço promocional é menor que o original
    raffle = db.execute('SELECT price FROM raffle WHERE id = ?', (raffle_id,)).fetchone()
    if raffle and promo_price >= raffle['price']:
        flash('O preço promocional deve ser menor que o preço original.', 'error')
        return redirect(url_for('admin_panel'))
    
    # Atualizar rifa com promoção
    db.execute('''
        UPDATE raffle 
        SET promo_price = ?, promo_end = ?
        WHERE id = ?
    ''', (promo_price, promo_end, raffle_id))
    db.commit()
    
    flash('Promoção configurada com sucesso!', 'success')
    return redirect(url_for('admin_panel'))
@app.route('/admin/delete_raffle/<int:raffle_id>', methods=['POST'])
@login_required
def delete_raffle(raffle_id):
    """Deleta uma rifa (somente se não houver bilhetes vendidos)"""
    if not current_user.is_admin:
        flash('Acesso negado.', 'error')
        return redirect(url_for('index'))
    
    db = database.get_db()
    
    # Verificar se a rifa pode ser deletada
    raffle = db.execute('SELECT * FROM raffle WHERE id = ?', (raffle_id,)).fetchone()
    
    if not raffle:
        flash('Rifa não encontrada.', 'error')
        return redirect(url_for('admin_panel'))
    
    # Contar tickets
    ticket_count = db.execute('SELECT COUNT(*) as count FROM ticket WHERE raffle_id = ?', (raffle_id,)).fetchone()['count']
    
    if ticket_count > 0:
        flash('Não é possível deletar rifa com bilhetes vendidos.', 'error')
        return redirect(url_for('admin_panel'))
    
    if raffle['status'] == 'closed':
        flash('Não é possível deletar rifa já encerrada.', 'error')
        return redirect(url_for('admin_panel'))
    
    # Deletar rifa
    db.execute('DELETE FROM raffle WHERE id = ?', (raffle_id,))
    db.commit()
    
    flash(f'Rifa "{raffle["title"]}" deletada com sucesso!', 'success')
    return redirect(url_for('admin_panel'))


@app.route('/admin/winner_details/<int:raffle_id>')
@login_required
def winner_details(raffle_id):
    """Retorna detalhes do ganhador em JSON"""
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403
    
    db = database.get_db()
    
    # Buscar dados da rifa e do ganhador
    query = '''
        SELECT r.*, t.number as winning_number, t.purchase_date,
               u.username, u.email, u.full_name, u.phone, u.cpf, u.pix_key, u.address
        FROM raffle r
        LEFT JOIN ticket t ON r.winner_ticket_id = t.id
        LEFT JOIN user u ON t.user_id = u.id
        WHERE r.id = ?
    '''
    result = db.execute(query, (raffle_id,)).fetchone()
    
    if not result or not result['winner_ticket_id']:
        return jsonify({'error': 'No winner found'}), 404
    
    return jsonify({
        'raffle_title': result['title'],
        'full_name': result['full_name'],
        'username': result['username'],
        'email': result['email'],
        'phone': result['phone'],
        'cpf': result['cpf'],
        'pix_key': result['pix_key'],
        'address': result['address'],
        'winning_number': result['winning_number'],
        'purchase_date': result['purchase_date'],
        'raffle_price': float(result['price'])
    })


# Inicialização do DB via comando
@app.cli.command('init-db')
def init_db_command():
    database.init_db()
    print('Initialized the database.')

if __name__ == '__main__':
    if not os.path.exists('rifamaster.db'):
        with app.app_context():
            database.init_db()
            print("Banco de dados inicializado automaticamente.")
            
    app.run(debug=True)
