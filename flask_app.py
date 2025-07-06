#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Application Flask pour PythonAnywhere - Téléfoot Bot
Version simplifiée et optimisée pour l'hébergement
"""

from flask import Flask, request, jsonify
import json
import os
import secrets
from datetime import datetime
import logging
import requests

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SECRET_TOKEN = os.getenv('WEBHOOK_SECRET', secrets.token_urlsafe(32))
BOT_TOKEN = os.getenv('BOT_TOKEN', '7573497633:AAHk9K15yTCiJP-zruJrc9v8eK8I9XhjyH4')
ADMIN_ID = int(os.getenv('ADMIN_ID', '1190237801'))

# Import du gestionnaire d'utilisateurs simplifié
from simple_user_manager import SimpleUserManager

# Initialisation
app = Flask(__name__)
user_manager = SimpleUserManager()

class TelefootWebhook:
    """Gestionnaire webhook pour Téléfoot Bot"""
    
    def __init__(self, user_manager):
        self.user_manager = user_manager
    
    def send_telegram_message(self, chat_id, text, parse_mode='Markdown'):
        """Envoie un message via l'API Telegram"""
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            
            response = requests.post(url, json=data)
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Erreur envoi message: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Erreur envoi message: {e}")
            return None
    
    def process_message(self, message):
        """Traite un message reçu"""
        try:
            chat_id = message['chat']['id']
            user_id = str(message['from']['id'])
            
            if 'text' not in message:
                return self.send_telegram_message(chat_id, "Je ne peux traiter que les messages texte.")
            
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
                return self.send_telegram_message(chat_id, "❓ Commande non reconnue. Utilisez /help pour l'aide.")
                
        except Exception as e:
            logger.error(f"Erreur traitement message: {e}")
            return self.send_telegram_message(chat_id, "❌ Erreur lors du traitement.")
    
    def handle_start(self, chat_id, user_id):
        """Traite /start"""
        # Enregistrer l'utilisateur s'il n'existe pas
        if user_id not in self.user_manager.users:
            self.user_manager.register_new_user(user_id)
        
        # Vérifier l'accès
        if not self.user_manager.check_user_access(user_id):
            return self.send_telegram_message(
                chat_id, 
                self.user_manager.messages["access_expired"]
            )
        
        # Message d'accueil
        welcome_msg = (
            "🤖 **TeleFoot Bot - Bienvenue !**\n\n"
            "✅ Votre licence est active\n\n"
            "📱 **Commandes disponibles :**\n"
            "• `/pronostics` - Pronostics du jour\n"
            "• `/status` - Votre statut\n"
            "• `/help` - Aide complète\n\n"
            "💰 **Tarifs :**\n"
            "• 1 semaine = 1000f\n"
            "• 1 mois = 3000f\n\n"
            "📞 **Contact :** Sossou Kouamé"
        )
        
        return self.send_telegram_message(chat_id, welcome_msg)
    
    def handle_status(self, chat_id, user_id):
        """Traite /status"""
        user_info = self.user_manager.get_user_info(user_id)
        
        if not user_info:
            return self.send_telegram_message(
                chat_id, 
                "❌ Utilisateur non enregistré. Utilisez /start pour commencer."
            )
        
        status = self.user_manager.get_user_status(user_id)
        expire_date = self.user_manager.get_expiration_date(user_id)
        
        if status == "actif":
            status_msg = (
                f"✅ **Statut :** Actif\n"
                f"📅 **Expire le :** {expire_date}\n"
                f"🔐 **Clé :** {user_info.get('license_key', 'N/A')}"
            )
        else:
            status_msg = (
                f"❌ **Statut :** {status}\n"
                f"💬 Contactez Sossou Kouamé pour activer votre licence."
            )
        
        return self.send_telegram_message(chat_id, status_msg)
    
    def handle_help(self, chat_id, user_id):
        """Traite /help"""
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
        
        return self.send_telegram_message(chat_id, help_msg)
    
    def handle_pronostics(self, chat_id, user_id):
        """Traite /pronostics"""
        if not self.user_manager.check_user_access(user_id):
            return self.send_telegram_message(
                chat_id, 
                self.user_manager.messages["access_expired"]
            )
        
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
        
        return self.send_telegram_message(chat_id, pronostics_msg)
    
    def handle_activate(self, chat_id, text):
        """Traite /activer (admin uniquement)"""
        try:
            parts = text.split()
            if len(parts) != 3:
                return self.send_telegram_message(
                    chat_id,
                    "❌ Format incorrect. Utilisez : `/activer user_id plan`\n"
                    "Exemple : `/activer 123456789 semaine`"
                )
            
            _, user_id, plan = parts
            
            if plan not in ["semaine", "mois"]:
                return self.send_telegram_message(
                    chat_id, 
                    self.user_manager.messages["invalid_plan"]
                )
            
            # Activation
            license_key, expires = self.user_manager.activate_user(user_id, plan)
            
            # Notifier l'admin
            admin_msg = f"✅ Utilisateur {user_id} activé pour 1 {plan}\n🔐 Clé : {license_key}"
            
            # Notifier l'utilisateur
            user_msg = self.user_manager.messages["license_activated"].format(
                license_key=license_key,
                expires=expires
            )
            
            self.send_telegram_message(int(user_id), user_msg)
            
            return self.send_telegram_message(chat_id, admin_msg)
            
        except Exception as e:
            logger.error(f"Erreur activation: {e}")
            return self.send_telegram_message(
                chat_id, 
                f"❌ Erreur lors de l'activation : {str(e)}"
            )

# Initialisation du webhook
webhook_handler = TelefootWebhook(user_manager)

# Routes Flask
@app.route('/')
def index():
    """Page d'accueil"""
    return jsonify({
        "status": "ok",
        "message": "TeleFoot Bot Webhook - PythonAnywhere",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0"
    })

@app.route('/health')
def health_check():
    """Contrôle de santé"""
    stats = user_manager.get_stats()
    return jsonify({
        "status": "healthy",
        "users": stats,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/webhook_info')
def webhook_info():
    """Informations sur le webhook"""
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"
        response = requests.get(url)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({"error": "Impossible de récupérer les infos"}), 500
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route(f'/{SECRET_TOKEN}', methods=['POST'])
def telegram_webhook():
    """Endpoint principal du webhook"""
    try:
        update = request.get_json()
        
        if not update:
            return jsonify({"error": "Pas de données"}), 400
        
        logger.info(f"Webhook reçu: {update}")
        
        # Traiter le message
        if 'message' in update:
            message = update['message']
            webhook_handler.process_message(message)
            return jsonify({"status": "ok"})
        
        # Traiter les callback queries
        elif 'callback_query' in update:
            callback_query = update['callback_query']
            webhook_handler.send_telegram_message(
                callback_query['message']['chat']['id'],
                "Fonctionnalité non disponible en mode webhook"
            )
            return jsonify({"status": "ok"})
        
        return jsonify({"status": "ok"})
        
    except Exception as e:
        logger.error(f"Erreur webhook: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/admin/stats')
def admin_stats():
    """Statistiques admin"""
    stats = user_manager.get_stats()
    return jsonify({
        "stats": stats,
        "secret_token": SECRET_TOKEN,
        "webhook_url": f"https://votreusername.pythonanywhere.com/{SECRET_TOKEN}",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    print(f"🔐 Secret Token: {SECRET_TOKEN}")
    print(f"📡 Webhook URL: https://votreusername.pythonanywhere.com/{SECRET_TOKEN}")
    app.run(debug=True, host='0.0.0.0', port=5000)