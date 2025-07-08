# Centreon Auto-Acknowledge Tool

Un outil d'automatisation complet pour acquitter les alertes d'un système de monitoring Centreon avec dashboard de visualisation en temps réel.

## 📋 Description

Ce projet Python offre une solution complète pour la gestion automatisée des alertes Centreon :
- **Script d'acquittement automatique** : acquitte les alertes non traitées dans Centreon
- **Dashboard web interactif** : visualise les statistiques et l'historique des acquittements en temps réel
- **Base de données intégrée** : stocke l'historique des opérations pour le suivi et les analyses

Il est particulièrement utile pour gérer les alertes récurrentes et implémenter des stratégies d'acquittement automatique selon vos besoins opérationnels.

## 🔧 Installation

### Prérequis

- Python 3.6+
- pip (gestionnaire de paquets Python)

### Étapes d'installation

1. Clonez ce dépôt sur votre machine locale :
   ```bash
   git clone https://github.com/senbonzak/centreon-auto.git
   cd centreon-auto
   ```

2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

3. Créez un fichier `.env` à la racine du projet en vous basant sur le modèle `.env.example` :
   ```bash
   cp env.example .env
   ```

4. Modifiez le fichier `.env` avec vos informations de connexion Centreon et dashboard :
   ```bash
   vim .env
   ```
   
   Configuration minimale requise :
   ```env
   # API Centreon
   CENTREON_API_URL=https://votre-serveur-centreon/api/latest
   CENTREON_LOGIN=votre_login
   CENTREON_PASSWORD=votre_mot_de_passe
   
   # Configuration de l'application
   ALERT_LIMIT=100
   LOG_LEVEL=INFO
   
   # Configuration du Dashboard
   FLASK_SECRET_KEY=votre-clé-secrète-unique
   FLASK_PORT=5000
   DATABASE_URL=sqlite:///centreon_dashboard.db
   ```

## 🚀 Utilisation

### 1. Lancement du Dashboard

Pour démarrer le dashboard web :

```bash
python dashboard.py
```

Le dashboard sera accessible sur :
- **Page principale** : http://localhost:5000
- **Historique** : http://localhost:5000/history

### 2. Exécution manuelle du script d'acquittement

Pour exécuter le script d'acquittement manuellement :

```bash
python scripts/monitoring.py
```

### 3. Planification avec Cron

Pour automatiser l'exécution du script, ajoutez une entrée dans votre crontab :

```bash
# Éditer le crontab
crontab -e

# Ajouter cette ligne pour exécuter toutes les 30 minutes
*/30 * * * * cd /chemin/vers/centreon-auto && python scripts/monitoring.py >> /var/log/centreon-auto-ack.log 2>&1
```

## 📁 Structure du projet

```
├── README.md              # Documentation du projet
├── dashboard.py           # Application web dashboard (NOUVEAU)
├── .env                   # Fichier de configuration (variables d'environnement)
├── .env.example           # Exemple de fichier de configuration
├── requirements.txt       # Dépendances Python (mis à jour avec Flask)
├── .gitignore            # Fichiers à ignorer par Git
├── logs/                  # Répertoire pour les fichiers de logs (créé automatiquement)
├── output/                # Répertoire pour les fichiers de sortie (créé automatiquement)
└── scripts/
    └── monitoring.py      # Script principal d'acquittement des alertes
```

## 📊 Fonctionnalités

### Script d'acquittement (monitoring.py)
- Connexion sécurisée à l'API Centreon
- Récupération des alertes non acquittées
- Acquittement automatique des alertes
- Logs détaillés des opérations (console et fichier)
- Sauvegarde des alertes dans un fichier JSON

### Dashboard Web (dashboard.py) - NOUVEAU ✨
- **Page principale** : métriques en temps réel et graphiques
  - Statistiques des dernières 24h
  - Graphique horaire des acquittements
  - Distribution des statuts d'alertes
  - Activité récente
- **Page historique** : consultation et filtrage des données
  - Filtres par période, statut et résultat
  - Export des données en CSV
  - Statistiques détaillées
- **Actualisation automatique** toutes les 30 secondes
- **Base de données SQLite** pour le stockage persistant

## ⚙️ Configuration

Les paramètres suivants peuvent être configurés via des variables d'environnement ou le fichier `.env` :

### Configuration Centreon
| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| CENTREON_API_URL | URL de l'API Centreon | - |
| CENTREON_LOGIN | Nom d'utilisateur Centreon | - |
| CENTREON_PASSWORD | Mot de passe Centreon | - |
| ALERT_LIMIT | Nombre maximum d'alertes à traiter | 100 |

### Configuration Script
| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| OUTPUT_DIR | Répertoire pour les fichiers de sortie | output |
| OUTPUT_FILE | Chemin du fichier de sortie | output/alerts_output.json |
| LOG_DIR | Répertoire pour les fichiers de logs | logs |
| LOG_LEVEL | Niveau de détail des logs | INFO |
| LOGIN_TIMEOUT | Timeout de connexion (secondes) | 30 |
| API_TIMEOUT | Timeout API (secondes) | 60 |
| ACK_TIMEOUT | Timeout acquittement (secondes) | 20 |

### Configuration Dashboard (NOUVEAU)
| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| FLASK_SECRET_KEY | Clé secrète Flask | - |
| FLASK_PORT | Port du serveur web | 5000 |
| FLASK_DEBUG | Mode debug | False |
| DATABASE_URL | URL de la base de données | sqlite:///centreon_dashboard.db |

## 🌐 Interface Dashboard

### Page Principale
- **Métriques 24h** : nombre total d'acquittements, succès, taux de réussite, temps de réponse moyen
- **Graphique horaire** : visualisation des acquittements par heure
- **Graphique de statuts** : répartition par type d'alerte (WARNING, CRITICAL)
- **Activité récente** : derniers acquittements effectués

### Page Historique
- **Filtres avancés** : par période (1-30 jours), statut, résultat
- **Statistiques filtrées** : métriques calculées selon les filtres appliqués
- **Export CSV** : téléchargement des données pour analyse externe
- **Tableau détaillé** : historique complet avec tous les détails

## 📝 Logs

Les logs sont enregistrés dans le répertoire `logs/` avec un fichier par jour au format `YYYY-MM-DD_centreon.log`. Ils incluent :
- La connexion à l'API
- Les alertes récupérées
- Les opérations d'acquittement
- Les erreurs éventuelles

## 🛠️ Dépannage

### Problèmes courants

1. **Erreur de connexion à l'API Centreon**
   - Vérifiez vos identifiants dans le fichier `.env`
   - Assurez-vous que l'URL de l'API est correcte et accessible

2. **Le script ne traite aucune alerte**
   - Vérifiez que des alertes non acquittées existent dans Centreon
   - Augmentez la valeur de `ALERT_LIMIT` si nécessaire

3. **Dashboard ne démarre pas**
   - Vérifiez que le port 5000 n'est pas utilisé : `netstat -tlnp | grep :5000`
   - Changez le port avec la variable `FLASK_PORT` dans `.env`
   - Vérifiez les permissions d'écriture pour la base de données

4. **Base de données corrompue**
   - Supprimez le fichier `centreon_dashboard.db` pour réinitialiser
   - Redémarrez le dashboard pour recréer la base

5. **Timeouts fréquents**
   - Augmentez les valeurs de timeout dans `.env` :
     ```env
     LOGIN_TIMEOUT=60
     API_TIMEOUT=120
     ACK_TIMEOUT=40
     ```

### Vérification de l'installation

```bash
# Tester la connexion API
python scripts/monitoring.py

# Vérifier les dépendances
pip list | grep -E "(Flask|requests|python-dotenv)"

# Tester le dashboard
curl http://localhost:5000/api/stats
```

## 🔄 Architecture et Fonctionnement

### Intégration intelligente

Le projet utilise une architecture avec **intégration automatique** entre les composants :

1. **Script d'acquittement** (`monitoring.py`) :
   - **Détection automatique** du dashboard au démarrage
   - **Mode intégré** : sauvegarde directe en base si dashboard détecté
   - **Mode standalone** : fonctionne normalement si dashboard absent
   - Génère toujours les logs et JSON (backup)

2. **Dashboard web** (`dashboard.py`) :
   - Interface de visualisation en temps réel
   - Base de données SQLite intégrée
   - API REST pour les données
   - Historique et export des données

### Flux de données intelligent

```
Centreon API → monitoring.py → {
    ├── Dashboard DB (si disponible) → Interface Web temps réel
    ├── Logs détaillés 
    └── Fichiers JSON (backup)
}
```

### Messages de détection

Au démarrage de monitoring.py :
- ✅ `"Dashboard detected - Integration enabled"` → Données temps réel
- ⚠️ `"Dashboard not detected - Standalone mode"` → Mode traditionnel

### Déploiement

1. **Démarrez le dashboard** :
   ```bash
   python dashboard.py
   ```

2. **Testez l'intégration** :
   ```bash
   python scripts/monitoring.py
   # Doit afficher: "Dashboard detected - Integration enabled"
   ```

3. **Planifiez le script d'acquittement** :
   ```bash
   # Ajoutez au crontab
   */30 * * * * cd /chemin/vers/centreon-auto && python scripts/monitoring.py
   ```

4. **Accédez à l'interface** : http://localhost:5000

## 📜 Licence

[MIT](LICENSE)

## 👥 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à soumettre une pull request ou à ouvrir une issue pour tout problème ou suggestion.

### Développements futurs
- Notifications en temps réel (WebSocket)
- Authentification utilisateur
- Gestion multi-tenant
- API REST pour intégrations externes
- Rapports automatisés par email