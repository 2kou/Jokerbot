#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script d'installation automatique pour PythonAnywhere
Configure le bot Téléfoot en mode webhook
"""

import requests
import json
import os
import secrets
from datetime import datetime

def configure_webhook(username, bot_token=None):
    """Configure le webhook pour PythonAnywhere"""
    
    # Configuration par défaut
    if not bot_token:
        bot_token = "7573497633:AAHk9K15yTCiJP-zruJrc9v8eK8I9XhjyH4"
    
    # Générer le token secret
    secret_token = secrets.token_urlsafe(32)
    
    # URLs
    domain = f"https://{username}.pythonanywhere.com"
    webhook_url = f"{domain}/{secret_token}"
    
    print("🚀 Configuration PythonAnywhere pour Téléfoot Bot")
    print("=" * 60)
    print(f"👤 Utilisateur: {username}")
    print(f"🔐 Secret Token: {secret_token}")
    print(f"📡 Webhook URL: {webhook_url}")
    print()
    
    # Test du token bot
    print("1. Test du token bot...")
    try:
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getMe")
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                bot_info = data['result']
                print(f"   ✅ Bot valide: @{bot_info['username']} ({bot_info['id']})")
            else:
                print(f"   ❌ Erreur API: {data.get('description')}")
                return False
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    # Supprimer l'ancien webhook
    print("2. Suppression de l'ancien webhook...")
    try:
        response = requests.post(f"https://api.telegram.org/bot{bot_token}/deleteWebhook")
        if response.status_code == 200:
            print("   ✅ Ancien webhook supprimé")
        else:
            print("   ⚠️ Pas d'ancien webhook à supprimer")
    except Exception as e:
        print(f"   ⚠️ Erreur suppression: {e}")
    
    # Configurer le nouveau webhook
    print("3. Configuration du nouveau webhook...")
    try:
        webhook_data = {
            "url": webhook_url,
            "max_connections": 40,
            "allowed_updates": ["message", "callback_query"]
        }
        
        response = requests.post(
            f"https://api.telegram.org/bot{bot_token}/setWebhook",
            json=webhook_data
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                print(f"   ✅ Webhook configuré: {webhook_url}")
            else:
                print(f"   ❌ Erreur configuration: {result.get('description')}")
                return False
        else:
            print(f"   ❌ Erreur HTTP: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Erreur: {e}")
        return False
    
    # Créer le fichier de configuration
    print("4. Création des fichiers de configuration...")
    
    # Fichier .env
    env_content = f"""# Configuration PythonAnywhere - Téléfoot Bot
BOT_TOKEN={bot_token}
WEBHOOK_SECRET={secret_token}
ADMIN_ID=1190237801
PYTHONANYWHERE_USERNAME={username}
WEBHOOK_URL={webhook_url}
"""
    
    with open('.env', 'w', encoding='utf-8') as f:
        f.write(env_content)
    print("   ✅ Fichier .env créé")
    
    # Fichier de configuration JSON
    config = {
        "bot_token": bot_token,
        "webhook_secret": secret_token,
        "domain": domain,
        "webhook_url": webhook_url,
        "username": username,
        "created_at": datetime.now().isoformat(),
        "endpoints": {
            "health": f"{domain}/health",
            "webhook_info": f"{domain}/webhook_info",
            "admin_stats": f"{domain}/admin/stats"
        }
    }
    
    with open('pythonanywhere_config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    print("   ✅ Configuration JSON créée")
    
    # Instructions pour WSGI
    wsgi_content = f"""import sys
import os

# Chemin vers votre projet
project_home = '/home/{username}/mysite'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Charger les variables d'environnement
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_home, '.env'))
except:
    pass

# Importer l'application Flask
from flask_app import app as application

if __name__ == "__main__":
    application.run()
"""
    
    with open(f'{username}_pythonanywhere_com_wsgi.py', 'w', encoding='utf-8') as f:
        f.write(wsgi_content)
    print(f"   ✅ Fichier WSGI créé: {username}_pythonanywhere_com_wsgi.py")
    
    # Vérification finale
    print("5. Vérification de la configuration...")
    try:
        response = requests.get(f"https://api.telegram.org/bot{bot_token}/getWebhookInfo")
        if response.status_code == 200:
            data = response.json()
            if data.get('ok'):
                webhook_info = data['result']
                print(f"   ✅ URL configurée: {webhook_info.get('url', 'Aucune')}")
                print(f"   📊 Messages en attente: {webhook_info.get('pending_update_count', 0)}")
                if webhook_info.get('last_error_message'):
                    print(f"   ⚠️ Dernière erreur: {webhook_info['last_error_message']}")
    except Exception as e:
        print(f"   ⚠️ Impossible de vérifier: {e}")
    
    print("\n" + "=" * 60)
    print("✅ CONFIGURATION TERMINÉE AVEC SUCCÈS!")
    print("\n📋 PROCHAINES ÉTAPES SUR PYTHONANYWHERE:")
    print("1. Uploadez ces fichiers dans /home/{}/mysite/:".format(username))
    print("   - flask_app.py")
    print("   - simple_user_manager.py")
    print("   - .env")
    print("   - {}_pythonanywhere_com_wsgi.py".format(username))
    print("\n2. Installez les dépendances:")
    print("   pip3.10 install --user flask requests python-dotenv")
    print("\n3. Configurez l'application web:")
    print("   - Allez dans l'onglet Web")
    print("   - Créez une nouvelle app Flask")
    print("   - Utilisez le fichier WSGI généré")
    print("\n4. Testez le bot:")
    print(f"   - Health check: {domain}/health")
    print(f"   - Webhook info: {domain}/webhook_info")
    print("   - Envoyez /start à votre bot")
    print(f"\n🔐 Gardez précieusement votre secret token: {secret_token}")
    
    return True

def main():
    """Fonction principale"""
    print("Configuration PythonAnywhere pour Téléfoot Bot")
    print("=" * 50)
    
    # Demander le nom d'utilisateur
    username = input("\n📝 Entrez votre nom d'utilisateur PythonAnywhere: ").strip()
    
    if not username:
        print("❌ Nom d'utilisateur requis!")
        return
    
    # Demander le token bot (optionnel)
    bot_token = input("\n🤖 Token bot (appuyez sur Entrée pour utiliser celui par défaut): ").strip()
    
    # Configuration
    if configure_webhook(username, bot_token or None):
        print("\n🎉 Configuration réussie! Suivez les instructions ci-dessus.")
    else:
        print("\n❌ Échec de la configuration. Vérifiez vos paramètres.")

if __name__ == "__main__":
    main()