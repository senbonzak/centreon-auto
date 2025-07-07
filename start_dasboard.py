#!/usr/bin/env python3
"""
Script de démarrage du dashboard Centreon
Gère le démarrage du serveur web et les tâches de monitoring
"""

import os
import sys
import subprocess
import time
import signal
import argparse
from multiprocessing import Process
from datetime import datetime

def run_dashboard():
    """Lance le serveur dashboard Flask"""
    print("🚀 Démarrage du dashboard web...")
    try:
        from dashboard import app, socketio
        
        debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
        port = int(os.getenv('FLASK_PORT', 5000))
        
        print(f"📱 Dashboard accessible sur: http://localhost:{port}")
        print(f"🔧 Mode debug: {'Activé' if debug_mode else 'Désactivé'}")
        
        socketio.run(app, debug=debug_mode, host='0.0.0.0', port=port)
        
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("Assurez-vous que Flask et les dépendances sont installées:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur lors du démarrage du dashboard: {e}")
        sys.exit(1)

def run_monitoring_script():
    """Lance le script de monitoring périodiquement"""
    print("📊 Démarrage du monitoring automatique...")
    
    monitoring_script = os.path.join(os.path.dirname(__file__), 'scripts', 'monitoring.py')
    if not os.path.exists(monitoring_script):
        print(f"❌ Script de monitoring non trouvé: {monitoring_script}")
        return
    
    interval = int(os.getenv('MONITORING_INTERVAL', 300))  # 5 minutes par défaut
    print(f"⏰ Intervalle de monitoring: {interval} secondes")
    
    while True:
        try:
            print(f"🔍 Exécution du script de monitoring - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Exécuter le script de monitoring
            result = subprocess.run([
                sys.executable, monitoring_script
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                print("✅ Script de monitoring exécuté avec succès")
                if result.stdout:
                    print("📄 Sortie:", result.stdout[-200:])  # Dernières 200 caractères
            else:
                print(f"⚠️ Le script de monitoring a terminé avec le code: {result.returncode}")
                if result.stderr:
                    print("❌ Erreur:", result.stderr[-200:])
            
        except subprocess.TimeoutExpired:
            print("⏰ Timeout du script de monitoring (5 minutes)")
        except Exception as e:
            print(f"❌ Erreur lors de l'exécution du monitoring: {e}")
        
        print(f"⏸️ Attente {interval} secondes avant la prochaine exécution...")
        time.sleep(interval)

def setup_database():
    """Initialise la base de données"""
    print("🗄️ Initialisation de la base de données...")
    try:
        from dashboard import app, db
        
        with app.app_context():
            db.create_all()
            print("✅ Base de données initialisée avec succès")
            
    except Exception as e:
        print(f"❌ Erreur lors de l'initialisation de la base: {e}")
        sys.exit(1)

def check_dependencies():
    """Vérifie que toutes les dépendances sont installées"""
    required_packages = [
        'flask', 'flask_sqlalchemy', 'flask_socketio', 
        'requests', 'python-dotenv'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Paquets manquants:")
        for pkg in missing_packages:
            print(f"   - {pkg}")
        print("\nInstallez les dépendances avec:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    
    print("✅ Toutes les dépendances sont installées")

def signal_handler(signum, frame):
    """Gestionnaire de signaux pour arrêt propre"""
    print("\n🛑 Arrêt du dashboard demandé...")
    sys.exit(0)

def main():
    parser = argparse.ArgumentParser(description="Dashboard Centreon Auto-Acknowledge")
    parser.add_argument('--mode', choices=['dashboard', 'monitoring', 'full'], 
                       default='full', help='Mode de fonctionnement')
    parser.add_argument('--setup-db', action='store_true', 
                       help='Initialiser uniquement la base de données')
    parser.add_argument('--check-deps', action='store_true',
                       help='Vérifier les dépendances uniquement')
    
    args = parser.parse_args()
    
    # Gestionnaire de signaux
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    print("=" * 60)
    print("🎯 DASHBOARD CENTREON AUTO-ACKNOWLEDGE")
    print("=" * 60)
    
    # Vérifications préliminaires
    if args.check_deps:
        check_dependencies()
        return
    
    check_dependencies()
    
    if args.setup_db:
        setup_database()
        return
    
    # Initialiser la base de données au premier démarrage
    setup_database()
    
    try:
        if args.mode == 'dashboard':
            # Mode dashboard uniquement
            run_dashboard()
            
        elif args.mode == 'monitoring':
            # Mode monitoring uniquement
            run_monitoring_script()
            
        elif args.mode == 'full':
            # Mode complet avec dashboard et monitoring
            print("🚀 Démarrage en mode complet...")
            
            # Créer les processus
            dashboard_process = Process(target=run_dashboard, name="Dashboard")
            monitoring_process = Process(target=run_monitoring_script, name="Monitoring")
            
            # Démarrer les processus
            dashboard_process.start()
            monitoring_process.start()
            
            print("✅ Dashboard et monitoring démarrés")
            print("📱 Accédez au dashboard sur: http://localhost:5000")
            print("🔍 Le monitoring s'exécute automatiquement")
            print("💡 Appuyez sur Ctrl+C pour arrêter")
            
            try:
                # Attendre que les processus se terminent
                dashboard_process.join()
                monitoring_process.join()
            except KeyboardInterrupt:
                print("\n🛑 Arrêt des services...")
                dashboard_process.terminate()
                monitoring_process.terminate()
                dashboard_process.join(timeout=10)
                monitoring_process.join(timeout=10)
                
    except Exception as e:
        print(f"❌ Erreur critique: {e}")
        sys.exit(1)
    
    print("👋 Dashboard arrêté proprement")

if __name__ == "__main__":
    main()
