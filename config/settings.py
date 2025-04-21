import os
import logging
from dotenv import load_dotenv
import sys

# Charger les variables depuis le fichier .env s'il existe
load_dotenv()

# API Centreon
API_URL = os.getenv("CENTREON_API_URL")
if not API_URL:
    print("ERREUR: Variable d'environnement CENTREON_API_URL non définie")
    sys.exit(1)

# Identifiants
LOGIN = os.getenv("CENTREON_LOGIN")
PASSWORD = os.getenv("CENTREON_PASSWORD")
if not LOGIN or not PASSWORD:
    print("ERREUR: Variables d'environnement CENTREON_LOGIN et/ou CENTREON_PASSWORD non définies")
    sys.exit(1)

# Limite d'alertes
ALERT_LIMIT = int(os.getenv("ALERT_LIMIT", 100))

# Fichier de sortie
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
OUTPUT_FILE = os.getenv("OUTPUT_FILE", os.path.join(OUTPUT_DIR, "alerts_output.json"))

# Répertoire de logs
LOG_DIR = os.getenv("LOG_DIR", "logs")

# Fichier de logs - utilise la date du jour pour le nom de fichier
from datetime import datetime
today = datetime.now().strftime("%Y-%m-%d")
LOG_FILE = os.getenv("LOG_FILE", os.path.join(LOG_DIR, f"{today}_centreon.log"))

# Configuration des logs
LOGGING_CONFIG = {
    'level': os.getenv("LOG_LEVEL", "INFO").upper(),
    'format': "%(asctime)s [%(levelname)s] - %(message)s",
    'datefmt': "%Y-%m-%d %H:%M:%S"
}

def configure_logging():
    """Configure le système de logging"""
    # Crée le répertoire de logs s'il n'existe pas
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    # Configuration du système de logging
    logging.basicConfig(
        filename=LOG_FILE,
        level=getattr(logging, LOGGING_CONFIG['level']),
        format=LOGGING_CONFIG['format'],
        datefmt=LOGGING_CONFIG['datefmt']
    )
    
    # Ajouter un handler pour afficher les logs dans la console
    console = logging.StreamHandler()
    console.setLevel(getattr(logging, LOGGING_CONFIG['level']))
    formatter = logging.Formatter(LOGGING_CONFIG['format'], LOGGING_CONFIG['datefmt'])
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)
    
    logging.info("Système de logging configuré")

# Vérification supplémentaire pour les chemins relatifs
if not os.path.isabs(OUTPUT_FILE):
    OUTPUT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), OUTPUT_FILE)

if not os.path.isabs(LOG_FILE):
    LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), LOG_FILE)