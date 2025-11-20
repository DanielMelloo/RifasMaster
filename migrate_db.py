import sqlite3
import os

def migrate_db():
    db_path = 'rifamaster.db'
    
    if not os.path.exists(db_path):
        print("Banco de dados não encontrado.")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Colunas a adicionar
    new_columns = [
        ('full_name', 'TEXT'),
        ('phone', 'TEXT'),
        ('pix_key', 'TEXT'),
        ('address', 'TEXT'),
        ('cpf', 'TEXT')
    ]
    
    print("Iniciando migração...")
    
    for col_name, col_type in new_columns:
        try:
            cursor.execute(f"ALTER TABLE user ADD COLUMN {col_name} {col_type}")
            print(f"Coluna '{col_name}' adicionada com sucesso.")
        except sqlite3.OperationalError as e:
            if "duplicate column name" in str(e):
                print(f"Coluna '{col_name}' já existe.")
            else:
                print(f"Erro ao adicionar coluna '{col_name}': {e}")
                
    conn.commit()
    conn.close()
    print("Migração concluída.")

if __name__ == '__main__':
    migrate_db()
