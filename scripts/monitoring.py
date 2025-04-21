import requests
import json
import urllib3
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Désactiver les avertissements pour les certificats non vérifiés
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===============================================
# CONFIGURATION
# ===============================================

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

# Répertoires et fichiers
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
LOG_DIR = os.getenv("LOG_DIR", "logs")

# Obtenir la date du jour pour les noms de fichiers
today = datetime.now().strftime("%Y-%m-%d")

# Chemin des fichiers de sortie et de logs
OUTPUT_FILE = os.getenv("OUTPUT_FILE", os.path.join(OUTPUT_DIR, "alerts_output.json"))
LOG_FILE = os.getenv("LOG_FILE", os.path.join(LOG_DIR, f"{today}_centreon.log"))

# S'assurer que les chemins sont absolus
if not os.path.isabs(OUTPUT_FILE):
    OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", OUTPUT_FILE)

if not os.path.isabs(LOG_FILE):
    LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", LOG_FILE)

# Configuration des logs
LOGGING_CONFIG = {
    'level': os.getenv("LOG_LEVEL", "INFO").upper(),
    'format': "%(asctime)s [%(levelname)s] - %(message)s",
    'datefmt': "%Y-%m-%d %H:%M:%S"
}

# ===============================================
# FONCTIONS
# ===============================================

def configure_logging():
    """Configure le système de logging"""
    # Créer les répertoires s'ils n'existent pas
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
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

def get_token():
    """Obtient un token d'authentification depuis l'API Centreon"""
    url = f"{API_URL}/login"
    headers = {"Content-Type": "application/json"}
    payload = {
        "security": {
            "credentials": {
                "login": LOGIN,
                "password": PASSWORD
            }
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload, verify=False)
        response.raise_for_status()
        token = response.json()["security"]["token"]
        logging.info("Connexion à l'API Centreon réussie")
        return token
    except Exception as e:
        logging.error(f"Erreur de connexion à l'API Centreon: {e}")
        return None

def get_unhandled_alerts(token):
    """Récupère les alertes non acquittées depuis l'API Centreon"""
    if not token:
        logging.error("Token d'authentification manquant")
        return []
    
    url = f"{API_URL}/monitoring/resources"
    headers = {
        "Content-Type": "application/json",
        "X-AUTH-TOKEN": token
    }
    params = {
        "page": 1,
        "limit": ALERT_LIMIT,
        "states[]": "unhandled_problems",
        "types[]": "service",
        "statuses[]": ["WARNING", "DOWN", "CRITICAL", "UNKNOWN"]
    }
    try:
        response = requests.get(url, headers=headers, params=params, verify=False)
        response.raise_for_status()
        alerts = response.json().get("result", [])
        logging.info(f"{len(alerts)} alertes non acquittées trouvées")
        return alerts
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des alertes: {e}")
        return []

def acknowledge_service(token, service_id, host_id, comment="Auto ACK by Miguel"):
    """Acquitte un service en alerte"""
    if not token:
        logging.error("Token d'authentification manquant")
        return False
        
    url = f"{API_URL}/monitoring/resources/acknowledge"
    headers = {
        "Content-Type": "application/json",
        "X-AUTH-TOKEN": token
    }
    payload = {
        "acknowledgement": {
            "comment": comment,
            "is_notify_contacts": False,
            "is_persistent_comment": True,
            "is_sticky": True,
            "with_services": False
        },
        "resources": [
            {
                "type": "service",
                "id": service_id,
                "parent": {
                    "id": host_id
                }
            }
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, verify=False)
        response.raise_for_status()
        logging.info(f"Service {service_id} acquitté sur l'hôte {host_id}")
        return True
    except Exception as e:
        logging.error(f"Échec de l'acquittement du service {service_id} sur l'hôte {host_id}: {e}")
        return False

def save_alerts_to_file(alerts):
    """Sauvegarde les alertes dans un fichier JSON"""
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(alerts, f, indent=2)
        logging.info(f"Alertes sauvegardées dans {OUTPUT_FILE}")
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde des alertes: {e}")

def main():
    """Fonction principale du script"""
    # Configuration du système de logging
    configure_logging()
    
    logging.info("=== Démarrage du script d'acquittement des alertes ===")
    
    # Récupération du token
    token = get_token()
    if not token:
        logging.error("Impossible de continuer sans token d'authentification")
        return
    
    # Récupération des alertes non acquittées
    alerts = get_unhandled_alerts(token)
    
    if not alerts:
        logging.info("Aucune alerte à traiter")
        return
        
    # Sauvegarde des alertes dans un fichier JSON
    save_alerts_to_file(alerts)
    
    # Acquittement des alertes
    successful_acks = 0
    for alert in alerts:
        service_id = alert.get("service_id")
        host_id = alert.get("host_id")
        service_name = alert.get("name", "Inconnu")
        host_name = alert.get("parent", {}).get("name", "Inconnu")
        
        if service_id and host_id:
            if acknowledge_service(token, service_id, host_id):
                successful_acks += 1
                logging.info(f"Service '{service_name}' acquitté sur l'hôte '{host_name}'")
    
    logging.info(f"Acquittement terminé: {successful_acks}/{len(alerts)} alertes traitées avec succès")
    logging.info("=== Fin du script d'acquittement des alertes ===")

if __name__ == "__main__":
    main()