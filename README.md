# Centreon Auto-Acknowledge Tool avec Dashboard Web

Un outil d'automatisation pour acquitter les alertes d'un système de monitoring Centreon, maintenant avec un dashboard web temps réel pour la visualisation et l'analyse.

## 🆕 **Nouveau : Dashboard Web Temps Réel**

### ✨ Fonctionnalités Dashboard
- 📊 **Métriques temps réel** : Acquittements, taux de succès, temps de réponse
- 📈 **Graphiques interactifs** : Tendances horaires, distribution des statuts
- 📋 **Historique détaillé** : Filtres avancés, recherche, pagination
- 📤 **Export de données** : CSV et JSON avec filtres appliqués
- 🔄 **Temps réel** : Mises à jour automatiques via WebSocket
- 📱 **Interface responsive** : Compatible mobile et desktop

### 🎯 Accès Rapide
- **Dashboard principal** : http://localhost:5000
- **Historique détaillé** : http://localhost:5000/history

## 📋 Description

Ce script Python permet d'acquitter automatiquement les alertes non traitées dans Centreon avec une interface web moderne pour le monitoring et l'analyse. Il est particulièrement utile pour gérer les alertes récurrentes et analyser les performances du système.

## 🔧 Installation

### Prérequis

- Python 3.8+
- pip (gestionnaire de paquets Python)
- Accès à l'API Centreon

### Installation Rapide

```bash
# 1. Cloner le projet
git clone https://github.com/senbonzak/centreon-auto.git
cd centreon-auto

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Configuration
cp env.example .env
# Éditer .env avec vos paramètres Centreon

# 4. Initialiser le dashboard
python start_dashboard.py --setup-db

# 5. Démarrer (mode complet : dashboard + monitoring)
python start_dashboard.py --mode full
```

## ⚙️ Configuration

### Fichier `.env`

```bash
# Configuration Centreon
CENTREON_API_URL=https://votre-serveur-centreon/centreon/api/latest
CENTREON_LOGIN=votre_login
CENTREON_PASSWORD=votre_mot_de_passe
ALERT_LIMIT=100
LOG_LEVEL=INFO

# Configuration Dashboard
FLASK_SECRET_KEY=votre-clé-secrète-très-longue-et-complexe
FLASK_DEBUG=False
FLASK_PORT=5000
DATABASE_URL=sqlite:///centreon_dashboard.db

# Optionnel
MONITORING_INTERVAL=300  # 5 minutes
```

### Variables de Configuration

| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| CENTREON_API_URL | URL de l'API Centreon | - |
| CENTREON_LOGIN | Nom d'utilisateur Centreon | - |
| CENTREON_PASSWORD | Mot de passe Centreon | - |
| ALERT_LIMIT | Nombre maximum d'alertes à traiter | 100 |
| FLASK_PORT | Port du serveur web | 5000 |
| MONITORING_INTERVAL | Intervalle monitoring (secondes) | 300 |
| DATABASE_URL | URL de la base de données | sqlite:///centreon_dashboard.db |
| LOG_LEVEL | Niveau de détail des logs | INFO |

## 🚀 Utilisation

### Modes de Fonctionnement

```bash
# Dashboard uniquement (développement/test)
python start_dashboard.py --mode dashboard

# Monitoring automatique uniquement
python start_dashboard.py --mode monitoring

# Mode complet (dashboard + monitoring automatique)
python start_dashboard.py --mode full

# Vérifications système
python start_dashboard.py --check-deps
python start_dashboard.py --setup-db
```

### Exécution Manuelle du Script

```bash
# Acquittement manuel des alertes
python scripts/monitoring.py
```

### Planification avec Cron

```bash
# Éditer crontab
crontab -e

# Ajouter : exécuter toutes les 5 minutes
*/5 * * * * cd /chemin/vers/centreon-auto && python scripts/monitoring.py >> /var/log/centreon-auto.log 2>&1
```

## 📊 Interface Dashboard

### Page Principale (`/`)
- **Métriques 24h** : Total acquittements, succès, taux de réussite
- **Graphique horaire** : Évolution des acquittements sur 24h
- **Distribution statuts** : Répartition WARNING/CRITICAL/DOWN/UNKNOWN  
- **Activité récente** : Liste des 10 derniers acquittements
- **Statut connexion** : Indicateur temps réel WebSocket

### Page Historique (`/history`)
- **Filtres avancés** : Par date, statut, résultat, recherche libre
- **Graphiques de tendance** : Évolution sur la période sélectionnée
- **Top hôtes** : Hôtes avec le plus d'acquittements
- **Tableau détaillé** : Historique complet avec pagination
- **Export** : Téléchargement CSV/JSON des données filtrées

### API REST

| Endpoint | Méthode | Description |
|----------|---------|-------------|
| `/api/stats` | GET | Statistiques générales |
| `/api/charts/hourly` | GET | Données graphique horaire |
| `/api/charts/status-distribution` | GET | Distribution des statuts |
| `/api/recent-acks` | GET | Acquittements récents |
| `/api/history` | GET | Historique avec filtres |
| `/api/export/csv` | GET | Export CSV |
| `/api/export/json` | GET | Export JSON |

## 📁 Structure du Projet

```
centreon-auto/
├── README.md                    # Cette documentation
├── .env                         # Configuration (à créer)
├── .env.example                 # Exemple de configuration
├── requirements.txt             # Dépendances Python
├── .gitignore                  # Fichiers ignorés par Git
├── dashboard.py                # 🆕 Application web Flask
├── start_dashboard.py          # 🆕 Script de démarrage
├── scripts/
│   └── monitoring.py           # Script de monitoring (amélioré)
├── templates/                  # 🆕 Templates HTML
│   ├── dashboard.html          # Page d'accueil
│   └── history.html           # Page historique
├── static/                     # 🆕 Assets web (auto-créé)
├── logs/                       # Logs (auto-créé)
├── output/                     # Fichiers de sortie (auto-créé)
└── centreon_dashboard.db       # 🆕 Base de données (auto-créé)
```

## 🔧 Déploiement Production

### Service Systemd

```bash
# Créer le service
sudo vim /etc/systemd/system/centreon-dashboard.service
```

```ini
[Unit]
Description=Centreon Auto-Acknowledge Dashboard
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/centreon-auto
Environment=PATH=/opt/centreon-auto/venv/bin
ExecStart=/opt/centreon-auto/venv/bin/python start_dashboard.py --mode full
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Activer et démarrer
sudo systemctl daemon-reload
sudo systemctl enable centreon-dashboard
sudo systemctl start centreon-dashboard
sudo systemctl status centreon-dashboard
```

### Proxy Nginx

```bash
# Configuration Nginx
sudo vim /etc/nginx/sites-available/centreon-dashboard
```

```nginx
server {
    listen 80;
    server_name dashboard-centreon.votre-domaine.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name dashboard-centreon.votre-domaine.com;

    # Certificats SSL
    ssl_certificate /etc/letsencrypt/live/dashboard-centreon.votre-domaine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/dashboard-centreon.votre-domaine.com/privkey.pem;

    # Proxy vers Flask
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Support WebSocket
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

```bash
# Activer et SSL
sudo ln -s /etc/nginx/sites-available/centreon-dashboard /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
sudo certbot --nginx -d dashboard-centreon.votre-domaine.com
```

## 📈 Monitoring et Logs

### Logs Importants

```bash
# Logs du dashboard
tail -f logs/$(date +%Y-%m-%d)_centreon.log

# Logs système (si service systemd)
sudo journalctl -u centreon-dashboard -f

# Logs Nginx (si proxy)
tail -f /var/log/nginx/centreon-dashboard-error.log
```

### Métriques Collectées

- **Acquittements** : Nombre, taux de succès, temps de traitement
- **Performance API** : Temps de réponse Centreon
- **Système** : Temps d'exécution, erreurs
- **Utilisateurs** : Connexions WebSocket (optionnel)

## 🛠️ Dépannage

### Problèmes Courants

**1. Erreur de connexion à Centreon**
```bash
# Vérifier la configuration
grep CENTREON .env

# Tester manuellement l'API
curl -k -X POST https://votre-centreon/centreon/api/latest/login \
  -H "Content-Type: application/json" \
  -d '{"security":{"credentials":{"login":"user","password":"pass"}}}'
```

**2. Dashboard inaccessible**
```bash
# Vérifier le service
sudo systemctl status centreon-dashboard

# Tester en local
curl http://localhost:5000/api/stats

# Vérifier les ports
netstat -tlnp | grep :5000
```

**3. Base de données locked**
```bash
# Redémarrer le service
sudo systemctl restart centreon-dashboard

# Vérifier les permissions
ls -la centreon_dashboard.db
```

**4. Erreurs WebSocket**
```bash
# Dans les logs du navigateur (F12)
# Vérifier que le proxy supporte WebSocket
# Tester sans proxy sur localhost:5000
```

### Tests de Vérification

```bash
# Test complet du système
python start_dashboard.py --check-deps
python start_dashboard.py --setup-db

# Test de l'API Centreon
python -c "
from scripts.monitoring import get_token
token, time = get_token()
print('Token OK' if token else 'Token KO')
"

# Test du dashboard
curl -s http://localhost:5000/api/stats | python -m json.tool
```

## 📊 Performance

### Optimisations Base de Données

```bash
# Pour SQLite (par défaut)
# Automatique, pas d'optimisation nécessaire

# Pour PostgreSQL (production)
# Ajouter dans .env :
# DATABASE_URL=postgresql://user:pass@localhost/centreon_dashboard
```

### Optimisations Serveur

```bash
# Production avec Gunicorn
pip install gunicorn
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 dashboard:app

# Avec cache Redis (optionnel)
pip install redis
# Ajouter REDIS_URL dans .env
```

## 📜 Changelog

### Version 2.0.0 (Dashboard Web)
- ✅ Interface web responsive complète
- ✅ Dashboard temps réel avec WebSocket
- ✅ Historique avec filtres avancés
- ✅ Export CSV/JSON des données
- ✅ Base de données SQLite intégrée
- ✅ API REST complète
- ✅ Support production (Systemd, Nginx)

### Version 1.0.0 (Script Original)
- ✅ Acquittement automatique des alertes
- ✅ Logs détaillés
- ✅ Configuration via .env
- ✅ Sauvegarde JSON des alertes

## 🤝 Contribution

Les contributions sont les bienvenues ! Pour contribuer :

1. Fork le projet
2. Créer une branche feature (`git checkout -b feature/amazing-feature`)
3. Commit les changements (`git commit -m 'Add amazing feature'`)
4. Push vers la branche (`git push origin feature/amazing-feature`)
5. Ouvrir une Pull Request

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 📞 Support

- **Issues GitHub** : [Créer une issue](https://github.com/senbonzak/centreon-auto/issues)
- **Discussions** : [GitHub Discussions](https://github.com/senbonzak/centreon-auto/discussions)
- **Documentation** : Voir ce README et les commentaires dans le code

## 🎯 Roadmap

### Version 2.1.0 (Prochaine)
- [ ] Authentification utilisateur
- [ ] Notifications email/Slack
- [ ] Dashboard multi-tenant
- [ ] API d'intégration Webhook

### Version 2.2.0 (Future)
- [ ] Interface d'administration
- [ ] Règles d'acquittement personnalisées
- [ ] Intégration Prometheus/Grafana
- [ ] Mode cluster/haute disponibilité

---

**🚀 Prêt à moderniser votre monitoring Centreon avec un dashboard professionnel !**
