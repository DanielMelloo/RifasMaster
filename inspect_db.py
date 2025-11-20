import sqlite3

DB_PATH = 'rifamaster.db'

def inspect_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("--- Inspecting Raffle promo_end ---")
    cursor.execute("SELECT id, title, promo_end FROM raffle")
    rows = cursor.fetchall()
    
    for row in rows:
        print(f"ID: {row[0]}, Title: {row[1]}, promo_end: '{row[2]}' (Type: {type(row[2])})")
        
    conn.close()

if __name__ == '__main__':
    inspect_db()
