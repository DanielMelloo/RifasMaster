import sys
import sqlite3
from werkzeug.security import generate_password_hash
from app import app
import database

def create_admin(username, email, password):
    with app.app_context():
        db = database.get_db()
        
        # Verificar se usuário já existe
        existing_user = db.execute('SELECT id FROM user WHERE email = ?', (email,)).fetchone()
        if existing_user:
            print(f"Erro: Usuário com email {email} já existe.")
            return

        # Criar hash da senha
        hashed_password = generate_password_hash(password)
        
        try:
            db.execute(
                'INSERT INTO user (username, email, password_hash, is_admin) VALUES (?, ?, ?, ?)',
                (username, email, hashed_password, True)
            )
            db.commit()
            print(f"Sucesso: Admin '{username}' ({email}) criado com sucesso!")
        except sqlite3.Error as e:
            print(f"Erro ao criar admin: {e}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Uso: python create_admin.py <username> <email> <password>")
        print("Exemplo: python create_admin.py admin admin@rifamaster.com senha123")
    else:
        create_admin(sys.argv[1], sys.argv[2], sys.argv[3])
