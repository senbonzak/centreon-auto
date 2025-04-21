# Centreon Auto-Acknowledge Tool

Un outil d'automatisation pour acquitter les alertes d'un système de monitoring Centreon.

## 📋 Description

Ce projet fournit un script Python permettant d'acquitter automatiquement les alertes non traitées dans Centreon. Il est particulièrement utile pour gérer les alertes récurrentes ou pour implémenter des stratégies d'acquittement automatique selon vos besoins opérationnels.

## 🔧 Installation

### Prérequis

- Python 3.6+
- pip (gestionnaire de paquets Python)

### Étapes d'installation

1. Clonez ce dépôt sur votre machine locale :
   ```bash
   git clone https://github.com/votre-username/centreon-auto-ack.git
   cd centreon-auto-ack
   ```

2. Installez les dépendances :
   ```bash
   pip install -r requirements.txt
   ```

3. Créez un fichier `.env` à la racine du projet en vous basant sur le modèle `.env.example` :
   ```bash
   cp .env.example .env
   ```

4. Modifiez le fichier `.env` avec vos informations de connexion Centreon :
   ```
   CENTREON_API_URL=https://votre-serveur-centreon/api/latest
   CENTREON_LOGIN=votre_login
   CENTREON_PASSWORD=votre_mot_de_passe
   ALERT_LIMIT=100
   LOG_LEVEL=INFO
   ```

## 🚀 Utilisation

### Exécution manuelle

Pour exécuter le script manuellement :

```bash
python scripts/monitoring.py
```

### Planification avec Cron

Pour automatiser l'exécution du script, vous pouvez ajouter une entrée dans votre crontab :

```bash
# Exécuter toutes les 30 minutes
*/30 * * * * cd /chemin/vers/centreon-auto-ack && python scripts/monitoring.py >> /var/log/centreon-auto-ack.log 2>&1
```

## 📁 Structure du projet

```
├── README.md               # Documentation du projet
├── config/                 # Configuration du projet
│   └── settings.py         # Paramètres et configuration
├── logs/                   # Répertoire pour les fichiers de logs
├── output/                 # Répertoire pour les fichiers de sortie
└── scripts/                # Scripts d'exécution
    └── monitoring.py       # Script principal d'acquittement des alertes
```

## ⚙️ Configuration

Les paramètres suivants peuvent être configurés via des variables d'environnement ou le fichier `.env` :

| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| CENTREON_API_URL | URL de l'API Centreon | - |
| CENTREON_LOGIN | Nom d'utilisateur Centreon | - |
| CENTREON_PASSWORD | Mot de passe Centreon | - |
| ALERT_LIMIT | Nombre maximum d'alertes à traiter | 100 |
| OUTPUT_DIR | Répertoire pour les fichiers de sortie | output |
| OUTPUT_FILE | Chemin du fichier de sortie | output/alerts_output.json |
| LOG_DIR | Répertoire pour les fichiers de logs | logs |
| LOG_LEVEL | Niveau de détail des logs (DEBUG, INFO, WARNING, ERROR) | INFO |

## 📊 Fonctionnalités

- Connexion sécurisée à l'API Centreon
- Récupération des alertes non acquittées
- Acquittement automatique des alertes
- Logs détaillés des opérations
- Sauvegarde des alertes dans un fichier JSON

## 📝 Logs

Les logs sont enregistrés dans le répertoire `logs/` avec un fichier par jour au format `YYYY-MM-DD_centreon.log`. Ils incluent les informations sur :
- La connexion à l'API
- Les alertes récupérées
- Les opérations d'acquittement
- Les erreurs éventuelles

## 🛠️ Dépannage

### Problèmes courants

1. **Erreur de connexion à l'API**
   - Vérifiez vos identifiants dans le fichier `.env`
   - Assurez-vous que l'URL de l'API est correcte et accessible

2. **Le script ne traite aucune alerte**
   - Vérifiez que des alertes non acquittées existent dans Centreon
   - Augmentez la valeur de `ALERT_LIMIT` si nécessaire

3. **Erreur "Module not found"**
   - Vérifiez que toutes les dépendances sont installées : `pip install -r requirements.txt`

## 📜 Licence

[MIT](LICENSE)

## 👥 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à soumettre une pull request ou à ouvrir une issue pour tout problème ou suggestion.

1. Forkez le projet
2. Créez votre branche de fonctionnalité (`git checkout -b feature/amazing-feature`)
3. Committez vos changements (`git commit -m 'Add some amazing feature'`)
4. Poussez vers la branche (`git push origin feature/amazing-feature`)
5. Ouvrez une Pull Request