#!/usr/bin/env python3
"""
Script d'envoi d'emails pour les hôtes du hostgroup SQUARE
Utilise le CLI Centreon pour vérifier l'appartenance aux hostgroups
"""

import json
import subprocess
import smtplib
import ssl
import os
import sys
import logging
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# ===============================================
# CONFIGURATION
# ===============================================

# Configuration Centreon CLI
CENTREON_USER = os.getenv("CENTREON_LOGIN")
CENTREON_PASSWORD = os.getenv("CENTREON_PASSWORD")

# Configuration Email avec support relai local
EMAIL_SENDER = os.getenv("EMAIL_SENDER", "centreon@localhost")  # Default sender
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")  # Optionnel pour relai local
SMTP_SERVER = os.getenv("SMTP_SERVER", "localhost")  # Default relai local
SMTP_PORT = int(os.getenv("SMTP_PORT", 25))  # Default port relai

# Destinataires pour SQUARE
SQUARE_RECIPIENTS = os.getenv("SQUARE_EMAIL_RECIPIENTS", "admin@exemple.com").split(",")
SQUARE_CC_RECIPIENTS = os.getenv("SQUARE_EMAIL_CC", "").split(",") if os.getenv("SQUARE_EMAIL_CC") else []
SQUARE_BCC_RECIPIENTS = os.getenv("SQUARE_EMAIL_BCC", "").split(",") if os.getenv("SQUARE_EMAIL_BCC") else []

# Nettoyer les listes (supprimer les espaces et entrées vides)
SQUARE_RECIPIENTS = [email.strip() for email in SQUARE_RECIPIENTS if email.strip()]
SQUARE_CC_RECIPIENTS = [email.strip() for email in SQUARE_CC_RECIPIENTS if email.strip()]
SQUARE_BCC_RECIPIENTS = [email.strip() for email in SQUARE_BCC_RECIPIENTS if email.strip()]
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
LOG_DIR = os.getenv("LOG_DIR", "logs")
OUTPUT_FILE = os.getenv("OUTPUT_FILE", os.path.join(OUTPUT_DIR, "alerts_output.json"))

# Validation (seulement Centreon requis maintenant)
if not all([CENTREON_USER, CENTREON_PASSWORD]):
    print("ERREUR: Variables d'environnement manquantes (CENTREON_LOGIN, CENTREON_PASSWORD)")
    sys.exit(1)

# Détection du mode (relai local ou SMTP externe)
USE_LOCAL_RELAY = (SMTP_SERVER == "localhost" and not EMAIL_PASSWORD)
if USE_LOCAL_RELAY:
    logging.info(f"Mode relai local détecté: {SMTP_SERVER}:{SMTP_PORT}")
else:
    logging.info(f"Mode SMTP externe: {SMTP_SERVER}:{SMTP_PORT} avec authentification")

# Assurer les chemins absolus
if not os.path.isabs(OUTPUT_FILE):
    OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", OUTPUT_FILE)

# Logging
today = datetime.now().strftime("%Y-%m-%d")
LOG_FILE = os.path.join(LOG_DIR, f"{today}_square_email.log")
if not os.path.isabs(LOG_FILE):
    LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", LOG_FILE)

# ===============================================
# FONCTIONS
# ===============================================

def configure_logging():
    """Configuration du logging"""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    date_format = "%H:%M:%S"
    
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format=log_format,
        datefmt=date_format
    )
    
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    formatter = logging.Formatter(log_format, date_format)
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

def extract_alerts_with_jq():
    """Extraire les alertes avec jq comme spécifié"""
    try:
        if not os.path.exists(OUTPUT_FILE):
            logging.error(f"Fichier non trouvé: {OUTPUT_FILE}")
            return []
        
        # Commande jq mise à jour avec le status
        jq_command = [
            "jq", 
            ".alerts[] | {service_id: .service_id, host_id: .host_id, service_name: .name, host_name: .parent.name, service_information: .information, status: .status.name}",
            OUTPUT_FILE
        ]
        
        logging.info("Extraction des alertes avec jq...")
        result = subprocess.run(jq_command, capture_output=True, text=True, check=True)
        
        # Parser les résultats JSON (une ligne par objet)
        alerts = []
        for line in result.stdout.strip().split('\n'):
            if line.strip():
                try:
                    alerts.append(json.loads(line))
                except json.JSONDecodeError:
                    logging.warning(f"Ligne JSON invalide ignorée: {line}")
        
        logging.info(f"{len(alerts)} alertes extraites")
        return alerts
        
    except subprocess.CalledProcessError as e:
        logging.error(f"Erreur jq: {e}")
        logging.error(f"Output: {e.stdout}")
        logging.error(f"Error: {e.stderr}")
        return []
    except FileNotFoundError:
        logging.error("jq non trouvé. Installer avec: apt install jq")
        return []
    except Exception as e:
        logging.error(f"Erreur extraction: {e}")
        return []

def check_hostgroup_membership(hostname):
    """Vérifier si un hôte appartient au hostgroup SQUARE"""
    try:
        # Commande centreon exacte comme spécifiée
        centreon_command = [
            "centreon",
            "-u", CENTREON_USER,
            "-p", CENTREON_PASSWORD,
            "-o", "HOST",
            "-a", "gethostgroup",
            "-v", hostname
        ]
        
        logging.debug(f"Vérification hostgroup pour {hostname}")
        result = subprocess.run(centreon_command, capture_output=True, text=True, check=True)
        
        # Parser la sortie (format: id;name)
        lines = result.stdout.strip().split('\n')
        
        # Ignorer la ligne d'en-tête si présente
        for line in lines[1:]:  # Skip header "id;name"
            if ';' in line:
                hostgroup_id, hostgroup_name = line.split(';', 1)
                logging.debug(f"  Hostgroup trouvé: {hostgroup_name} (ID: {hostgroup_id})")
                
                # Vérifier si "SQUARE" est dans le nom (insensible à la casse)
                if "SQUARE" in hostgroup_name.upper():
                    logging.info(f"✅ {hostname} appartient au hostgroup SQUARE: {hostgroup_name}")
                    return True
        
        logging.debug(f"❌ {hostname} n'appartient pas au hostgroup SQUARE")
        return False
        
    except subprocess.CalledProcessError as e:
        logging.warning(f"Erreur CLI Centreon pour {hostname}: {e}")
        logging.debug(f"Output: {e.stdout}")
        logging.debug(f"Error: {e.stderr}")
        return False
    except Exception as e:
        logging.error(f"Erreur vérification hostgroup pour {hostname}: {e}")
        return False

def create_email_message(alert):
    """Créer le message email pour une alerte SQUARE"""
    service_name = alert.get("service_name", "Service inconnu")
    host_name = alert.get("host_name", "Hôte inconnu")
    service_info = alert.get("service_information", "Pas d'information disponible")
    status = alert.get("status", "UNKNOWN")
    
    # Message
    msg = MIMEMultipart()
    msg['From'] = EMAIL_SENDER
    msg['To'] = ", ".join(SQUARE_RECIPIENTS)
    
    # Ajouter les copies si définies
    if SQUARE_CC_RECIPIENTS:
        msg['Cc'] = ", ".join(SQUARE_CC_RECIPIENTS)
    
    if SQUARE_BCC_RECIPIENTS:
        msg['Bcc'] = ", ".join(SQUARE_BCC_RECIPIENTS)
    
    # Sujet: status - service_name on hostname
    msg['Subject'] = f"{status} - {service_name} on {host_name}"
    
    # Corps du message - Format demandé
    message_body = f"""Dear IT team,
Centreon has detected an unexpected event:

{service_info}

Thank you for your support and action.
Regards,
Monitoring Team"""
    
    # Version HTML (optionnelle, même contenu mais avec formatage)
    html_body = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 20px; }}
            .content {{ max-width: 600px; }}
            .service-info {{ 
                background-color: #f9f9f9; 
                border-left: 4px solid #337ab7; 
                padding: 15px; 
                margin: 15px 0;
                font-family: monospace;
            }}
        </style>
    </head>
    <body>
        <div class="content">
            <p>Dear IT team,</p>
            <p>Centreon has detected an unexpected event:</p>
            
            <div class="service-info">
                {service_info.replace('\n', '<br>')}
            </div>
            
            <p>Thank you for your support and action.</p>
            <p>Regards,<br>Monitoring Team</p>
        </div>
    </body>
    </html>
    """
    
    # Attacher les deux versions
    msg.attach(MIMEText(message_body, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))
    
    return msg

def send_email(message):
    """Envoyer l'email via relai local ou SMTP externe"""
    try:
        # Récupérer tous les destinataires (TO + CC + BCC)
        all_recipients = SQUARE_RECIPIENTS.copy()
        all_recipients.extend(SQUARE_CC_RECIPIENTS)
        all_recipients.extend(SQUARE_BCC_RECIPIENTS)
        
        if USE_LOCAL_RELAY:
            # Mode relai local : pas d'auth, pas de TLS
            logging.debug("Envoi via relai local (pas d'authentification)")
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.set_debuglevel(0)  # Mettre à 1 pour debug
                # Pour SMTP, il faut envoyer à TOUS les destinataires (TO+CC+BCC)
                server.sendmail(EMAIL_SENDER, all_recipients, message.as_string())
        else:
            # Mode SMTP externe : avec auth et TLS
            logging.debug("Envoi via SMTP externe (avec authentification)")
            context = ssl.create_default_context()
            with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
                server.starttls(context=context)
                server.login(EMAIL_SENDER, EMAIL_PASSWORD)
                # Pour SMTP, il faut envoyer à TOUS les destinataires (TO+CC+BCC)
                server.sendmail(EMAIL_SENDER, all_recipients, message.as_string())
        
        return True, None
        
    except Exception as e:
        return False, str(e)

def process_square_alerts():
    """Processus principal"""
    logging.info("=== Démarrage du traitement SQUARE ===")
    
    # 1. Extraire les alertes avec jq
    alerts = extract_alerts_with_jq()
    if not alerts:
        logging.info("Aucune alerte à traiter")
        return
    
    # 2. Traiter chaque alerte
    square_alerts = []
    checked_hosts = set()  # Cache pour éviter les vérifications répétées
    
    for i, alert in enumerate(alerts, 1):
        host_name = alert.get("host_name")
        service_name = alert.get("service_name")
        
        if not host_name:
            logging.warning(f"[{i:2d}/{len(alerts)}] Nom d'hôte manquant pour {service_name}")
            continue
        
        logging.info(f"[{i:2d}/{len(alerts)}] Traitement: {service_name} sur {host_name}")
        
        # Vérifier appartenance SQUARE (avec cache)
        if host_name not in checked_hosts:
            is_square = check_hostgroup_membership(host_name)
            checked_hosts.add(host_name)
            
            # Stocker le résultat pour cet hôte
            if is_square:
                square_alerts.append(alert)
        else:
            # Hôte déjà vérifié, chercher dans les alertes SQUARE déjà trouvées
            if any(a.get("host_name") == host_name for a in square_alerts):
                square_alerts.append(alert)
    
    # 3. Envoyer les emails pour les alertes SQUARE
    if not square_alerts:
        logging.info("Aucune alerte SQUARE trouvée")
        return
    
    logging.info(f"Envoi d'emails pour {len(square_alerts)} alertes SQUARE")
    
    emails_sent = 0
    emails_failed = 0
    
    for alert in square_alerts:
        try:
            message = create_email_message(alert)
            success, error = send_email(message)
            
            if success:
                emails_sent += 1
                logging.info(f"✅ Email envoyé: {alert['service_name']} sur {alert['host_name']}")
            else:
                emails_failed += 1
                logging.error(f"❌ Échec email: {alert['service_name']} sur {alert['host_name']} - {error}")
                
        except Exception as e:
            emails_failed += 1
            logging.error(f"❌ Erreur: {alert['service_name']} sur {alert['host_name']} - {e}")
    
    # Résumé
    logging.info(f"Résumé: {emails_sent} emails envoyés, {emails_failed} échecs")
    logging.info("=== Traitement SQUARE terminé ===")

def main():
    """Fonction principale"""
    configure_logging()
    
    logging.info("Script d'email SQUARE - Démarrage")
    logging.info(f"Mode email: {'Relai local' if USE_LOCAL_RELAY else 'SMTP externe'}")
    logging.info(f"Serveur: {SMTP_SERVER}:{SMTP_PORT}")
    logging.info(f"Expéditeur: {EMAIL_SENDER}")
    logging.info(f"Fichier source: {OUTPUT_FILE}")
    logging.info(f"Destinataires TO: {SQUARE_RECIPIENTS}")
    
    if SQUARE_CC_RECIPIENTS:
        logging.info(f"Destinataires CC: {SQUARE_CC_RECIPIENTS}")
    if SQUARE_BCC_RECIPIENTS:
        logging.info(f"Destinataires BCC: {SQUARE_BCC_RECIPIENTS}")
    
    # Vérifications préalables
    if not os.path.exists(OUTPUT_FILE):
        logging.error(f"Fichier d'alertes non trouvé: {OUTPUT_FILE}")
        logging.info("Exécuter d'abord monitoring.py")
        return
    
    # Traitement
    process_square_alerts()

if __name__ == "__main__":
    main()
