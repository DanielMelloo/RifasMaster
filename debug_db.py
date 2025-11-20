import sqlite3
import datetime

DB_PATH = 'rifamaster.db'

def test_crash():
    print("--- Attempting to reproduce crash with PARSE_DECLTYPES ---")
    try:
        conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM raffle WHERE status = 'active'")
        rows = cursor.fetchall()
        print("Success! Rows fetched:")
        for row in rows:
            print(row)
        conn.close()
    except Exception as e:
        print(f"CRASHED as expected: {e}")

def inspect_raw():
    print("\n--- Inspecting RAW data (no converters) ---")
    conn = sqlite3.connect(DB_PATH) # No detect_types
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, promo_end FROM raffle")
    rows = cursor.fetchall()
    for row in rows:
        id, title, promo_end = row
        print(f"ID: {id}")
        print(f"Title: {title}")
        print(f"promo_end (raw): {repr(promo_end)}")
        if isinstance(promo_end, str):
            print(f"Length: {len(promo_end)}")
            print(f"Bytes: {promo_end.encode('utf-8')}")
    conn.close()

if __name__ == '__main__':
    test_crash()
    inspect_raw()
