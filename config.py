"""
Configuração para rodar o Flask em subpath /Rifa
"""

class Config:
    # Subdiretório base
    APPLICATION_ROOT = '/Rifa'
    
    # Outras configurações
    SECRET_KEY = 'your_secret_key_here'  # Trocar em produção
    SESSION_COOKIE_PATH = '/Rifa/'
    
    # Upload
    UPLOAD_FOLDER = 'static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
