import os
from dotenv import load_dotenv

# Charger les variables depuis le fichier .env s'il existe
load_dotenv()

# URL de base de l'API Centreon
API_URL = os.getenv("CENTREON_API_URL")

# Identifiants d'accès
LOGIN = os.getenv("CENTREON_LOGIN")
PASSWORD = os.getenv("CENTREON_PASSWORD")

# Nombre maximum d’alertes à récupérer
ALERT_LIMIT = int(os.getenv("ALERT_LIMIT", 100))

# Nom du fichier de sortie
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "output/alerts_output.json")

# Fichier de logs (futur usage)
LOG_FILE = os.getenv("LOG_FILE", "logs/alerts.log")

LOGGING_CONFIG = {
    'level': os.getenv("LOG_LEVEL", "INFO").upper(),
    'format': "%(asctime)s [%(levelname)s] - %(message)s",
    'datefmt': "%Y-%m-%d %H:%M:%S"
}


import os
import logging
from dotenv import load_dotenv

# Charger les variables depuis le fichier .env s'il existe
load_dotenv()

# API Centreon
API_URL = os.getenv("CENTREON_API_URL")

# Identifiants
LOGIN = os.getenv("CENTREON_LOGIN")
PASSWORD = os.getenv("CENTREON_PASSWORD")

# Limite d’alertes
ALERT_LIMIT = int(os.getenv("ALERT_LIMIT", 100))

# Fichier de sortie
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "output/alerts_output.json")

# Fichier de logs
LOG_FILE = os.getenv("LOG_FILE", f"logs/alerts.log")

# Configuration des logs
LOGGING_CONFIG = {
    'level': os.getenv("LOG_LEVEL", "INFO").upper(),
    'format': "%(asctime)s [%(levelname)s] - %(message)s",
    'datefmt': "%Y-%m-%d %H:%M:%S"
}

def configure_logging():
    log_path = LOG_FILE if os.path.isabs(LOG_FILE) else os.path.join(os.getcwd(), LOG_FILE)
    os.makedirs(os.path.dirname(log_path), exist_ok=True)

    logging.basicConfig(
        filename=log_path,
        level=LOGGING_CONFIG['level'],
        format=LOGGING_CONFIG['format'],
        datefmt=LOGGING_CONFIG['datefmt']
    )
