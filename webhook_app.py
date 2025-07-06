#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Webhook Flask App pour Téléfoot Bot sur PythonAnywhere
Version adaptée du bot principal pour fonctionner avec des webhooks
"""

from flask import Flask, request, jsonify
import json
import os
import secrets
from datetime import datetime
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration du webhook
SECRET_TOKEN = os.getenv('WEBHOOK_SECRET', secrets.token_urlsafe(32))
BOT_TOKEN = os.getenv('BOT_TOKEN', '7573497633:AAHk9K15yTCiJP-zruJrc9v8eK8I9XhjyH4')
API_ID = int(os.getenv('API_ID', '29177661'))
API_HASH = os.getenv('API_HASH', 'a8639172fa8d35dbfd8ea46286d349ab')
ADMIN_ID = int(os.getenv('ADMIN_ID', '1190237801'))

# Configuration Flask
app = Flask(__name__)

# Import des modules du bot - avec gestion d'erreur
try:
    from user_manager import UserManager
    from config import MESSAGES, PLANS
    user_manager = UserManager()
except ImportError as e:
    logger.error(f"Erreur d'importation: {e}")
    # Configuration minimale en cas d'erreur
    MESSAGES = {
        "access_expired": "⛔ Accès expiré. Contactez l'admin.",
        "invalid_plan": "❌ Plan invalide"
    }
    PLANS = {"semaine": {"duration_days": 7}, "mois": {"duration_days": 30}}
    user_manager = None

class WebhookBot:
    """Gestionnaire du bot en mode webhook"""
    
    def __init__(self):
        self.user_manager = UserManager()
        
    def process_message(self, message):
        """Traite un message reçu via webhook"""
        try:
            chat_id = message['chat']['id']
            user_id = str(message['from']['id'])
            
            # Vérifier si c'est un message texte
            if 'text' not in message:
                return {"method": "sendMessage", "chat_id": chat_id, "text": "Je ne peux traiter que les messages texte."}
            
            text = message['text']
            
            # Traiter les commandes
            if text == '/start':
                return self.handle_start(chat_id, user_id)
            elif text == '/status':
                return self.handle_status(chat_id, user_id)
            elif text == '/help':
                return self.handle_help(chat_id, user_id)
            elif text == '/pronostics':
                return self.handle_pronostics(chat_id, user_id)
            elif text.startswith('/activer') and int(message['from']['id']) == ADMIN_ID:
                return self.handle_activate(chat_id, text)
            else:
                return self.handle_unknown_command(chat_id, user_id)
                
        except Exception as e:
            logger.error(f"Erreur lors du traitement du message: {e}")
            return {"method": "sendMessage", "chat_id": chat_id, "text": "❌ Erreur lors du traitement de votre message."}
    
    def handle_start(self, chat_id, user_id):
        """Traite la commande /start"""
        # Enregistrement automatique du nouvel utilisateur
        if user_id not in self.user_manager.users:
            self.user_manager.register_new_user(user_id)
        
        # Vérification de l'accès
        if not self.user_manager.check_user_access(user_id):
            return {
                "method": "sendMessage",
                "chat_id": chat_id,
                "text": MESSAGES["access_expired"],
                "parse_mode": "Markdown"
            }
        
        # Utilisateur actif - Message d'accueil
        welcome_msg = (
            "🤖 **TeleFoot Bot - Bienvenue !**\n\n"
            "✅ Votre licence est active\n\n"
            "📱 **Commandes principales :**\n"
            "• `/pronostics` - Pronostics du jour\n"
            "• `/status` - Votre statut\n"
            "• `/help` - Aide complète\n\n"
            "💰 **Tarifs :**\n"
            "• 1 semaine = 1000f\n"
            "• 1 mois = 3000f\n\n"
            "📞 **Contact :** Sossou Kouamé"
        )
        
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": welcome_msg,
            "parse_mode": "Markdown"
        }
    
    def handle_status(self, chat_id, user_id):
        """Traite la commande /status"""
        user_info = self.user_manager.get_user_info(user_id)
        
        if not user_info:
            return {
                "method": "sendMessage",
                "chat_id": chat_id,
                "text": "❌ Utilisateur non enregistré. Utilisez /start pour commencer."
            }
        
        status = self.user_manager.get_user_status(user_id)
        expire_date = self.user_manager.get_expiration_date(user_id)
        
        if status == "actif":
            status_msg = f"✅ **Statut :** Actif\n📅 **Expire le :** {expire_date}\n🔐 **Clé :** {user_info.get('license_key', 'N/A')}"
        else:
            status_msg = f"❌ **Statut :** {status}\n💬 Contactez Sossou Kouamé pour activer votre licence."
        
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": status_msg,
            "parse_mode": "Markdown"
        }
    
    def handle_help(self, chat_id, user_id):
        """Traite la commande /help"""
        help_msg = (
            "📋 **Aide TeleFoot Bot**\n\n"
            "🤖 **Commandes disponibles :**\n"
            "• `/start` - Commencer\n"
            "• `/status` - Voir votre statut\n"
            "• `/pronostics` - Pronostics du jour\n"
            "• `/help` - Cette aide\n\n"
            "💰 **Tarifs :**\n"
            "• 1 semaine = 1000f\n"
            "• 1 mois = 3000f\n\n"
            "📞 **Contact :** Sossou Kouamé\n"
            "📧 **Support :** Via Telegram"
        )
        
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": help_msg,
            "parse_mode": "Markdown"
        }
    
    def handle_pronostics(self, chat_id, user_id):
        """Traite la commande /pronostics"""
        if not self.user_manager.check_user_access(user_id):
            return {
                "method": "sendMessage",
                "chat_id": chat_id,
                "text": MESSAGES["access_expired"],
                "parse_mode": "Markdown"
            }
        
        # Pronostics du jour
        today = datetime.now().strftime("%d/%m/%Y")
        pronostics_msg = (
            f"⚽ **Pronostics du {today}**\n\n"
            "🏆 **Matchs Premium :**\n"
            "• Real Madrid vs Barcelona - **1X** (Cote: 1.85)\n"
            "• Manchester City vs Liverpool - **Over 2.5** (Cote: 1.75)\n"
            "• PSG vs Marseille - **1** (Cote: 1.65)\n\n"
            "📈 **Analyse :**\n"
            "• Confiance élevée sur les 3 matchs\n"
            "• Bankroll recommandé : 5% par pari\n\n"
            "🎯 **Prédiction du jour :** 85% de réussite\n"
            "💰 **Gain potentiel :** +150% sur mise totale"
        )
        
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": pronostics_msg,
            "parse_mode": "Markdown"
        }
    
    def handle_activate(self, chat_id, text):
        """Traite la commande /activer (admin seulement)"""
        try:
            parts = text.split()
            if len(parts) != 3:
                return {
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": "❌ Format incorrect. Utilisez : `/activer user_id plan`\nExemple : `/activer 123456789 semaine`",
                    "parse_mode": "Markdown"
                }
            
            _, user_id, plan = parts
            
            if plan not in ["semaine", "mois"]:
                return {
                    "method": "sendMessage",
                    "chat_id": chat_id,
                    "text": MESSAGES["invalid_plan"]
                }
            
            # Activation de l'utilisateur
            license_key, expires = self.user_manager.activate_user(user_id, plan)
            
            return {
                "method": "sendMessage",
                "chat_id": chat_id,
                "text": f"✅ Utilisateur {user_id} activé pour 1 {plan}\n🔐 Clé : {license_key}",
                "parse_mode": "Markdown"
            }
            
        except Exception as e:
            return {
                "method": "sendMessage",
                "chat_id": chat_id,
                "text": f"❌ Erreur lors de l'activation : {str(e)}"
            }
    
    def handle_unknown_command(self, chat_id, user_id):
        """Traite les commandes inconnues"""
        return {
            "method": "sendMessage",
            "chat_id": chat_id,
            "text": "❓ Commande non reconnue. Utilisez /help pour voir les commandes disponibles."
        }

# Initialisation du bot webhook
webhook_bot = WebhookBot()

@app.route('/')
def index():
    """Page d'accueil pour vérifier que l'app fonctionne"""
    return jsonify({
        "status": "ok",
        "message": "TeleFoot Bot Webhook is running",
        "timestamp": datetime.now().isoformat()
    })

@app.route('/health')
def health_check():
    """Endpoint de santé"""
    return jsonify({
        "status": "healthy",
        "users_count": len(user_manager.users),
        "timestamp": datetime.now().isoformat()
    })

@app.route(f'/{SECRET_TOKEN}', methods=['POST'])
def telegram_webhook():
    """Endpoint principal pour recevoir les webhooks de Telegram"""
    try:
        # Récupérer les données du webhook
        update = request.get_json()
        
        if not update:
            return jsonify({"error": "No data received"}), 400
        
        logger.info(f"Webhook reçu: {update}")
        
        # Traiter le message
        if 'message' in update:
            message = update['message']
            response = webhook_bot.process_message(message)
            
            # Retourner la réponse pour que Telegram l'envoie
            return jsonify(response)
        
        # Traiter les callback queries (boutons)
        elif 'callback_query' in update:
            callback_query = update['callback_query']
            return jsonify({
                "method": "answerCallbackQuery",
                "callback_query_id": callback_query['id'],
                "text": "Fonctionnalité non disponible en mode webhook"
            })
        
        return jsonify({"status": "ok"})
        
    except Exception as e:
        logger.error(f"Erreur webhook: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/set_webhook', methods=['POST'])
def set_webhook():
    """Endpoint pour configurer le webhook (admin seulement)"""
    try:
        # Vérifier les paramètres
        data = request.get_json()
        if not data or 'admin_key' not in data:
            return jsonify({"error": "Admin key required"}), 401
        
        # Ici vous pourriez ajouter une vérification d'admin key
        webhook_url = data.get('webhook_url')
        if not webhook_url:
            return jsonify({"error": "webhook_url required"}), 400
        
        # Configuration du webhook via l'API Telegram
        import requests
        
        telegram_api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/setWebhook"
        webhook_data = {
            "url": f"{webhook_url}/{SECRET_TOKEN}",
            "max_connections": 40,
            "allowed_updates": ["message", "callback_query"]
        }
        
        response = requests.post(telegram_api_url, json=webhook_data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('ok'):
                return jsonify({
                    "status": "success",
                    "message": "Webhook configuré avec succès",
                    "webhook_url": f"{webhook_url}/{SECRET_TOKEN}"
                })
            else:
                return jsonify({"error": result.get('description', 'Erreur inconnue')}), 500
        else:
            return jsonify({"error": "Erreur lors de la configuration"}), 500
            
    except Exception as e:
        logger.error(f"Erreur configuration webhook: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/webhook_info')
def webhook_info():
    """Informations sur le webhook actuel"""
    try:
        import requests
        
        telegram_api_url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
        response = requests.get(telegram_api_url)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Impossible de récupérer les infos webhook"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Afficher le token secret pour la configuration
    print(f"🔐 Secret Token: {SECRET_TOKEN}")
    print(f"📡 Webhook URL: https://yourusername.pythonanywhere.com/{SECRET_TOKEN}")
    
    # Démarrer l'application Flask
    app.run(debug=True, host='0.0.0.0', port=5000)