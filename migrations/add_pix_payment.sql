-- Migração: Adicionar suporte a pagamentos PIX via Efí
-- Execute este arquivo para atualizar o banco de dados existente

-- Adicionar colunas de pagamento à tabela 'user'
ALTER TABLE user ADD COLUMN full_name TEXT;
ALTER TABLE user ADD COLUMN phone TEXT;
ALTER TABLE user ADD COLUMN cpf TEXT;
ALTER TABLE user ADD COLUMN pix_key TEXT;
ALTER TABLE user ADD COLUMN address TEXT;

-- Adicionar colunas de pagamento à tabela 'ticket'
ALTER TABLE ticket ADD COLUMN payment_txid TEXT UNIQUE;
ALTER TABLE ticket ADD COLUMN payment_status TEXT DEFAULT 'pending';
ALTER TABLE ticket ADD COLUMN pix_qrcode TEXT;
ALTER TABLE ticket ADD COLUMN pix_copy_paste TEXT;
ALTER TABLE ticket ADD COLUMN payment_expiration TIMESTAMP;
ALTER TABLE ticket ADD COLUMN paid_at TIMESTAMP;
ALTER TABLE ticket ADD COLUMN total_price REAL;

-- Índices para melhorar performance de consultas
CREATE INDEX IF NOT EXISTS idx_ticket_payment_txid ON ticket(payment_txid);
CREATE INDEX IF NOT EXISTS idx_ticket_payment_status ON ticket(payment_status);
CREATE INDEX IF NOT EXISTS idx_ticket_user_raffle ON ticket(user_id, raffle_id);
