import sqlite3
import click
from flask import current_app, g
import datetime

def convert_timestamp(val):
    """Custom timestamp converter to handle multiple formats."""
    if not val:
        return None
    s = val.decode('utf-8')
    # Try standard format first
    try:
        return datetime.datetime.fromisoformat(s)
    except ValueError:
        pass
    # Try format without seconds
    try:
        return datetime.datetime.strptime(s, '%Y-%m-%d %H:%M')
    except ValueError:
        pass
    # Fallback to legacy sqlite3 default behavior (space separator)
    try:
        return datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        pass
    return s

# Register the converter
sqlite3.register_converter("TIMESTAMP", convert_timestamp)

def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()

    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))

def init_app(app):
    app.teardown_appcontext(close_db)
