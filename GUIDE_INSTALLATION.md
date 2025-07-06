# 🚀 Guide d'Installation PythonAnywhere - Téléfoot Bot

## 📋 Ce dont vous avez besoin

1. **Compte PythonAnywhere** (gratuit ou payant)
2. **Token Bot Telegram** : `7573497633:AAHk9K15yTCiJP-zruJrc9v8eK8I9XhjyH4`
3. **Les fichiers suivants** (déjà créés) :
   - `flask_app.py` - Application principale
   - `simple_user_manager.py` - Gestionnaire d'utilisateurs
   - `install_pythonanywhere.py` - Script d'installation

## 🎯 Installation Automatique (Recommandée)

### Étape 1: Configuration automatique

```bash
# Exécutez le script de configuration
python3 install_pythonanywhere.py
```

**Entrez vos informations :**
- Nom d'utilisateur PythonAnywhere
- Token bot (utilisez celui par défaut ou le vôtre)

Le script va :
- Configurer automatiquement le webhook
- Créer les fichiers `.env` et WSGI
- Afficher les instructions complètes

### Étape 2: Upload sur PythonAnywhere

1. **Connectez-vous à PythonAnywhere**
2. **Allez dans Files**
3. **Uploadez dans `/home/votreusername/mysite/` :**
   - `flask_app.py`
   - `simple_user_manager.py`
   - `.env` (généré par le script)
   - `votreusername_pythonanywhere_com_wsgi.py` (généré)

### Étape 3: Installation des dépendances

Dans une **Console Bash** :

```bash
cd /home/votreusername/mysite
pip3.10 install --user flask requests python-dotenv
```

### Étape 4: Configuration de l'application web

1. **Onglet Web** → **Add a new web app**
2. **Choisissez Flask** et **Python 3.10**
3. **Dans WSGI configuration**, remplacez le contenu par celui du fichier généré

### Étape 5: Test

1. **Rechargez** l'application web
2. **Testez** : `https://votreusername.pythonanywhere.com/health`
3. **Envoyez** `/start` à votre bot

---

## ⚙️ Installation Manuelle

Si vous préférez configurer manuellement :

### 1. Création des fichiers

**Fichier `.env` :**
```env
BOT_TOKEN=7573497633:AAHk9K15yTCiJP-zruJrc9v8eK8I9XhjyH4
WEBHOOK_SECRET=votre_secret_token_aleatoire
ADMIN_ID=1190237801
```

**Fichier WSGI (remplacez `votreusername`) :**
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

from flask_app import app as application
```

### 2. Configuration du webhook

```bash
# Dans une console Python
import requests
import secrets

# Générer un token secret
secret_token = secrets.token_urlsafe(32)
print(f"Secret Token: {secret_token}")

# Configurer le webhook
bot_token = "7573497633:AAHk9K15yTCiJP-zruJrc9v8eK8I9XhjyH4"
webhook_url = f"https://votreusername.pythonanywhere.com/{secret_token}"

response = requests.post(
    f"https://api.telegram.org/bot{bot_token}/setWebhook",
    json={"url": webhook_url}
)

print(response.json())
```

---

## 🔧 URLs Importantes

Une fois installé, votre bot aura ces endpoints :

```
https://votreusername.pythonanywhere.com/         # Page d'accueil
https://votreusername.pythonanywhere.com/health  # Santé de l'app
https://votreusername.pythonanywhere.com/webhook_info # Info webhook
https://votreusername.pythonanywhere.com/admin/stats  # Stats admin
https://votreusername.pythonanywhere.com/SECRET_TOKEN # Webhook Telegram
```

## 🧪 Tests de Vérification

### Test 1: Santé de l'application
```bash
curl https://votreusername.pythonanywhere.com/health
```

### Test 2: Information webhook
```bash
curl https://api.telegram.org/bot7573497633:AAHk9K15yTCiJP-zruJrc9v8eK8I9XhjyH4/getWebhookInfo
```

### Test 3: Bot Telegram
Envoyez `/start` dans votre chat avec le bot.

---

## ❗ Dépannage

### Le bot ne répond pas

1. **Vérifiez les logs** dans PythonAnywhere
2. **Testez l'endpoint** `/health`
3. **Vérifiez le webhook** avec `/webhook_info`
4. **Reconfigurez** si nécessaire

### Erreur 500

1. **Vérifiez** que Flask est installé
2. **Vérifiez** le fichier WSGI
3. **Consultez** les logs d'erreur

### Webhook non configuré

1. **Exécutez** le script d'installation
2. **Vérifiez** le token secret
3. **Testez** avec curl

---

## 🎉 Fonctionnalités Disponibles

### Commandes Utilisateur
- `/start` - Démarrer le bot
- `/status` - Voir son statut
- `/help` - Aide
- `/pronostics` - Pronostics football

### Commandes Admin
- `/activer user_id plan` - Activer un utilisateur

### Gestion des Licences
- **Plans** : semaine (1000f), mois (3000f)
- **Expiration** automatique
- **Vérification** d'accès

---

## 📞 Support

En cas de problème :
1. Consultez les logs PythonAnywhere
2. Vérifiez que tous les fichiers sont uploadés
3. Testez les endpoints un par un
4. Contactez le support si nécessaire

**Votre bot Téléfoot est maintenant prêt sur PythonAnywhere !** 🎊