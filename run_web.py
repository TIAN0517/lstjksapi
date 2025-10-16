import os
from pathlib import Path

# Ensure the repository root is on sys.path when running from arbitrary locations
ROOT_DIR = Path(__file__).resolve().parent

# Default to SQLite if DATABASE_URL not provided
os.environ.setdefault('DATABASE_URL', 'sqlite:///./data/bossjy.db')
os.environ.setdefault('FLASK_ENV', 'production')

from services.fastapi.web_app import app, socketio  # noqa: E402


if __name__ == '__main__':
    port = int(os.getenv('PORT', '5000'))
    debug = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'
    socketio.run(app, host='0.0.0.0', port=port, debug=debug, allow_unsafe_werkzeug=True)
