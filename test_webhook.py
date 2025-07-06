#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script de test pour le webhook PythonAnywhere
Teste les fonctionnalités du bot en mode webhook
"""

import requests
import json
import os
from datetime import datetime

class WebhookTester:
    """Testeur pour le webhook PythonAnywhere"""
    
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.bot_token = os.getenv('BOT_TOKEN', '7573497633:AAHk9K15yTCiJP-zruJrc9v8eK8I9XhjyH4')
        
    def test_health_endpoint(self):
        """Test l'endpoint de santé"""
        try:
            response = requests.get(f"{self.base_url}/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Health check OK: {data}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur health check: {e}")
            return False
    
    def test_webhook_info(self):
        """Test l'endpoint d'info webhook"""
        try:
            response = requests.get(f"{self.base_url}/webhook_info")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Webhook info OK: {data}")
                return True
            else:
                print(f"❌ Webhook info failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur webhook info: {e}")
            return False
    
    def test_telegram_webhook(self):
        """Test le webhook Telegram directement"""
        try:
            # Vérifier l'état du webhook via l'API Telegram
            url = f"https://api.telegram.org/bot{self.bot_token}/getWebhookInfo"
            response = requests.get(url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    webhook_info = data.get('result', {})
                    print("✅ Webhook Telegram configuré:")
                    print(f"   URL: {webhook_info.get('url', 'Aucune')}")
                    print(f"   Messages en attente: {webhook_info.get('pending_update_count', 0)}")
                    print(f"   Dernière erreur: {webhook_info.get('last_error_message', 'Aucune')}")
                    return True
                else:
                    print(f"❌ Erreur API Telegram: {data.get('description')}")
                    return False
            else:
                print(f"❌ Erreur HTTP Telegram: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur test webhook Telegram: {e}")
            return False
    
    def simulate_webhook_message(self, secret_token, message_text="/start"):
        """Simule un message webhook"""
        try:
            # Simuler un message webhook
            webhook_data = {
                "update_id": 123456789,
                "message": {
                    "message_id": 1,
                    "from": {
                        "id": 1190237801,
                        "is_bot": False,
                        "first_name": "Test",
                        "username": "testuser"
                    },
                    "chat": {
                        "id": 1190237801,
                        "type": "private"
                    },
                    "date": int(datetime.now().timestamp()),
                    "text": message_text
                }
            }
            
            response = requests.post(
                f"{self.base_url}/{secret_token}",
                json=webhook_data,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Simulation webhook OK: {data}")
                return True
            else:
                print(f"❌ Simulation webhook failed: {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur simulation webhook: {e}")
            return False
    
    def run_all_tests(self, secret_token=None):
        """Exécute tous les tests"""
        print("🧪 Tests du webhook PythonAnywhere")
        print("=" * 50)
        
        tests_passed = 0
        total_tests = 0
        
        # Test 1: Health check
        print("\n1. Test Health Check")
        total_tests += 1
        if self.test_health_endpoint():
            tests_passed += 1
        
        # Test 2: Webhook info
        print("\n2. Test Webhook Info")
        total_tests += 1
        if self.test_webhook_info():
            tests_passed += 1
        
        # Test 3: Telegram webhook
        print("\n3. Test Telegram Webhook")
        total_tests += 1
        if self.test_telegram_webhook():
            tests_passed += 1
        
        # Test 4: Simulation webhook (si secret fourni)
        if secret_token:
            print("\n4. Test Simulation Webhook")
            total_tests += 1
            if self.simulate_webhook_message(secret_token):
                tests_passed += 1
        
        # Résultats
        print("\n" + "=" * 50)
        print(f"🧪 Résultats: {tests_passed}/{total_tests} tests réussis")
        
        if tests_passed == total_tests:
            print("✅ Tous les tests sont passés!")
            return True
        else:
            print("❌ Certains tests ont échoué.")
            return False

def main():
    """Fonction principale de test"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python test_webhook.py <URL_BASE> [SECRET_TOKEN]")
        print("Exemple: python test_webhook.py https://votreusername.pythonanywhere.com")
        return
    
    base_url = sys.argv[1]
    secret_token = sys.argv[2] if len(sys.argv) > 2 else None
    
    tester = WebhookTester(base_url)
    tester.run_all_tests(secret_token)

if __name__ == "__main__":
    main()