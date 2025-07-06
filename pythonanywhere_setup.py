#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de configuration pour PythonAnywhere
Configure automatiquement le webhook pour le bot Téléfoot
"""

import requests
import os
import secrets
import json
from datetime import datetime

class PythonAnywhereSetup:
    """Configuration du webhook sur PythonAnywhere"""
    
    def __init__(self):
        self.bot_token = os.getenv('BOT_TOKEN', '7573497633:AAHk9K15yTCiJP-zruJrc9v8eK8I9XhjyH4')
        self.secret_token = os.getenv('WEBHOOK_SECRET') or secrets.token_urlsafe(32)
        self.domain = None  # À définir avec votre nom d'utilisateur PythonAnywhere
        
    def set_domain(self, username):
        """Définit le domaine PythonAnywhere"""
        self.domain = f"https://{username}.pythonanywhere.com"
        
    def test_bot_token(self):
        """Teste si le token du bot est valide"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getMe"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    bot_info = data.get('result', {})
                    print(f"✅ Bot Token valide: @{bot_info.get('username')} ({bot_info.get('id')})")
                    return True
                else:
                    print(f"❌ Erreur API: {data.get('description')}")
                    return False
            else:
                print(f"❌ Erreur HTTP: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors du test: {e}")
            return False
    
    def remove_webhook(self):
        """Supprime le webhook existant"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/deleteWebhook"
            response = requests.post(url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    print("✅ Webhook précédent supprimé")
                    return True
                else:
                    print(f"❌ Erreur suppression: {data.get('description')}")
                    return False
            else:
                print(f"❌ Erreur HTTP: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la suppression: {e}")
            return False
    
    def set_webhook(self):
        """Configure le webhook"""
        if not self.domain:
            print("❌ Domaine PythonAnywhere non défini. Utilisez set_domain() d'abord.")
            return False
            
        try:
            webhook_url = f"{self.domain}/{self.secret_token}"
            url = f"https://api.telegram.org/bot{self.bot_token}/setWebhook"
            
            data = {
                "url": webhook_url,
                "max_connections": 40,
                "allowed_updates": ["message", "callback_query"]
            }
            
            response = requests.post(url, json=data)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('ok'):
                    print(f"✅ Webhook configuré: {webhook_url}")
                    return True
                else:
                    print(f"❌ Erreur configuration: {result.get('description')}")
                    return False
            else:
                print(f"❌ Erreur HTTP: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur lors de la configuration: {e}")
            return False
    
    def get_webhook_info(self):
        """Récupère les informations du webhook"""
        try:
            url = f"https://api.telegram.org/bot{self.bot_token}/getWebhookInfo"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    webhook_info = data.get('result', {})
                    print("\n📡 Informations du webhook:")
                    print(f"URL: {webhook_info.get('url', 'Aucune')}")
                    print(f"Connexions max: {webhook_info.get('max_connections', 'N/A')}")
                    print(f"Messages en attente: {webhook_info.get('pending_update_count', 0)}")
                    print(f"Dernière erreur: {webhook_info.get('last_error_message', 'Aucune')}")
                    return webhook_info
                else:
                    print(f"❌ Erreur API: {data.get('description')}")
                    return None
            else:
                print(f"❌ Erreur HTTP: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Erreur lors de la récupération: {e}")
            return None
    
    def generate_env_file(self):
        """Génère un fichier .env avec les variables nécessaires"""
        env_content = f"""# Configuration PythonAnywhere pour Téléfoot Bot
BOT_TOKEN={self.bot_token}
WEBHOOK_SECRET={self.secret_token}
API_ID=29177661
API_HASH=a8639172fa8d35dbfd8ea46286d349ab
ADMIN_ID=1190237801

# URLs importantes
WEBHOOK_URL={self.domain}/{self.secret_token}
HEALTH_CHECK_URL={self.domain}/health
"""
        
        with open('.env', 'w') as f:
            f.write(env_content)
        
        print("✅ Fichier .env créé avec la configuration")
        return True
    
    def generate_config_json(self):
        """Génère un fichier de configuration JSON"""
        config = {
            "bot_token": self.bot_token,
            "webhook_secret": self.secret_token,
            "domain": self.domain,
            "created_at": datetime.now().isoformat(),
            "endpoints": {
                "webhook": f"{self.domain}/{self.secret_token}",
                "health": f"{self.domain}/health",
                "info": f"{self.domain}/webhook_info"
            }
        }
        
        with open('pythonanywhere_config.json', 'w') as f:
            json.dump(config, f, indent=2)
        
        print("✅ Configuration sauvegardée dans pythonanywhere_config.json")
        return True
    
    def complete_setup(self, username):
        """Effectue la configuration complète"""
        print("🚀 Configuration PythonAnywhere pour Téléfoot Bot")
        print("=" * 50)
        
        # Étape 1: Définir le domaine
        self.set_domain(username)
        print(f"📡 Domaine: {self.domain}")
        
        # Étape 2: Tester le token
        if not self.test_bot_token():
            print("❌ Configuration interrompue: Token invalide")
            return False
        
        # Étape 3: Supprimer l'ancien webhook
        self.remove_webhook()
        
        # Étape 4: Configurer le nouveau webhook
        if not self.set_webhook():
            print("❌ Configuration interrompue: Impossible de configurer le webhook")
            return False
        
        # Étape 5: Vérifier la configuration
        self.get_webhook_info()
        
        # Étape 6: Générer les fichiers de configuration
        self.generate_env_file()
        self.generate_config_json()
        
        print("\n✅ Configuration terminée avec succès!")
        print(f"🔐 Secret Token: {self.secret_token}")
        print(f"📡 Webhook URL: {self.domain}/{self.secret_token}")
        print("\n📋 Prochaines étapes:")
        print("1. Uploadez webhook_app.py sur PythonAnywhere")
        print("2. Installez les dépendances: flask, requests")
        print("3. Configurez l'app web Flask sur PythonAnywhere")
        print("4. Testez le webhook avec un message au bot")
        
        return True

def main():
    """Fonction principale pour la configuration"""
    setup = PythonAnywhereSetup()
    
    # Demander le nom d'utilisateur PythonAnywhere
    username = input("Entrez votre nom d'utilisateur PythonAnywhere: ").strip()
    
    if not username:
        print("❌ Nom d'utilisateur requis")
        return
    
    # Effectuer la configuration complète
    setup.complete_setup(username)

if __name__ == "__main__":
    main()