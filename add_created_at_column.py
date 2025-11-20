import sqlite3
from datetime import datetime

def add_created_at_column():
    """Adiciona coluna created_at à tabela ticket"""
    conn = sqlite3.connect('rifamaster.db')
    cursor = conn.cursor()
    
    # Verificar se a coluna já existe
    cursor.execute("PRAGMA table_info(ticket)")
    columns = {row[1] for row in cursor.fetchall()}
    
    if 'created_at' not in columns:
        # Adicionar coluna (SQLite não suporta DEFAULT CURRENT_TIMESTAMP em ALTER TABLE)
        cursor.execute('ALTER TABLE ticket ADD COLUMN created_at TIMESTAMP')
        
        # Atualizar todos os registros existentes com timestamp atual
        cursor.execute("UPDATE ticket SET created_at = datetime('now') WHERE created_at IS NULL")
        
        print("✓ Adicionada coluna 'created_at' à tabela ticket")
        print("✓ Registros existentes atualizados com timestamp atual")
    else:
        print("✓ Coluna 'created_at' já existe")
    
    conn.commit()
    conn.close()
    print("\n✅ Migração concluída!")

if __name__ == '__main__':
    add_created_at_column()
