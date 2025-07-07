import requests
import json
import urllib3
import os
import sys
import logging
import time
from datetime import datetime
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from flask import Flask

# Désactiver les avertissements pour les certificats non vérifiés
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===============================================
# CONFIGURATION
# ===============================================

# Charger les variables depuis le fichier .env s'il existe
load_dotenv()

# Configuration Flask pour la base de données (si le dashboard est en cours d'exécution)
try:
    # Essayer d'importer l'app dashboard si elle existe
    from dashboard import app, db, save_acknowledgment, save_system_metrics
    DASHBOARD_ENABLED = True
    print("Dashboard détecté - Intégration activée")
except ImportError:
    DASHBOARD_ENABLED = False
    print("Dashboard non détecté - Mode standalone")

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
    
    start_time = time.time()
    try:
        response = requests.post(url, headers=headers, json=payload, verify=False)
        response.raise_for_status()
        token = response.json()["security"]["token"]
        response_time = time.time() - start_time
        
        logging.info(f"Connexion à l'API Centreon réussie (temps: {response_time:.3f}s)")
        return token, response_time
    except Exception as e:
        response_time = time.time() - start_time
        logging.error(f"Erreur de connexion à l'API Centreon: {e} (temps: {response_time:.3f}s)")
        return None, response_time

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
    
    start_time = time.time()
    try:
        response = requests.get(url, headers=headers, params=params, verify=False)
        response.raise_for_status()
        alerts = response.json().get("result", [])
        response_time = time.time() - start_time
        
        logging.info(f"{len(alerts)} alertes non acquittées trouvées (temps: {response_time:.3f}s)")
        return alerts, response_time
    except Exception as e:
        response_time = time.time() - start_time
        logging.error(f"Erreur lors de la récupération des alertes: {e} (temps: {response_time:.3f}s)")
        return [], response_time

def acknowledge_service(token, service_id, host_id, service_name=None, host_name=None, comment="Auto ACK by Miguel"):
    """Acquitte un service en alerte"""
    if not token:
        logging.error("Token d'authentification manquant")
        return False, "Token manquant", None
        
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

    start_time = time.time()
    try:
        response = requests.post(url, headers=headers, json=payload, verify=False)
        response.raise_for_status()
        response_time = time.time() - start_time
        
        logging.info(f"Service {service_id} acquitté sur l'hôte {host_id} (temps: {response_time:.3f}s)")
        
        # Sauvegarder dans le dashboard si disponible
        if DASHBOARD_ENABLED:
            with app.app_context():
                save_acknowledgment(
                    service_id=service_id,
                    host_id=host_id,
                    service_name=service_name,
                    host_name=host_name,
                    success=True,
                    response_time=response_time
                )
        
        return True, None, response_time
    except Exception as e:
        response_time = time.time() - start_time
        error_msg = str(e)
        logging.error(f"Échec de l'acquittement du service {service_id} sur l'hôte {host_id}: {error_msg} (temps: {response_time:.3f}s)")
        
        # Sauvegarder l'échec dans le dashboard si disponible
        if DASHBOARD_ENABLED:
            with app.app_context():
                save_acknowledgment(
                    service_id=service_id,
                    host_id=host_id,
                    service_name=service_name,
                    host_name=host_name,
                    success=False,
                    error_message=error_msg,
                    response_time=response_time
                )
        
        return False, error_msg, response_time

def save_alerts_to_file(alerts):
    """Sauvegarde les alertes dans un fichier JSON"""
    try:
        # Enrichir les alertes avec timestamp
        enriched_alerts = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_count": len(alerts),
            "alerts": alerts
        }
        
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(enriched_alerts, f, indent=2)
        logging.info(f"Alertes sauvegardées dans {OUTPUT_FILE}")
    except Exception as e:
        logging.error(f"Erreur lors de la sauvegarde des alertes: {e}")

def extract_alert_info(alert):
    """Extrait les informations importantes d'une alerte"""
    return {
        'service_id': alert.get("service_id"),
        'host_id': alert.get("host_id"),
        'service_name': alert.get("name", "Inconnu"),
        'host_name': alert.get("parent", {}).get("name", "Inconnu"),
        'status': alert.get("status", {}).get("name", "UNKNOWN"),
        'output': alert.get("information", "")
    }

def main():
    """Fonction principale du script"""
    script_start_time = time.time()
    
    # Configuration du système de logging
    configure_logging()
    
    logging.info("=== Démarrage du script d'acquittement des alertes ===")
    
    # Métriques de performance
    metrics = {
        'api_response_time': 0,
        'total_alerts': 0,
        'successful_acks': 0,
        'failed_acks': 0,
        'errors': []
    }
    
    # Récupération du token
    token, token_response_time = get_token()
    metrics['api_response_time'] = token_response_time
    
    if not token:
        logging.error("Impossible de continuer sans token d'authentification")
        if DASHBOARD_ENABLED:
            with app.app_context():
                save_system_metrics(
                    api_response_time=token_response_time,
                    total_alerts=0,
                    successful_acks=0,
                    failed_acks=1,
                    execution_time=time.time() - script_start_time
                )
        return
    
    # Récupération des alertes non acquittées
    alerts, alerts_response_time = get_unhandled_alerts(token)
    metrics['api_response_time'] = max(metrics['api_response_time'], alerts_response_time)
    metrics['total_alerts'] = len(alerts)
    
    if not alerts:
        logging.info("Aucune alerte à traiter")
        script_execution_time = time.time() - script_start_time
        
        if DASHBOARD_ENABLED:
            with app.app_context():
                save_system_metrics(
                    api_response_time=metrics['api_response_time'],
                    total_alerts=0,
                    successful_acks=0,
                    failed_acks=0,
                    execution_time=script_execution_time
                )
        return
        
    # Sauvegarde des alertes dans un fichier JSON
    save_alerts_to_file(alerts)
    
    # Acquittement des alertes
    logging.info(f"Début de l'acquittement de {len(alerts)} alertes...")
    
    for i, alert in enumerate(alerts, 1):
        alert_info = extract_alert_info(alert)
        
        logging.info(f"[{i}/{len(alerts)}] Traitement de l'alerte: {alert_info['service_name']} sur {alert_info['host_name']}")
        
        if alert_info['service_id'] and alert_info['host_id']:
            success, error_msg, response_time = acknowledge_service(
                token, 
                alert_info['service_id'], 
                alert_info['host_id'],
                alert_info['service_name'],
                alert_info['host_name']
            )
            
            if success:
                metrics['successful_acks'] += 1
                logging.info(f"✓ Service '{alert_info['service_name']}' acquitté sur l'hôte '{alert_info['host_name']}'")
            else:
                metrics['failed_acks'] += 1
                metrics['errors'].append({
                    'service': alert_info['service_name'],
                    'host': alert_info['host_name'],
                    'error': error_msg
                })
                logging.error(f"✗ Échec d'acquittement pour '{alert_info['service_name']}' sur '{alert_info['host_name']}': {error_msg}")
        else:
            metrics['failed_acks'] += 1
            error_msg = "Service ID ou Host ID manquant"
            metrics['errors'].append({
                'service': alert_info['service_name'],
                'host': alert_info['host_name'],
                'error': error_msg
            })
            logging.error(f"✗ {error_msg} pour l'alerte: {alert_info}")
    
    # Calcul du temps d'exécution total
    script_execution_time = time.time() - script_start_time
    
    # Résumé final
    logging.info(f"=== Résumé de l'exécution ===")
    logging.info(f"Alertes trouvées: {metrics['total_alerts']}")
    logging.info(f"Acquittements réussis: {metrics['successful_acks']}")
    logging.info(f"Acquittements échoués: {metrics['failed_acks']}")
    logging.info(f"Taux de succès: {(metrics['successful_acks'] / metrics['total_alerts'] * 100):.1f}%" if metrics['total_alerts'] > 0 else "N/A")
    logging.info(f"Temps d'exécution total: {script_execution_time:.3f}s")
    logging.info(f"Temps de réponse API moyen: {metrics['api_response_time']:.3f}s")
    
    # Afficher les erreurs s'il y en a
    if metrics['errors']:
        logging.warning(f"Erreurs détaillées ({len(metrics['errors'])}):")
        for error in metrics['errors']:
            logging.warning(f"  - {error['service']} ({error['host']}): {error['error']}")
    
    # Sauvegarder les métriques dans le dashboard
    if DASHBOARD_ENABLED:
        with app.app_context():
            save_system_metrics(
                api_response_time=metrics['api_response_time'],
                total_alerts=metrics['total_alerts'],
                successful_acks=metrics['successful_acks'],
                failed_acks=metrics['failed_acks'],
                execution_time=script_execution_time
            )
        logging.info("Métriques sauvegardées dans le dashboard")
    
    logging.info("=== Fin du script d'acquittement des alertes ===")

if __name__ == "__main__":
    main()
