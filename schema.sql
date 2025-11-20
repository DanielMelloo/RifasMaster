DROP TABLE IF EXISTS user;
DROP TABLE IF EXISTS raffle;
DROP TABLE IF EXISTS ticket;

CREATE TABLE user (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    is_admin BOOLEAN DEFAULT 0,
    full_name TEXT,
    phone TEXT,
    cpf TEXT,
    pix_key TEXT,
    address TEXT
);

CREATE TABLE raffle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    total_numbers INTEGER NOT NULL,
    image_url TEXT,
    status TEXT DEFAULT 'active',
    type TEXT DEFAULT 'manual',
    winner_ticket_id INTEGER,
    promo_price REAL,
    promo_end TIMESTAMP,
    FOREIGN KEY (winner_ticket_id) REFERENCES ticket (id)
);

CREATE TABLE ticket (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    raffle_id INTEGER NOT NULL,
    number INTEGER, -- Nullable for pending random tickets
    status TEXT DEFAULT 'pending',
    purchase_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_txid TEXT UNIQUE,
    payment_status TEXT DEFAULT 'pending',
    pix_qrcode TEXT,
    pix_copy_paste TEXT,
    payment_expiration TIMESTAMP,
    paid_at TIMESTAMP,
    total_price REAL,
    FOREIGN KEY (user_id) REFERENCES user (id),
    FOREIGN KEY (raffle_id) REFERENCES raffle (id)
);

-- Índices para performance
CREATE INDEX IF NOT EXISTS idx_ticket_payment_txid ON ticket(payment_txid);
CREATE INDEX IF NOT EXISTS idx_ticket_payment_status ON ticket(payment_status);
CREATE INDEX IF NOT EXISTS idx_ticket_user_raffle ON ticket(user_id, raffle_id);
