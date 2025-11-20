import sqlite3

def create_payment_table():
    conn = sqlite3.connect('rifamaster.db')
    cursor = conn.cursor()
    
    cursor.execute('DROP TABLE IF EXISTS payment')
    
    cursor.execute('''
    CREATE TABLE payment (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        txid TEXT UNIQUE NOT NULL,
        user_id INTEGER NOT NULL,
        raffle_id INTEGER NOT NULL,
        amount REAL NOT NULL,
        status TEXT DEFAULT 'pending',
        ticket_count INTEGER DEFAULT 0,
        type TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES user (id),
        FOREIGN KEY (raffle_id) REFERENCES raffle (id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("Payment table created successfully.")

if __name__ == '__main__':
    create_payment_table()
