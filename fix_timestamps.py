import sqlite3
import os

DB_PATH = 'rifamaster.db'

def fix_timestamps():
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print("Checking for malformed timestamps...")
        
        # 1. Fix 'T' separator
        cursor.execute("SELECT count(*) FROM raffle WHERE promo_end LIKE '%T%'")
        count_t = cursor.fetchone()[0]
        
        if count_t > 0:
            print(f"Found {count_t} rows with 'T' separator. Fixing...")
            cursor.execute("UPDATE raffle SET promo_end = REPLACE(promo_end, 'T', ' ') WHERE promo_end LIKE '%T%'")
            print("Fixed 'T' separators.")
        else:
            print("No rows with 'T' separator found.")

        # 3. Fix missing seconds (YYYY-MM-DD HH:MM -> YYYY-MM-DD HH:MM:00)
        cursor.execute("SELECT id, promo_end FROM raffle WHERE promo_end IS NOT NULL")
        rows = cursor.fetchall()
        
        fixed_count = 0
        for row in rows:
            raffle_id = row[0]
            promo_end = row[1]
            
            if isinstance(promo_end, str):
                original_promo_end = promo_end
                promo_end = promo_end.strip()
                
                # Fix 'T' if present
                if 'T' in promo_end:
                    promo_end = promo_end.replace('T', ' ')
                
                # Check if it looks like YYYY-MM-DD HH:MM (length 16)
                # Or if it just has one colon in the time part
                if len(promo_end) == 16 and promo_end.count(':') == 1:
                    promo_end += ':00'
                
                # Update if changed
                if promo_end != original_promo_end:
                    print(f"Fixing ID {raffle_id}: '{original_promo_end}' -> '{promo_end}'")
                    cursor.execute("UPDATE raffle SET promo_end = ? WHERE id = ?", (promo_end, raffle_id))
                    fixed_count += 1
        
        if fixed_count > 0:
            print(f"Fixed {fixed_count} rows.")
        else:
            print("No rows needed fixing.")
            
        conn.commit()
        print("Database timestamp fix completed successfully.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error fixing timestamps: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    fix_timestamps()
