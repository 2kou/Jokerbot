# 🚀 Guide Complet PythonAnywhere - TeleFoot Bot v2.0

## 📋 Nouvelles Fonctionnalités v2.0

### ✨ Système d'Approbation
- **Nouveaux utilisateurs** : Demande d'approbation automatique à l'admin
- **Essai gratuit** : 24h d'accès après approbation admin
- **Demandes de paiement** : Processus sécurisé avec validation admin

### 🔐 Licences Personnalisées
- **Format unique** : `user_id + moitié_id + date + 7 + 23 + 90`
- **Validation stricte** : Impossible de partager entre utilisateurs
- **Sécurité** : Hachage SHA256 pour l'unicité

### 🔄 Redirection Multi-Canaux
- **Messages authentiques** : Apparaissent comme venant du canal de destination
- **Limitation par plan** :
  - Essai : 1 redirection
  - Semaine : 10 redirections
  - Mois : 50 redirections

---

## 📁 Fichiers Nécessaires

### 1. **advanced_user_manager.py** - Gestionnaire avancé
- Système d'approbation avec workflow complet
- Génération de licences personnalisées
- Gestion des permissions par plan

### 2. **advanced_flask_app.py** - Bot principal
- Interface webhook optimisée
- Commandes complètes : `/start`, `/payer`, `/valider_licence`
- Système de notifications admin/utilisateur

### 3. **channel_redirection_system.py** - Système de redirection
- Messages apparaissent comme venant du canal destination
- Support multi-canaux selon l'abonnement
- Gestion des permissions et accès

---

## 🔧 Installation sur PythonAnywhere

### Étape 1: Préparation des fichiers

Uploadez dans `/home/votreusername/mysite/` :

```
mysite/
├── advanced_flask_app.py          # Bot principal
├── advanced_user_manager.py       # Gestionnaire utilisateurs
├── channel_redirection_system.py  # Système redirection
├── .env                           # Configuration
└── votreusername_pythonanywhere_com_wsgi.py
```

### Étape 2: Fichier .env

```env
# Configuration TeleFoot Bot v2.0
BOT_TOKEN=7573497633:AAHk9K15yTCiJP-zruJrc9v8eK8I9XhjyH4
WEBHOOK_SECRET=votre_secret_token_aleatoire
ADMIN_ID=1190237801

# API Telegram (pour redirection avancée)
API_ID=29177661
API_HASH=a8639172fa8d35dbfd8ea46286d349ab
```

### Étape 3: Fichier WSGI

```python
import sys
import os

project_home = '/home/votreusername/mysite'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_home, '.env'))
except:
    pass

from advanced_flask_app import app as application

if __name__ == "__main__":
    application.run()
```

### Étape 4: Installation des dépendances

```bash
pip3.10 install --user flask requests python-dotenv telethon
```

### Étape 5: Configuration webhook

```python
import requests
import secrets

# Générer token secret
secret_token = secrets.token_urlsafe(32)

# Configurer webhook
bot_token = "7573497633:AAHk9K15yTCiJP-zruJrc9v8eK8I9XhjyH4"
webhook_url = f"https://votreusername.pythonanywhere.com/{secret_token}"

response = requests.post(
    f"https://api.telegram.org/bot{bot_token}/setWebhook",
    json={"url": webhook_url}
)

print(response.json())
```

---

## 🎯 Fonctionnement du Système

### 📱 Processus Utilisateur

1. **Premier contact** `/start`
   - Enregistrement automatique
   - Notification admin pour approbation
   - Statut : "En attente"

2. **Approbation admin**
   - Admin reçoit : `/approuver_essai USER_ID`
   - Utilisateur obtient 24h d'essai
   - 1 redirection autorisée

3. **Demande d'abonnement** `/payer`
   - Choix du plan (semaine/mois)
   - Notification admin avec demande
   - Statut : "Paiement demandé"

4. **Validation paiement**
   - Admin : `/approuver_paiement USER_ID PLAN`
   - Génération licence personnalisée
   - Notification à l'utilisateur

5. **Activation finale** `/valider_licence`
   - Utilisateur saisit sa licence
   - Validation automatique
   - Accès complet activé

### 🔄 Système de Redirection

1. **Connexion compte** 
   - Client Telegram personnel requis
   - Vérification des permissions canal

2. **Ajout redirection**
   - Vérification limite selon plan
   - Messages apparaissent du canal destination
   - Support édition temps réel

3. **Limitations par plan**
   - **Essai** : 1 canal → 1 canal
   - **Semaine** : Multi-sources → 10 destinations
   - **Mois** : Multi-sources → 50 destinations

---

## 🛡️ Commandes Admin

### Gestion des Approbations
```bash
/admin                          # Panneau complet
/approuver_essai USER_ID        # Accorder essai 24h
/approuver_paiement USER_ID PLAN # Valider paiement
```

### Monitoring
```bash
# Statistiques en temps réel
curl https://votreusername.pythonanywhere.com/admin/stats

# Santé application
curl https://votreusername.pythonanywhere.com/health
```

---

## 🎮 Commandes Utilisateur

### Principales
- `/start` - Premier contact / Réinitialisation
- `/status` - Voir son statut et infos
- `/payer` - Souscrire un abonnement
- `/valider_licence` - Activer après paiement
- `/redirections` - Gérer les redirections
- `/pronostics` - Accéder aux pronostics premium

### Informations
- `/help` - Guide complet des commandes

---

## 🔐 Sécurité des Licences

### Format de Génération
```
Licence = user_id + (user_id[:len//2]) + date + "72390"
Hash = SHA256(licence_data)[:16]
Format final = "XXXX-XXXX-XXXX-XXXX"
```

### Validation
- Vérification stricte par user_id
- Impossible de partager
- Expiration automatique selon plan

---

## 📊 Monitoring et Logs

### Endpoints de Surveillance
```
/health                    # Santé générale
/admin/stats              # Statistiques détaillées
/webhook_info             # Information webhook
```

### Logs Importants
- Connexions clients Telegram
- Redirections en temps réel
- Approbations admin
- Validations de licences

---

## ❗ Dépannage

### Bot ne répond pas
1. Vérifier webhook : `/webhook_info`
2. Consulter logs PythonAnywhere
3. Tester endpoint : `/health`

### Redirections ne fonctionnent pas
1. Vérifier permissions canal
2. Confirmer client Telegram connecté
3. Vérifier limites utilisateur

### Licences invalides
1. Régénérer via admin
2. Vérifier user_id correct
3. Contrôler format de saisie

---

## 🎉 Avantages v2.0

✅ **Sécurité renforcée** avec licences personnalisées
✅ **Workflow complet** approbation → essai → paiement → activation  
✅ **Redirection authentique** - messages du canal destination
✅ **Limitation intelligente** selon abonnement
✅ **Interface admin** complète et automatisée
✅ **Monitoring** en temps réel
✅ **Expérience utilisateur** fluide et professionnelle

**Votre bot TeleFoot v2.0 est maintenant prêt pour un usage professionnel !** 🚀