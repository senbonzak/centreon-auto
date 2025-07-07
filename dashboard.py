# dashboard.py - Version modulaire

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///centreon_dashboard.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Extensions
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Importer les modèles
from models import AlertAcknowledgment, SystemMetrics

# Importer et enregistrer les routes API
from api_routes import register_api_routes
register_api_routes(app, db, AlertAcknowledgment, SystemMetrics)

# Routes principales
@app.route('/')
def index():
    return render_template('dashboard.html')

@app.route('/history')
def history():
    return render_template('history.html')

# WebSocket handlers
from websocket_handlers import register_websocket_handlers
register_websocket_handlers(socketio)

# Fonctions utilitaires
from utils import save_acknowledgment, save_system_metrics

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('FLASK_PORT', 5000))
    
    socketio.run(app, debug=debug_mode, host='0.0.0.0', port=port)
