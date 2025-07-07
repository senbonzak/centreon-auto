#!/usr/bin/env python3
"""
Centreon alert auto-acknowledgment script
English version with dashboard integration
"""

import requests
import json
import urllib3
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ===============================================
# CONFIGURATION
# ===============================================

load_dotenv()

# Dashboard integration
try:
    # Add parent directory to path for dashboard import
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from dashboard import app, db, save_acknowledgment
    DASHBOARD_ENABLED = True
    print("Dashboard detected - Integration enabled")
except ImportError:
    DASHBOARD_ENABLED = False
    print("Dashboard not detected - Standalone mode")

# Centreon API
API_URL = os.getenv("CENTREON_API_URL")
if not API_URL:
    print("ERROR: CENTREON_API_URL environment variable not defined")
    sys.exit(1)

# Credentials
LOGIN = os.getenv("CENTREON_LOGIN")
PASSWORD = os.getenv("CENTREON_PASSWORD")
if not LOGIN or not PASSWORD:
    print("ERROR: CENTREON_LOGIN and/or CENTREON_PASSWORD environment variables not defined")
    sys.exit(1)

# Configuration
ALERT_LIMIT = int(os.getenv("ALERT_LIMIT", 100))
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
LOG_DIR = os.getenv("LOG_DIR", "logs")

# Timeouts
LOGIN_TIMEOUT = int(os.getenv("LOGIN_TIMEOUT", 30))
API_TIMEOUT = int(os.getenv("API_TIMEOUT", 60))
ACK_TIMEOUT = int(os.getenv("ACK_TIMEOUT", 20))

# File paths
today = datetime.now().strftime("%Y-%m-%d")
OUTPUT_FILE = os.getenv("OUTPUT_FILE", os.path.join(OUTPUT_DIR, "alerts_output.json"))
LOG_FILE = os.getenv("LOG_FILE", os.path.join(LOG_DIR, f"{today}_centreon.log"))

# Ensure absolute paths
if not os.path.isabs(OUTPUT_FILE):
    OUTPUT_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", OUTPUT_FILE)

if not os.path.isabs(LOG_FILE):
    LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", LOG_FILE)

# ===============================================
# FUNCTIONS
# ===============================================

def configure_logging():
    """Configure simplified logging system"""
    # Create directories
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    
    # Simplified format
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    date_format = "%H:%M:%S"
    
    # File configuration
    logging.basicConfig(
        filename=LOG_FILE,
        level=getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper()),
        format=log_format,
        datefmt=date_format
    )
    
    # Console output
    console = logging.StreamHandler()
    console.setLevel(getattr(logging, os.getenv("LOG_LEVEL", "INFO").upper()))
    formatter = logging.Formatter(log_format, date_format)
    console.setFormatter(formatter)
    logging.getLogger('').addHandler(console)

def get_token():
    """Get authentication token from Centreon API"""
    logging.info(f"Connecting to {API_URL}")
    
    try:
        response = requests.post(
            f"{API_URL}/login",
            headers={"Content-Type": "application/json"},
            json={
                "security": {
                    "credentials": {
                        "login": LOGIN,
                        "password": PASSWORD
                    }
                }
            },
            verify=False,
            timeout=LOGIN_TIMEOUT
        )
        response.raise_for_status()
        token = response.json()["security"]["token"]
        logging.info("Centreon connection successful")
        return token
    except requests.exceptions.Timeout:
        logging.error(f"Connection timeout. Server too slow.")
        logging.info("Suggestion: Increase LOGIN_TIMEOUT in .env file")
        return None
    except requests.exceptions.ConnectionError as e:
        logging.error(f"Network connection error: {e}")
        return None
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error: {e}")
        if hasattr(e.response, 'status_code'):
            if e.response.status_code == 401:
                logging.error("Check your LOGIN/PASSWORD credentials")
            elif e.response.status_code == 403:
                logging.error("Access denied. Check user permissions")
        return None
    except Exception as e:
        logging.error(f"Centreon connection error: {e}")
        return None

def get_unhandled_alerts(token):
    """Get unacknowledged alerts from Centreon API"""
    if not token:
        logging.error("Missing authentication token")
        return []
    
    logging.info("Retrieving alerts")
    
    try:
        response = requests.get(
            f"{API_URL}/monitoring/resources",
            headers={
                "Content-Type": "application/json",
                "X-AUTH-TOKEN": token
            },
            params={
                "page": 1,
                "limit": ALERT_LIMIT,
                "states[]": "unhandled_problems",
                "types[]": "service",
                "statuses[]": ["WARNING", "CRITICAL"]
            },
            verify=False,
            timeout=API_TIMEOUT
        )
        response.raise_for_status()
        alerts = response.json().get("result", [])
        logging.info(f"{len(alerts)} alerts found")
        return alerts
    except requests.exceptions.Timeout:
        logging.error("Alert retrieval timeout")
        logging.info("Suggestion: Increase API_TIMEOUT in .env file")
        return []
    except requests.exceptions.HTTPError as e:
        logging.error(f"HTTP error retrieving alerts: {e}")
        if hasattr(e.response, 'status_code') and e.response.status_code == 401:
            logging.error("Token expired or invalid")
        return []
    except Exception as e:
        logging.error(f"Alert retrieval error: {e}")
        return []

def acknowledge_service(token, service_id, host_id, service_name=None, host_name=None, 
                       status=None, comment="Auto ACK by Miguel"):
    """Acknowledge a service alert"""
    if not token:
        logging.error("Missing token")
        return False
        
    try:
        response = requests.post(
            f"{API_URL}/monitoring/resources/acknowledge",
            headers={
                "Content-Type": "application/json",
                "X-AUTH-TOKEN": token
            },
            json={
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
            },
            verify=False,
            timeout=ACK_TIMEOUT
        )
        response.raise_for_status()
        
        # Save to dashboard if available
        if DASHBOARD_ENABLED:
            with app.app_context():
                save_acknowledgment(
                    service_id=service_id,
                    host_id=host_id,
                    service_name=service_name,
                    host_name=host_name,
                    status=status,
                    success=True
                )
                logging.debug("Acknowledgment saved to dashboard")
        
        return True
    except requests.exceptions.Timeout:
        error_msg = f"Acknowledgment timeout for service {service_id}"
        logging.error(error_msg)
        
        # Save failure to dashboard if available
        if DASHBOARD_ENABLED:
            with app.app_context():
                save_acknowledgment(
                    service_id=service_id,
                    host_id=host_id,
                    service_name=service_name,
                    host_name=host_name,
                    status=status,
                    success=False,
                    error_message=error_msg
                )
        
        return False
    except Exception as e:
        error_msg = f"Failed to acknowledge service {service_id}: {e}"
        logging.error(error_msg)
        
        # Save failure to dashboard if available
        if DASHBOARD_ENABLED:
            with app.app_context():
                save_acknowledgment(
                    service_id=service_id,
                    host_id=host_id,
                    service_name=service_name,
                    host_name=host_name,
                    status=status,
                    success=False,
                    error_message=str(e)
                )
        
        return False

def save_alerts_to_file(alerts):
    """Save alerts to JSON file"""
    try:
        data = {
            "timestamp": datetime.now().isoformat(),
            "count": len(alerts),
            "alerts": alerts
        }
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.info(f"Alerts saved: {OUTPUT_FILE}")
    except Exception as e:
        logging.error(f"Save error: {e}")

def main():
    """Main function"""
    configure_logging()
    
    logging.info("Starting acknowledgment script")
    
    if DASHBOARD_ENABLED:
        logging.info("Dashboard integration active - Real-time data available")
    
    # Get token
    token = get_token()
    if not token:
        logging.error("Cannot continue without token")
        return
    
    # Get alerts
    alerts = get_unhandled_alerts(token)
    if not alerts:
        logging.info("No alerts to process")
        return
        
    # Save alerts
    save_alerts_to_file(alerts)
    
    # Acknowledge alerts
    logging.info(f"Starting acknowledgment of {len(alerts)} alerts")
    successful_acks = 0
    failed_acks = 0
    
    for i, alert in enumerate(alerts, 1):
        service_id = alert.get("service_id")
        host_id = alert.get("host_id")
        service_name = alert.get("name", "Unknown")
        host_name = alert.get("parent", {}).get("name", "Unknown")
        status = alert.get("status", {}).get("name", "UNKNOWN")
        
        if service_id and host_id:
            if acknowledge_service(token, service_id, host_id, service_name, host_name, status):
                successful_acks += 1
                logging.info(f"[{i:2d}/{len(alerts)}] SUCCESS: {service_name} on {host_name}")
            else:
                failed_acks += 1
                logging.error(f"[{i:2d}/{len(alerts)}] FAILED: {service_name} on {host_name}")
        else:
            failed_acks += 1
            logging.warning(f"[{i:2d}/{len(alerts)}] Missing ID: {service_name} on {host_name}")
    
    # Summary
    logging.info(f"Summary: {successful_acks} successful, {failed_acks} failed out of {len(alerts)} alerts")
    
    if failed_acks > 0:
        logging.warning("Some failures occurred. Check timeouts or connectivity.")
    
    if DASHBOARD_ENABLED:
        logging.info("Check dashboard for real-time visualization: http://localhost:5000")
    
    logging.info("Script completed")

if __name__ == "__main__":
    main()