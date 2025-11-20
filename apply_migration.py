import sqlite3

# Aplicar migration
conn = sqlite3.connect('rifamaster.db')
cursor = conn.cursor()

# Adicionar colunas de pagamento à tabela 'user'
try:
    cursor.execute("ALTER TABLE user ADD COLUMN full_name TEXT")
except sqlite3.OperationalError:
    pass  # Coluna já existe

try:
    cursor.execute("ALTER TABLE user ADD COLUMN phone TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE user ADD COLUMN cpf TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE user ADD COLUMN pix_key TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE user ADD COLUMN address TEXT")
except sqlite3.OperationalError:
    pass

# Adicionar colunas de pagamento à tabela 'ticket'
try:
    cursor.execute("ALTER TABLE ticket ADD COLUMN payment_txid TEXT UNIQUE")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE ticket ADD COLUMN payment_status TEXT DEFAULT 'pending'")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE ticket ADD COLUMN pix_qrcode TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE ticket ADD COLUMN pix_copy_paste TEXT")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE ticket ADD COLUMN payment_expiration TIMESTAMP")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE ticket ADD COLUMN paid_at TIMESTAMP")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("ALTER TABLE ticket ADD COLUMN total_price REAL")
except sqlite3.OperationalError:
    pass

# Criar índices
try:
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ticket_payment_txid ON ticket(payment_txid)")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ticket_payment_status ON ticket(payment_status)")
except sqlite3.OperationalError:
    pass

try:
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_ticket_user_raffle ON ticket(user_id, raffle_id)")
except sqlite3.OperationalError:
    pass

conn.commit()
conn.close()

print("✅ Migration aplicada com sucesso!")
