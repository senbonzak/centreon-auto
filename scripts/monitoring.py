import requests
import json
import urllib3
from config import settings
import os
import logging
from datetime import datetime

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# Configuration du logger
today = datetime.now().strftime("%Y-%m-%d")
log_file = f"logs/{today}_ack.log"

logging.basicConfig(
    filename=log_file,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)


def get_token():
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
        return response.json()["security"]["token"]
    except Exception as e:
        print("Erreur de connexion :", e)
        return None

def get_unhandled_alerts(token):
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
        return response.json().get("result", [])
    except Exception as e:
        print("Erreur récupération alertes :", e)
        return []

def acknowledge_service(token, service_id, host_id, comment="Auto ACK by DJ Mag 🧠"):
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
        msg = f"Acknowledged service_id={service_id} on host_id={host_id}"
        print(msg)
        logging.info(msg)
        return True
    except Exception as e:
        error_msg = f"Failed to acknowledge service_id={service_id} on host_id={host_id} → {e}"
        print(error_msg)
        logging.error(error_msg)
        return False


if __name__ == "__main__":
    token = get_token()
    if token:
        alerts = get_unhandled_alerts(token)
        print(f"{len(alerts)} alertes non acquittées trouvées.")

        for alert in alerts:
            service_id = alert.get("service_id")
            host_id = alert.get("host_id")
            if service_id and host_id:
                acknowledge_service(token, service_id, host_id)
