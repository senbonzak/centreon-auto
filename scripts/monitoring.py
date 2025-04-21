import requests
import json
import urllib3
import os
import logging
import sys
from datetime import datetime

# Ajouter le répertoire parent au chemin pour trouver les modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings

# Configuration des logs
settings.configure_logging()
logger = logging.getLogger(__name__)

# Désactiver les avertissements pour les certificats non vérifiés
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def get_token():
    """Obtient un token d'authentification depuis l'API Centreon"""
    url = f"{settings.API_URL}/login"
    headers = {"Content-Type": "application/json"}
    payload = {
        "security": {
            "credentials": {
                "login": settings.LOGIN,
                "password": settings.PASSWORD
            }
        }
    }
    try:
        response = requests.post(url, headers=headers, json=payload, verify=False)
        response.raise_for_status()
        token = response.json()["security"]["token"]
        logger.info("Connexion à l'API Centreon réussie")
        return token
    except Exception as e:
        logger.error(f"Erreur de connexion à l'API Centreon: {e}")
        return None

def get_unhandled_alerts(token):
    """Récupère les alertes non acquittées depuis l'API Centreon"""
    if not token:
        logger.error("Token d'authentification manquant")
        return []
    
    url = f"{settings.API_URL}/monitoring/resources"
    headers = {
        "Content-Type": "application/json",
        "X-AUTH-TOKEN": token
    }
    params = {
        "page": 1,
        "limit": settings.ALERT_LIMIT,
        "states[]": "unhandled_problems",
        "types[]": "service",
        "statuses[]": ["WARNING", "DOWN", "CRITICAL", "UNKNOWN"]
    }
    try:
        response = requests.get(url, headers=headers, params=params, verify=False)
        response.raise_for_status()
        alerts = response.json().get("result", [])
        logger.info(f"{len(alerts)} alertes non acquittées trouvées")
        return alerts
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des alertes: {e}")
        return []

def acknowledge_service(token, service_id, host_id, comment="Auto ACK by DJ Mag 🧠"):
    """Acquitte un service en alerte"""
    if not token:
        logger.error("Token d'authentification manquant")
        return False
        
    url = f"{settings.API_URL}/monitoring/resources/acknowledge"
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
        logger.info(f"Service {service_id} acquitté sur l'hôte {host_id}")
        return True
    except Exception as e:
        logger.error(f"Échec de l'acquittement du service {service_id} sur l'hôte {host_id}: {e}")
        return False

def save_alerts_to_file(alerts):
    """Sauvegarde les alertes dans un fichier JSON"""
    output_path = settings.OUTPUT_FILE
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(alerts, f, indent=2)
        logger.info(f"Alertes sauvegardées dans {output_path}")
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde des alertes: {e}")

def main():
    """Fonction principale du script"""
    logger.info("Démarrage du script d'acquittement des alertes")
    
    token = get_token()
    if not token:
        logger.error("Impossible de continuer sans token d'authentification")
        return
    
    alerts = get_unhandled_alerts(token)
    
    if not alerts:
        logger.info("Aucune alerte à traiter")
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
                logger.info(f"Service '{service_name}' acquitté sur l'hôte '{host_name}'")
    
    logger.info(f"Acquittement terminé: {successful_acks}/{len(alerts)} alertes traitées avec succès")

if __name__ == "__main__":
    main()