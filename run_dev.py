import os
from pathlib import Path
from jinja2 import FileSystemLoader

# ensure local sqlite usage unless explicitly overridden
os.environ.setdefault('DATABASE_URL', 'sqlite:///./data/bossjy.db')
os.environ.setdefault('FLASK_ENV', 'development')

from app.web_app import app, socketio

root = Path(__file__).resolve().parent
app.template_folder = str(root / 'web' / 'templates')
app.static_folder = str(root / 'web' / 'static')
app.jinja_loader = FileSystemLoader(app.template_folder)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=9001, debug=False, allow_unsafe_werkzeug=True)
