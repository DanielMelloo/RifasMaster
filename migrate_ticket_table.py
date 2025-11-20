import sqlite3

def add_payment_columns():
    """Adiciona colunas de pagamento à tabela ticket"""
    conn = sqlite3.connect('rifamaster.db')
    cursor = conn.cursor()
    
    # Verificar se as colunas já existem
    cursor.execute("PRAGMA table_info(ticket)")
    columns = {row[1] for row in cursor.fetchall()}
    
    # Adicionar payment_txid se não existir
    if 'payment_txid' not in columns:
        cursor.execute('ALTER TABLE ticket ADD COLUMN payment_txid TEXT')
        print("✓ Adicionada coluna 'payment_txid'")
    else:
        print("✓ Coluna 'payment_txid' já existe")
    
    # Adicionar pix_qrcode se não existir
    if 'pix_qrcode' not in columns:
        cursor.execute('ALTER TABLE ticket ADD COLUMN pix_qrcode TEXT')
        print("✓ Adicionada coluna 'pix_qrcode'")
    else:
        print("✓ Coluna 'pix_qrcode' já existe")
    
    # Adicionar pix_copy_paste se não existir
    if 'pix_copy_paste' not in columns:
        cursor.execute('ALTER TABLE ticket ADD COLUMN pix_copy_paste TEXT')
        print("✓ Adicionada coluna 'pix_copy_paste'")
    else:
        print("✓ Coluna 'pix_copy_paste' já existe")
    
    # Adicionar payment_expiration se não existir
    if 'payment_expiration' not in columns:
        cursor.execute('ALTER TABLE ticket ADD COLUMN payment_expiration TEXT')
        print("✓ Adicionada coluna 'payment_expiration'")
    else:
        print("✓ Coluna 'payment_expiration' já existe")
    
    # Adicionar paid_at se não existir (usado no webhook)
    if 'paid_at' not in columns:
        cursor.execute('ALTER TABLE ticket ADD COLUMN paid_at TIMESTAMP')
        print("✓ Adicionada coluna 'paid_at'")
    else:
        print("✓ Coluna 'paid_at' já existe")
    
    conn.commit()
    conn.close()
    print("\n✅ Migração concluída com sucesso!")

if __name__ == '__main__':
    add_payment_columns()
