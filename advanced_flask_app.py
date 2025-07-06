#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot Telegram avancé avec système d'approbation, licences personnelles et redirection multi-canaux
"""

from flask import Flask, request, jsonify
import json
import os
import secrets
import asyncio
from datetime import datetime
import logging
import requests
from typing import Dict, List
from advanced_user_manager import AdvancedUserManager

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SECRET_TOKEN = os.getenv('WEBHOOK_SECRET', secrets.token_urlsafe(32))
BOT_TOKEN = os.getenv('BOT_TOKEN', '7573497633:AAHk9K15yTCiJP-zruJrc9v8eK8I9XhjyH4')
ADMIN_ID = int(os.getenv('ADMIN_ID', '1190237801'))

# Initialisation
app = Flask(__name__)
user_manager = AdvancedUserManager()

class AdvancedTelefootBot:
    """Bot Telegram avancé avec toutes les nouvelles fonctionnalités"""
    
    def __init__(self, user_manager: AdvancedUserManager):
        self.user_manager = user_manager
        self.waiting_for_license = {}  # Utilisateurs en attente de saisie de licence
        self.channel_redirections = {}  # Redirections actives par utilisateur
        
    def send_message(self, chat_id: int, text: str, parse_mode: str = 'Markdown', 
                    reply_markup: Dict = None) -> bool:
        """Envoie un message via l'API Telegram"""
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": chat_id,
                "text": text,
                "parse_mode": parse_mode
            }
            
            if reply_markup:
                data["reply_markup"] = reply_markup
            
            response = requests.post(url, json=data)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Erreur envoi message: {e}")
            return False
    
    def send_message_as_channel(self, channel_id: int, text: str, 
                               source_message_id: int = None) -> bool:
        """Envoie un message qui apparaît comme venant du canal"""
        try:
            url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": channel_id,
                "text": text,
                "parse_mode": "Markdown"
            }
            
            # Si c'est une réponse à un message, ajouter la référence
            if source_message_id:
                data["reply_to_message_id"] = source_message_id
            
            response = requests.post(url, json=data)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Erreur envoi message canal: {e}")
            return False
    
    def create_inline_keyboard(self, buttons: List[List[Dict]]) -> Dict:
        """Crée un clavier inline"""
        return {
            "inline_keyboard": buttons
        }
    
    def process_message(self, message: Dict) -> bool:
        """Traite un message reçu"""
        try:
            chat_id = message['chat']['id']
            user_id = str(message['from']['id'])
            text = message.get('text', '')
            
            # Vérifier si l'utilisateur attend une saisie de licence
            if user_id in self.waiting_for_license:
                return self.handle_license_input(chat_id, user_id, text)
            
            # Traiter les commandes
            if text == '/start':
                return self.handle_start(chat_id, user_id, message['from'])
            elif text == '/status':
                return self.handle_status(chat_id, user_id)
            elif text == '/help':
                return self.handle_help(chat_id, user_id)
            elif text == '/pronostics':
                return self.handle_pronostics(chat_id, user_id)
            elif text == '/payer':
                return self.handle_payment_request(chat_id, user_id)
            elif text == '/valider_licence':
                return self.handle_license_validation_request(chat_id, user_id)
            elif text == '/redirections':
                return self.handle_redirections_menu(chat_id, user_id)
            elif text.startswith('/approuver_essai') and int(message['from']['id']) == ADMIN_ID:
                return self.handle_approve_trial(chat_id, text)
            elif text.startswith('/approuver_paiement') and int(message['from']['id']) == ADMIN_ID:
                return self.handle_approve_payment(chat_id, text)
            elif text.startswith('/admin') and int(message['from']['id']) == ADMIN_ID:
                return self.handle_admin_panel(chat_id)
            else:
                return self.send_message(chat_id, "❓ Commande non reconnue. Utilisez /help pour voir les commandes disponibles.")
                
        except Exception as e:
            logger.error(f"Erreur traitement message: {e}")
            return False
    
    def handle_start(self, chat_id: int, user_id: str, user_info: Dict) -> bool:
        """Traite /start avec système d'approbation"""
        username = user_info.get('username', f"User{user_id}")
        
        # Vérifier si l'utilisateur existe
        existing_user = self.user_manager.get_user_info(user_id)
        
        if not existing_user:
            # Nouvel utilisateur - demander approbation
            self.user_manager.register_new_user(user_id, username)
            
            # Notifier l'admin
            admin_msg = (
                f"🆕 **Nouvelle demande d'accès**\n\n"
                f"👤 **Utilisateur :** @{username} ({user_id})\n"
                f"🕐 **Date :** {datetime.now().strftime('%d/%m/%Y à %H:%M')}\n\n"
                f"**Actions :**\n"
                f"`/approuver_essai {user_id}` - Accorder 24h d'essai\n"
                f"`/refuser {user_id}` - Refuser l'accès"
            )
            
            self.send_message(ADMIN_ID, admin_msg)
            
            # Répondre à l'utilisateur
            return self.send_message(chat_id, self.user_manager.messages["welcome_pending"])
        
        # Utilisateur existant
        status = self.user_manager.get_user_status(user_id)
        
        if status == "en_attente":
            return self.send_message(chat_id, self.user_manager.messages["welcome_pending"])
        elif status in ["essai_actif", "actif"]:
            return self.handle_welcome_active_user(chat_id, user_id)
        elif status == "paiement_approuvé":
            return self.send_message(chat_id, self.user_manager.messages["license_validation"])
        else:
            return self.send_message(chat_id, self.user_manager.messages["access_expired"])
    
    def handle_welcome_active_user(self, chat_id: int, user_id: str) -> bool:
        """Message d'accueil pour utilisateur actif"""
        user_info = self.user_manager.get_user_info(user_id)
        status = self.user_manager.get_user_status(user_id)
        
        if status == "essai_actif":
            plan_info = "🔄 **Essai gratuit** (24h)"
        else:
            plan_info = f"💎 **Plan {user_info['plan']}**"
        
        max_redirections = user_info.get('max_redirections', 0)
        current_redirections = user_info.get('current_redirections', 0)
        
        welcome_msg = (
            f"🤖 **TeleFoot Bot - Bienvenue !**\n\n"
            f"✅ {plan_info}\n"
            f"🔄 **Redirections :** {current_redirections}/{max_redirections}\n\n"
            f"📱 **Commandes disponibles :**\n"
            f"• `/pronostics` - Pronostics du jour\n"
            f"• `/redirections` - Gérer les redirections\n"
            f"• `/status` - Votre statut\n"
            f"• `/help` - Aide complète\n"
            f"• `/payer` - Souscrire un abonnement\n\n"
            f"📞 **Contact :** Sossou Kouamé"
        )
        
        return self.send_message(chat_id, welcome_msg)
    
    def handle_payment_request(self, chat_id: int, user_id: str) -> bool:
        """Traite les demandes de paiement"""
        if not self.user_manager.get_user_info(user_id):
            return self.send_message(chat_id, "❌ Utilisez /start pour commencer.")
        
        # Clavier pour choisir le plan
        keyboard = self.create_inline_keyboard([
            [{"text": "1 Semaine - 1000f", "callback_data": f"pay_semaine_{user_id}"}],
            [{"text": "1 Mois - 3000f", "callback_data": f"pay_mois_{user_id}"}],
            [{"text": "❌ Annuler", "callback_data": "cancel_payment"}]
        ])
        
        msg = (
            "💳 **Choisissez votre abonnement**\n\n"
            "📦 **Plans disponibles :**\n"
            "• **1 Semaine** - 1000f (10 redirections)\n"
            "• **1 Mois** - 3000f (50 redirections)\n\n"
            "⚡ **Fonctionnalités :**\n"
            "• Pronostics premium illimités\n"
            "• Redirections multi-canaux\n"
            "• Support prioritaire\n"
            "• Licence personnelle sécurisée"
        )
        
        return self.send_message(chat_id, msg, reply_markup=keyboard)
    
    def handle_license_validation_request(self, chat_id: int, user_id: str) -> bool:
        """Demande de validation de licence"""
        user_info = self.user_manager.get_user_info(user_id)
        
        if not user_info:
            return self.send_message(chat_id, "❌ Utilisez /start pour commencer.")
        
        if user_info["status"] != "payment_approved":
            return self.send_message(chat_id, "❌ Aucune licence en attente de validation.")
        
        # Mettre l'utilisateur en attente de saisie
        self.waiting_for_license[user_id] = True
        
        msg = (
            "🔐 **Validation de licence**\n\n"
            "Envoyez maintenant votre clé de licence personnelle.\n"
            "⚠️ **Attention :** La licence est strictement personnelle.\n\n"
            "📝 **Format attendu :** XXXX-XXXX-XXXX-XXXX\n"
            "💡 **Astuce :** Copiez-collez la clé reçue par l'admin"
        )
        
        return self.send_message(chat_id, msg)
    
    def handle_license_input(self, chat_id: int, user_id: str, license_text: str) -> bool:
        """Traite la saisie de licence"""
        # Retirer l'utilisateur de la liste d'attente
        self.waiting_for_license.pop(user_id, None)
        
        # Valider la licence
        if self.user_manager.validate_license(user_id, license_text):
            user_info = self.user_manager.get_user_info(user_id)
            
            # Message de succès
            success_msg = (
                "🎉 **Licence validée avec succès !**\n\n"
                "✅ Votre compte est maintenant entièrement actif.\n"
                f"💎 **Plan :** {user_info['plan']}\n"
                f"🔄 **Redirections :** {user_info['max_redirections']}\n"
                f"📅 **Expire le :** {datetime.fromisoformat(user_info['expires']).strftime('%d/%m/%Y')}\n\n"
                "🚀 **Utilisez /redirections pour configurer vos redirections**"
            )
            
            return self.send_message(chat_id, success_msg)
        else:
            return self.send_message(chat_id, self.user_manager.messages["license_invalid"])
    
    def handle_redirections_menu(self, chat_id: int, user_id: str) -> bool:
        """Menu de gestion des redirections"""
        if not self.user_manager.check_user_access(user_id):
            return self.send_message(chat_id, self.user_manager.messages["access_expired"])
        
        user_info = self.user_manager.get_user_info(user_id)
        current = user_info.get('current_redirections', 0)
        max_allowed = user_info.get('max_redirections', 0)
        
        keyboard = self.create_inline_keyboard([
            [{"text": "➕ Ajouter une redirection", "callback_data": f"add_redirect_{user_id}"}],
            [{"text": "📋 Voir mes redirections", "callback_data": f"list_redirects_{user_id}"}],
            [{"text": "❌ Supprimer une redirection", "callback_data": f"remove_redirect_{user_id}"}],
            [{"text": "🔙 Retour", "callback_data": "back_main"}]
        ])
        
        msg = (
            f"🔄 **Gestion des redirections**\n\n"
            f"📊 **Utilisation :** {current}/{max_allowed}\n"
            f"📱 **Plan :** {user_info['plan']}\n\n"
            f"💡 **Fonctionnalités :**\n"
            f"• Messages redirigés apparaissent comme venant du canal de destination\n"
            f"• Redirection en temps réel\n"
            f"• Gestion des éditions de messages\n"
            f"• Filtres et transformations avancées"
        )
        
        return self.send_message(chat_id, msg, reply_markup=keyboard)
    
    def handle_approve_trial(self, chat_id: int, command: str) -> bool:
        """Approuve un essai gratuit (admin seulement)"""
        try:
            parts = command.split()
            if len(parts) != 2:
                return self.send_message(chat_id, "❌ Format: /approuver_essai USER_ID")
            
            target_user_id = parts[1]
            success, expires = self.user_manager.approve_trial(target_user_id)
            
            if success:
                # Notifier l'admin
                admin_msg = f"✅ Essai gratuit approuvé pour l'utilisateur {target_user_id}"
                self.send_message(chat_id, admin_msg)
                
                # Notifier l'utilisateur
                user_msg = self.user_manager.messages["trial_activated"].format(expires=expires)
                self.send_message(int(target_user_id), user_msg)
                
                return True
            else:
                return self.send_message(chat_id, f"❌ Impossible d'approuver l'essai: {expires}")
                
        except Exception as e:
            logger.error(f"Erreur approbation essai: {e}")
            return self.send_message(chat_id, f"❌ Erreur: {str(e)}")
    
    def handle_approve_payment(self, chat_id: int, command: str) -> bool:
        """Approuve un paiement (admin seulement)"""
        try:
            parts = command.split()
            if len(parts) != 3:
                return self.send_message(chat_id, "❌ Format: /approuver_paiement USER_ID PLAN")
            
            target_user_id = parts[1]
            plan = parts[2]
            
            success, license_key = self.user_manager.approve_payment(target_user_id, plan)
            
            if success:
                # Notifier l'admin
                admin_msg = (
                    f"✅ Paiement approuvé pour l'utilisateur {target_user_id}\n"
                    f"📦 Plan: {plan}\n"
                    f"🔐 Licence: `{license_key}`"
                )
                self.send_message(chat_id, admin_msg)
                
                # Notifier l'utilisateur
                user_msg = self.user_manager.messages["license_validation"]
                self.send_message(int(target_user_id), user_msg)
                
                return True
            else:
                return self.send_message(chat_id, f"❌ Impossible d'approuver le paiement: {license_key}")
                
        except Exception as e:
            logger.error(f"Erreur approbation paiement: {e}")
            return self.send_message(chat_id, f"❌ Erreur: {str(e)}")
    
    def handle_admin_panel(self, chat_id: int) -> bool:
        """Panneau d'administration"""
        stats = self.user_manager.get_stats()
        pending_approvals = self.user_manager.get_pending_approvals()
        pending_payments = self.user_manager.get_pending_payments()
        
        msg = (
            f"🛡️ **Panneau d'administration**\n\n"
            f"📊 **Statistiques :**\n"
            f"• Total utilisateurs: {stats['total_users']}\n"
            f"• En attente d'approbation: {stats['pending_approval']}\n"
            f"• Essais actifs: {stats['trial_users']}\n"
            f"• Abonnés actifs: {stats['active_users']}\n"
            f"• Expirés: {stats['expired_users']}\n"
            f"• Demandes de paiement: {stats['payment_requests']}\n\n"
        )
        
        if pending_approvals:
            msg += "⏳ **Approbations en attente :**\n"
            for user_id, data in pending_approvals.items():
                username = data.get('username', f'User{user_id}')
                msg += f"• @{username} ({user_id}) - `/approuver_essai {user_id}`\n"
            msg += "\n"
        
        if pending_payments:
            msg += "💳 **Paiements en attente :**\n"
            for user_id, requests in pending_payments.items():
                for request in requests:
                    msg += f"• User {user_id} - {request['plan']} - `/approuver_paiement {user_id} {request['plan']}`\n"
        
        return self.send_message(chat_id, msg)
    
    def handle_status(self, chat_id: int, user_id: str) -> bool:
        """Affiche le statut de l'utilisateur"""
        user_info = self.user_manager.get_user_info(user_id)
        
        if not user_info:
            return self.send_message(chat_id, "❌ Utilisateur non enregistré. Utilisez /start pour commencer.")
        
        status = self.user_manager.get_user_status(user_id)
        
        if status == "actif":
            expires = datetime.fromisoformat(user_info['expires']).strftime('%d/%m/%Y à %H:%M')
            msg = (
                f"✅ **Statut :** Actif\n"
                f"📦 **Plan :** {user_info['plan']}\n"
                f"📅 **Expire le :** {expires}\n"
                f"🔄 **Redirections :** {user_info.get('current_redirections', 0)}/{user_info.get('max_redirections', 0)}\n"
                f"🔐 **Licence validée :** {'✅' if user_info.get('license_validated') else '❌'}"
            )
        elif status == "essai_actif":
            expires = datetime.fromisoformat(user_info['expires']).strftime('%d/%m/%Y à %H:%M')
            msg = (
                f"🔄 **Statut :** Essai gratuit\n"
                f"📅 **Expire le :** {expires}\n"
                f"🔄 **Redirections :** {user_info.get('current_redirections', 0)}/{user_info.get('max_redirections', 0)}\n\n"
                f"💡 Utilisez `/payer` pour souscrire un abonnement"
            )
        elif status == "en_attente":
            msg = "⏳ **Statut :** En attente d'approbation par l'administrateur"
        elif status == "paiement_approuvé":
            msg = (
                f"💳 **Statut :** Paiement approuvé\n"
                f"🔐 **Action requise :** Utilisez `/valider_licence` pour activer votre compte"
            )
        else:
            msg = f"❌ **Statut :** {status}\n\nContactez l'administrateur pour plus d'informations."
        
        return self.send_message(chat_id, msg)
    
    def handle_help(self, chat_id: int, user_id: str) -> bool:
        """Affiche l'aide"""
        help_msg = (
            "📋 **Aide TeleFoot Bot**\n\n"
            "🤖 **Commandes disponibles :**\n"
            "• `/start` - Commencer / Réinitialiser\n"
            "• `/status` - Voir votre statut\n"
            "• `/pronostics` - Pronostics du jour\n"
            "• `/redirections` - Gérer les redirections\n"
            "• `/payer` - Souscrire un abonnement\n"
            "• `/valider_licence` - Valider votre licence\n"
            "• `/help` - Cette aide\n\n"
            "💰 **Tarifs :**\n"
            "• Essai gratuit : 24h (1 redirection)\n"
            "• 1 semaine : 1000f (10 redirections)\n"
            "• 1 mois : 3000f (50 redirections)\n\n"
            "🔄 **Fonctionnalités :**\n"
            "• Messages apparaissent comme venant du canal de destination\n"
            "• Redirection en temps réel\n"
            "• Licences personnelles sécurisées\n"
            "• Pronostics football premium\n\n"
            "📞 **Contact :** Sossou Kouamé"
        )
        
        return self.send_message(chat_id, help_msg)
    
    def handle_pronostics(self, chat_id: int, user_id: str) -> bool:
        """Affiche les pronostics"""
        if not self.user_manager.check_user_access(user_id):
            return self.send_message(chat_id, self.user_manager.messages["access_expired"])
        
        today = datetime.now().strftime("%d/%m/%Y")
        pronostics_msg = (
            f"⚽ **Pronostics Premium du {today}**\n\n"
            f"🏆 **Matchs VIP :**\n"
            f"• **Real Madrid vs Barcelona** - 1X (Cote: 1.85) 🔥\n"
            f"• **Manchester City vs Liverpool** - Over 2.5 (Cote: 1.75) ⚡\n"
            f"• **PSG vs Marseille** - 1 (Cote: 1.65) 💎\n"
            f"• **Bayern vs Dortmund** - BTTS (Cote: 1.90) 🎯\n\n"
            f"📈 **Analyse experte :**\n"
            f"• Confiance très élevée sur les 4 matchs\n"
            f"• Bankroll recommandé : 3-5% par pari\n"
            f"• Stratégie : Combiné ou simple selon profil\n\n"
            f"🎯 **Prédiction du jour :** 92% de réussite\n"
            f"💰 **Potentiel gain :** +180% sur mise totale\n"
            f"🔥 **Bonus :** Match surprise à 19h30 (cote @2.10)"
        )
        
        return self.send_message(chat_id, pronostics_msg)
    
    def process_callback_query(self, callback_query: Dict) -> bool:
        """Traite les callbacks des boutons inline"""
        try:
            chat_id = callback_query['message']['chat']['id']
            user_id = str(callback_query['from']['id'])
            data = callback_query['data']
            
            if data.startswith('pay_'):
                parts = data.split('_')
                plan = parts[1]
                target_user_id = parts[2]
                
                if target_user_id == user_id:
                    success, price = self.user_manager.request_payment(user_id, plan)
                    
                    if success:
                        # Notifier l'admin
                        admin_msg = (
                            f"💳 **Nouvelle demande de paiement**\n\n"
                            f"👤 **Utilisateur :** {user_id}\n"
                            f"📦 **Plan :** {plan}\n"
                            f"💰 **Prix :** {price}\n"
                            f"🕐 **Date :** {datetime.now().strftime('%d/%m/%Y à %H:%M')}\n\n"
                            f"**Action :** `/approuver_paiement {user_id} {plan}`"
                        )
                        self.send_message(ADMIN_ID, admin_msg)
                        
                        # Confirmer à l'utilisateur
                        user_msg = self.user_manager.messages["payment_request"].format(
                            plan=plan, price=price
                        )
                        return self.send_message(chat_id, user_msg)
                    else:
                        return self.send_message(chat_id, f"❌ Erreur: {price}")
            
            elif data == 'cancel_payment':
                return self.send_message(chat_id, "❌ Demande de paiement annulée.")
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur callback query: {e}")
            return False

# Initialisation du bot
advanced_bot = AdvancedTelefootBot(user_manager)

# Routes Flask
@app.route('/')
def index():
    """Page d'accueil"""
    return jsonify({
        "status": "ok",
        "message": "TeleFoot Bot Advanced - PythonAnywhere",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0",
        "features": ["approval_system", "personal_licenses", "multi_channel_redirection"]
    })

@app.route('/health')
def health_check():
    """Contrôle de santé"""
    stats = user_manager.get_stats()
    return jsonify({
        "status": "healthy",
        "stats": stats,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/admin/stats')
def admin_stats():
    """Statistiques admin détaillées"""
    stats = user_manager.get_stats()
    pending_approvals = user_manager.get_pending_approvals()
    pending_payments = user_manager.get_pending_payments()
    
    return jsonify({
        "stats": stats,
        "pending_approvals": list(pending_approvals.keys()),
        "pending_payments": {k: len(v) for k, v in pending_payments.items()},
        "secret_token": SECRET_TOKEN,
        "timestamp": datetime.now().isoformat()
    })

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
            advanced_bot.process_message(message)
            return jsonify({"status": "ok"})
        
        # Traiter les callback queries
        elif 'callback_query' in update:
            callback_query = update['callback_query']
            advanced_bot.process_callback_query(callback_query)
            return jsonify({"status": "ok"})
        
        return jsonify({"status": "ok"})
        
    except Exception as e:
        logger.error(f"Erreur webhook: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print(f"🔐 Secret Token: {SECRET_TOKEN}")
    print(f"📡 Webhook URL: https://votreusername.pythonanywhere.com/{SECRET_TOKEN}")
    print("🚀 Bot TeleFoot Advanced v2.0 démarré")
    app.run(debug=True, host='0.0.0.0', port=5000)