#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TeleFoot Bot avec redirection authentique - Messages apparaissent vraiment du canal de destination
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
from authentic_redirection_system import get_authentic_redirection_system

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
SECRET_TOKEN = os.getenv('WEBHOOK_SECRET', secrets.token_urlsafe(32))
BOT_TOKEN = os.getenv('BOT_TOKEN', '7573497633:AAHk9K15yTCiJP-zruJrc9v8eK8I9XhjyH4')
ADMIN_ID = int(os.getenv('ADMIN_ID', '1190237801'))
API_ID = int(os.getenv('API_ID', '29177661'))
API_HASH = os.getenv('API_HASH', 'a8639172fa8d35dbfd8ea46286d349ab')

# Initialisation
app = Flask(__name__)
user_manager = AdvancedUserManager()
redirection_system = get_authentic_redirection_system(user_manager)

class TelefootAuthenticBot:
    """Bot avec système de redirection authentique"""
    
    def __init__(self, user_manager: AdvancedUserManager, redirection_system):
        self.user_manager = user_manager
        self.redirection_system = redirection_system
        self.waiting_for_license = {}
        self.waiting_for_phone = {}
        self.waiting_for_code = {}
        self.pending_redirections = {}
        
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
    
    def create_inline_keyboard(self, buttons: List[List[Dict]]) -> Dict:
        """Crée un clavier inline"""
        return {"inline_keyboard": buttons}
    
    def process_message(self, message: Dict) -> bool:
        """Traite un message reçu"""
        try:
            chat_id = message['chat']['id']
            user_id = str(message['from']['id'])
            text = message.get('text', '')
            
            # Vérifier les états d'attente
            if user_id in self.waiting_for_license:
                return self.handle_license_input(chat_id, user_id, text)
            elif user_id in self.waiting_for_phone:
                return asyncio.run(self.handle_phone_input(chat_id, user_id, text))
            elif user_id in self.waiting_for_code:
                return asyncio.run(self.handle_code_input(chat_id, user_id, text))
            
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
            elif text == '/connect_admin':
                return self.handle_connect_admin_request(chat_id, user_id)
            elif text == '/redirections':
                return asyncio.run(self.handle_redirections_menu(chat_id, user_id))
            elif text == '/test_redirection':
                return asyncio.run(self.handle_test_redirection(chat_id, user_id))
            elif text.startswith('/approuver_essai') and int(message['from']['id']) == ADMIN_ID:
                return self.handle_approve_trial(chat_id, text)
            elif text.startswith('/approuver_paiement') and int(message['from']['id']) == ADMIN_ID:
                return self.handle_approve_payment(chat_id, text)
            elif text.startswith('/admin') and int(message['from']['id']) == ADMIN_ID:
                return asyncio.run(self.handle_admin_panel(chat_id))
            else:
                return self.send_message(chat_id, "❓ Commande non reconnue. Utilisez /help pour voir les commandes disponibles.")
                
        except Exception as e:
            logger.error(f"Erreur traitement message: {e}")
            return False
    
    def handle_start(self, chat_id: int, user_id: str, user_info: Dict) -> bool:
        """Traite /start avec système d'approbation"""
        username = user_info.get('username', f"User{user_id}")
        
        existing_user = self.user_manager.get_user_info(user_id)
        
        if not existing_user:
            # Nouvel utilisateur
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
            return self.send_message(chat_id, self.user_manager.messages["welcome_pending"])
        
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
            f"🤖 **TeleFoot Bot - Redirection Authentique !**\n\n"
            f"✅ {plan_info}\n"
            f"🔄 **Redirections :** {current_redirections}/{max_redirections}\n\n"
            f"🎯 **Nouvelles fonctionnalités :**\n"
            f"• Messages apparaissent vraiment du canal de destination\n"
            f"• Plus de mention 'MO' ou autres signatures\n"
            f"• Redirection 100% authentique\n\n"
            f"📱 **Commandes :**\n"
            f"• `/connect_admin` - Connecter vos canaux admin\n"
            f"• `/redirections` - Gérer les redirections\n"
            f"• `/test_redirection` - Tester le système\n"
            f"• `/pronostics` - Pronostics premium\n"
            f"• `/payer` - Souscrire un abonnement\n\n"
            f"📞 **Contact :** Sossou Kouamé"
        )
        
        return self.send_message(chat_id, welcome_msg)
    
    def handle_connect_admin_request(self, chat_id: int, user_id: str) -> bool:
        """Demande de connexion avec droits admin"""
        if not self.user_manager.check_user_access(user_id):
            return self.send_message(chat_id, self.user_manager.messages["access_expired"])
        
        self.waiting_for_phone[user_id] = True
        
        msg = (
            "📱 **Connexion avec droits administrateur**\n\n"
            "Pour que les messages apparaissent vraiment comme venant de vos canaux, "
            "vous devez vous connecter avec un compte qui a les droits administrateur "
            "sur ces canaux.\n\n"
            "⚠️ **Important :** Vous devez être admin des canaux pour la redirection authentique.\n\n"
            "📝 **Envoyez maintenant votre numéro de téléphone** (format international) :\n"
            "Exemple : +33612345678"
        )
        
        return self.send_message(chat_id, msg)
    
    async def handle_phone_input(self, chat_id: int, user_id: str, phone: str) -> bool:
        """Traite la saisie du numéro de téléphone"""
        self.waiting_for_phone.pop(user_id, None)
        
        try:
            success, message = await self.redirection_system.connect_channel_admin(
                user_id, phone, API_ID, API_HASH
            )
            
            if success:
                return self.send_message(chat_id, f"✅ {message}")
            else:
                if "Code de vérification envoyé" in message:
                    self.waiting_for_code[user_id] = phone
                    msg = (
                        f"📱 **Code de vérification envoyé**\n\n"
                        f"Un code a été envoyé au numéro {phone}\n"
                        f"📝 **Envoyez maintenant le code reçu**"
                    )
                    return self.send_message(chat_id, msg)
                else:
                    return self.send_message(chat_id, f"❌ {message}")
        
        except Exception as e:
            logger.error(f"Erreur connexion admin {user_id}: {e}")
            return self.send_message(chat_id, f"❌ Erreur: {str(e)}")
    
    async def handle_code_input(self, chat_id: int, user_id: str, code: str) -> bool:
        """Traite la saisie du code de vérification"""
        phone = self.waiting_for_code.pop(user_id, None)
        
        if not phone:
            return self.send_message(chat_id, "❌ Aucune demande de code en cours.")
        
        try:
            success, message = await self.redirection_system.verify_code(user_id, phone, code)
            
            if success:
                admin_channels = await self.redirection_system.get_user_admin_channels(user_id)
                
                msg = (
                    f"✅ **Connexion réussie !**\n\n"
                    f"🛡️ **Canaux avec droits admin :** {len(admin_channels)}\n\n"
                )
                
                if admin_channels:
                    msg += "📋 **Vos canaux administrateur :**\n"
                    for channel in admin_channels[:5]:  # Limiter à 5 pour l'affichage
                        msg += f"• {channel['title']} (ID: {channel['id']})\n"
                    
                    if len(admin_channels) > 5:
                        msg += f"• ... et {len(admin_channels) - 5} autres\n"
                    
                    msg += "\n🚀 **Utilisez /redirections pour configurer vos redirections authentiques**"
                else:
                    msg += "⚠️ **Aucun canal avec droits admin trouvé**\n\nVous devez être administrateur des canaux pour la redirection authentique."
                
                return self.send_message(chat_id, msg)
            else:
                return self.send_message(chat_id, f"❌ {message}")
        
        except Exception as e:
            logger.error(f"Erreur vérification code {user_id}: {e}")
            return self.send_message(chat_id, f"❌ Erreur: {str(e)}")
    
    async def handle_redirections_menu(self, chat_id: int, user_id: str) -> bool:
        """Menu de gestion des redirections authentiques"""
        if not self.user_manager.check_user_access(user_id):
            return self.send_message(chat_id, self.user_manager.messages["access_expired"])
        
        user_info = self.user_manager.get_user_info(user_id)
        admin_channels = await self.redirection_system.get_user_admin_channels(user_id)
        
        if not admin_channels:
            msg = (
                "⚠️ **Aucun canal administrateur connecté**\n\n"
                "Pour utiliser la redirection authentique, vous devez :\n"
                "1. Utiliser `/connect_admin` pour vous connecter\n"
                "2. Être administrateur des canaux que vous voulez utiliser\n\n"
                "💡 **Avantage :** Les messages apparaîtront vraiment comme venant de vos canaux !"
            )
            return self.send_message(chat_id, msg)
        
        current = user_info.get('current_redirections', 0)
        max_allowed = user_info.get('max_redirections', 0)
        
        keyboard = self.create_inline_keyboard([
            [{"text": "➕ Ajouter redirection authentique", "callback_data": f"add_auth_redirect_{user_id}"}],
            [{"text": "📋 Voir mes redirections", "callback_data": f"list_auth_redirects_{user_id}"}],
            [{"text": "🧪 Tester une redirection", "callback_data": f"test_auth_redirect_{user_id}"}],
            [{"text": "❌ Supprimer redirection", "callback_data": f"remove_auth_redirect_{user_id}"}],
            [{"text": "🔙 Retour", "callback_data": "back_main"}]
        ])
        
        msg = (
            f"🔄 **Redirection Authentique**\n\n"
            f"📊 **Utilisation :** {current}/{max_allowed}\n"
            f"🛡️ **Canaux admin :** {len(admin_channels)}\n"
            f"📱 **Plan :** {user_info['plan']}\n\n"
            f"✨ **Avantages authentiques :**\n"
            f"• Messages apparaissent du canal de destination\n"
            f"• Aucune signature 'MO' ou autre\n"
            f"• Redirection invisible aux utilisateurs\n"
            f"• Support édition en temps réel\n\n"
            f"🎯 **Prêt pour redirection professionnelle !**"
        )
        
        return self.send_message(chat_id, msg, reply_markup=keyboard)
    
    async def handle_test_redirection(self, chat_id: int, user_id: str) -> bool:
        """Teste le système de redirection authentique"""
        if not self.user_manager.check_user_access(user_id):
            return self.send_message(chat_id, self.user_manager.messages["access_expired"])
        
        admin_channels = await self.redirection_system.get_user_admin_channels(user_id)
        
        if not admin_channels:
            return self.send_message(chat_id, "❌ Aucun canal admin connecté. Utilisez /connect_admin d'abord.")
        
        # Tester sur le premier canal admin
        test_channel = admin_channels[0]
        test_message = f"Message de test envoyé le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
        
        success, result = await self.redirection_system.test_authentic_message(
            user_id, test_channel['id'], test_message
        )
        
        if success:
            msg = (
                f"✅ **Test réussi !**\n\n"
                f"📡 **Canal testé :** {test_channel['title']}\n"
                f"📝 **Résultat :** {result}\n\n"
                f"🎯 **Le message est apparu comme venant du canal {test_channel['title']} directement !**\n\n"
                f"Votre système de redirection authentique fonctionne parfaitement."
            )
        else:
            msg = f"❌ **Échec du test**\n\n{result}"
        
        return self.send_message(chat_id, msg)
    
    def handle_payment_request(self, chat_id: int, user_id: str) -> bool:
        """Traite les demandes de paiement"""
        if not self.user_manager.get_user_info(user_id):
            return self.send_message(chat_id, "❌ Utilisez /start pour commencer.")
        
        keyboard = self.create_inline_keyboard([
            [{"text": "1 Semaine - 1000f (10 redirections)", "callback_data": f"pay_semaine_{user_id}"}],
            [{"text": "1 Mois - 3000f (50 redirections)", "callback_data": f"pay_mois_{user_id}"}],
            [{"text": "❌ Annuler", "callback_data": "cancel_payment"}]
        ])
        
        msg = (
            "💳 **Abonnement Redirection Authentique**\n\n"
            "🎯 **Nouveau : Messages 100% authentiques !**\n"
            "Fini les signatures 'MO' - vos messages apparaîtront "
            "vraiment comme venant de vos canaux de destination.\n\n"
            "📦 **Plans disponibles :**\n"
            "• **1 Semaine** - 1000f (10 redirections authentiques)\n"
            "• **1 Mois** - 3000f (50 redirections authentiques)\n\n"
            "⚡ **Fonctionnalités premium :**\n"
            "• Redirection invisible aux utilisateurs\n"
            "• Messages du canal de destination\n"
            "• Support édition temps réel\n"
            "• Pronostics premium illimités\n"
            "• Licence personnelle sécurisée\n"
            "• Support prioritaire"
        )
        
        return self.send_message(chat_id, msg, reply_markup=keyboard)
    
    def handle_license_validation_request(self, chat_id: int, user_id: str) -> bool:
        """Demande de validation de licence"""
        user_info = self.user_manager.get_user_info(user_id)
        
        if not user_info:
            return self.send_message(chat_id, "❌ Utilisez /start pour commencer.")
        
        if user_info["status"] != "payment_approved":
            return self.send_message(chat_id, "❌ Aucune licence en attente de validation.")
        
        self.waiting_for_license[user_id] = True
        
        msg = (
            "🔐 **Validation de licence personnelle**\n\n"
            "Envoyez maintenant votre clé de licence unique.\n"
            "⚠️ **Attention :** Cette licence est strictement personnelle et sécurisée.\n\n"
            "📝 **Format attendu :** XXXX-XXXX-XXXX-XXXX\n"
            "💡 **Astuce :** Copiez-collez la clé envoyée par l'administrateur\n\n"
            "🎯 **Une fois validée, vous aurez accès à la redirection authentique !**"
        )
        
        return self.send_message(chat_id, msg)
    
    def handle_license_input(self, chat_id: int, user_id: str, license_text: str) -> bool:
        """Traite la saisie de licence"""
        self.waiting_for_license.pop(user_id, None)
        
        if self.user_manager.validate_license(user_id, license_text):
            user_info = self.user_manager.get_user_info(user_id)
            
            success_msg = (
                "🎉 **Licence validée avec succès !**\n\n"
                "✅ Votre compte premium est maintenant actif.\n"
                f"💎 **Plan :** {user_info['plan']}\n"
                f"🔄 **Redirections authentiques :** {user_info['max_redirections']}\n"
                f"📅 **Expire le :** {datetime.fromisoformat(user_info['expires']).strftime('%d/%m/%Y')}\n\n"
                "🚀 **Prochaines étapes :**\n"
                "1. `/connect_admin` - Connecter vos canaux admin\n"
                "2. `/redirections` - Configurer vos redirections\n"
                "3. `/test_redirection` - Tester le système\n\n"
                "🎯 **Vos messages apparaîtront désormais comme venant de vos canaux !**"
            )
            
            return self.send_message(chat_id, success_msg)
        else:
            return self.send_message(chat_id, self.user_manager.messages["license_invalid"])
    
    def handle_approve_trial(self, chat_id: int, command: str) -> bool:
        """Approuve un essai gratuit (admin seulement)"""
        try:
            parts = command.split()
            if len(parts) != 2:
                return self.send_message(chat_id, "❌ Format: /approuver_essai USER_ID")
            
            target_user_id = parts[1]
            success, expires = self.user_manager.approve_trial(target_user_id)
            
            if success:
                admin_msg = f"✅ Essai gratuit approuvé pour l'utilisateur {target_user_id}"
                self.send_message(chat_id, admin_msg)
                
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
                admin_msg = (
                    f"✅ Paiement approuvé pour l'utilisateur {target_user_id}\n"
                    f"📦 Plan: {plan}\n"
                    f"🔐 Licence: `{license_key}`\n\n"
                    f"L'utilisateur peut maintenant utiliser /valider_licence"
                )
                self.send_message(chat_id, admin_msg)
                
                user_msg = (
                    "💳 **Paiement confirmé !**\n\n"
                    "Votre abonnement a été validé par l'administrateur.\n"
                    "🔐 **Utilisez maintenant /valider_licence pour activer votre compte**\n\n"
                    "🎯 **Bientôt : Redirection authentique à votre disposition !**"
                )
                self.send_message(int(target_user_id), user_msg)
                
                return True
            else:
                return self.send_message(chat_id, f"❌ Impossible d'approuver le paiement: {license_key}")
                
        except Exception as e:
            logger.error(f"Erreur approbation paiement: {e}")
            return self.send_message(chat_id, f"❌ Erreur: {str(e)}")
    
    async def handle_admin_panel(self, chat_id: int) -> bool:
        """Panneau d'administration"""
        stats = self.user_manager.get_stats()
        redirection_stats = await self.redirection_system.get_redirection_stats()
        pending_approvals = self.user_manager.get_pending_approvals()
        pending_payments = self.user_manager.get_pending_payments()
        
        msg = (
            f"🛡️ **Panneau d'administration TeleFoot v2.0**\n\n"
            f"📊 **Statistiques utilisateurs :**\n"
            f"• Total utilisateurs: {stats['total_users']}\n"
            f"• En attente d'approbation: {stats['pending_approval']}\n"
            f"• Essais actifs: {stats['trial_users']}\n"
            f"• Abonnés actifs: {stats['active_users']}\n"
            f"• Expirés: {stats['expired_users']}\n"
            f"• Demandes de paiement: {stats['payment_requests']}\n\n"
            f"🔄 **Statistiques redirections authentiques :**\n"
            f"• Utilisateurs connectés: {redirection_stats['active_users']}\n"
            f"• Canaux admin: {redirection_stats['admin_channels']}\n"
            f"• Redirections actives: {redirection_stats['total_redirections']}\n\n"
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
                f"✅ **Statut :** Actif Premium\n"
                f"📦 **Plan :** {user_info['plan']}\n"
                f"📅 **Expire le :** {expires}\n"
                f"🔄 **Redirections :** {user_info.get('current_redirections', 0)}/{user_info.get('max_redirections', 0)}\n"
                f"🛡️ **Redirection authentique :** {'✅ Activée' if user_id in redirection_system.active_clients else '❌ Non connectée'}\n"
                f"🔐 **Licence validée :** {'✅' if user_info.get('license_validated') else '❌'}"
            )
        elif status == "essai_actif":
            expires = datetime.fromisoformat(user_info['expires']).strftime('%d/%m/%Y à %H:%M')
            msg = (
                f"🔄 **Statut :** Essai gratuit\n"
                f"📅 **Expire le :** {expires}\n"
                f"🔄 **Redirections :** {user_info.get('current_redirections', 0)}/{user_info.get('max_redirections', 0)}\n"
                f"🛡️ **Redirection authentique :** {'✅ Activée' if user_id in redirection_system.active_clients else '❌ Non connectée'}\n\n"
                f"💡 Utilisez `/payer` pour souscrire un abonnement premium"
            )
        elif status == "en_attente":
            msg = "⏳ **Statut :** En attente d'approbation par l'administrateur"
        elif status == "paiement_approuvé":
            msg = (
                f"💳 **Statut :** Paiement approuvé\n"
                f"🔐 **Action requise :** Utilisez `/valider_licence` pour activer votre compte premium"
            )
        else:
            msg = f"❌ **Statut :** {status}\n\nContactez l'administrateur pour plus d'informations."
        
        return self.send_message(chat_id, msg)
    
    def handle_help(self, chat_id: int, user_id: str) -> bool:
        """Affiche l'aide"""
        help_msg = (
            "📋 **TeleFoot Bot - Redirection Authentique**\n\n"
            "🎯 **Nouveau :** Messages apparaissent vraiment de vos canaux !\n\n"
            "🤖 **Commandes principales :**\n"
            "• `/start` - Commencer / Réinitialiser\n"
            "• `/status` - Voir votre statut complet\n"
            "• `/connect_admin` - Connecter vos canaux admin\n"
            "• `/redirections` - Gérer redirections authentiques\n"
            "• `/test_redirection` - Tester le système\n"
            "• `/pronostics` - Pronostics premium\n"
            "• `/payer` - Souscrire abonnement\n"
            "• `/valider_licence` - Activer votre licence\n\n"
            "💰 **Tarifs :**\n"
            "• Essai gratuit : 24h (1 redirection)\n"
            "• 1 semaine : 1000f (10 redirections)\n"
            "• 1 mois : 3000f (50 redirections)\n\n"
            "🔄 **Redirection authentique :**\n"
            "• Messages du canal de destination\n"
            "• Aucune signature visible\n"
            "• Édition temps réel\n"
            "• Redirection invisible\n\n"
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
            f"🏆 **Sélection VIP :**\n"
            f"• **Real Madrid vs Barcelona** - 1X (Cote: 1.85) 🔥\n"
            f"• **Manchester City vs Liverpool** - Over 2.5 (Cote: 1.75) ⚡\n"
            f"• **PSG vs Marseille** - 1 (Cote: 1.65) 💎\n"
            f"• **Bayern vs Dortmund** - BTTS (Cote: 1.90) 🎯\n"
            f"• **Arsenal vs Chelsea** - Under 3.5 (Cote: 1.80) 🛡️\n\n"
            f"📈 **Analyse experte :**\n"
            f"• Confiance très élevée sur les 5 matchs\n"
            f"• Stratégie recommandée : Simple + Combiné\n"
            f"• Gestion bankroll : 3-5% par pari\n\n"
            f"🎯 **Prédiction du jour :** 94% de réussite\n"
            f"💰 **Potentiel gain :** +220% sur mise totale\n"
            f"🔥 **Match surprise :** Disponible à 19h30 (cote @2.25)\n\n"
            f"📊 **Statistiques du mois :** 89% de réussite"
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
                            f"💳 **Nouvelle demande d'abonnement**\n\n"
                            f"👤 **Utilisateur :** {user_id}\n"
                            f"📦 **Plan :** {plan} (redirection authentique)\n"
                            f"💰 **Prix :** {price}\n"
                            f"🕐 **Date :** {datetime.now().strftime('%d/%m/%Y à %H:%M')}\n\n"
                            f"**Action :** `/approuver_paiement {user_id} {plan}`"
                        )
                        self.send_message(ADMIN_ID, admin_msg)
                        
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
authentic_bot = TelefootAuthenticBot(user_manager, redirection_system)

# Routes Flask
@app.route('/')
def index():
    """Page d'accueil"""
    return jsonify({
        "status": "ok",
        "message": "TeleFoot Bot v2.0 - Redirection Authentique",
        "timestamp": datetime.now().isoformat(),
        "version": "2.0",
        "features": ["authentic_redirection", "personal_licenses", "admin_approval"]
    })

@app.route('/health')
def health_check():
    """Contrôle de santé"""
    stats = user_manager.get_stats()
    return jsonify({
        "status": "healthy",
        "user_stats": stats,
        "timestamp": datetime.now().isoformat()
    })

@app.route('/admin/stats')
def admin_stats():
    """Statistiques admin détaillées"""
    user_stats = user_manager.get_stats()
    
    return jsonify({
        "user_stats": user_stats,
        "pending_approvals": list(user_manager.get_pending_approvals().keys()),
        "pending_payments": {k: len(v) for k, v in user_manager.get_pending_payments().items()},
        "authentic_redirection": True,
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
        
        if 'message' in update:
            message = update['message']
            authentic_bot.process_message(message)
            return jsonify({"status": "ok"})
        
        elif 'callback_query' in update:
            callback_query = update['callback_query']
            authentic_bot.process_callback_query(callback_query)
            return jsonify({"status": "ok"})
        
        return jsonify({"status": "ok"})
        
    except Exception as e:
        logger.error(f"Erreur webhook: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print(f"🔐 Secret Token: {SECRET_TOKEN}")
    print(f"📡 Webhook URL: https://votreusername.pythonanywhere.com/{SECRET_TOKEN}")
    print("🚀 TeleFoot Bot v2.0 - Redirection Authentique démarré")
    app.run(debug=True, host='0.0.0.0', port=5000)