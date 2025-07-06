from telethon import events
from user_manager import UserManager
from config import ADMIN_ID, MESSAGES

class BotHandlers:
    """Gestionnaire des commandes et événements du bot"""
    
    def __init__(self, bot, user_manager: UserManager):
        self.bot = bot
        self.user_manager = user_manager
        self.register_handlers()
    
    def register_handlers(self):
        """Enregistre tous les handlers du bot"""
        self.bot.add_event_handler(self.start_handler, events.NewMessage(pattern='/start'))
        self.bot.add_event_handler(self.activer_handler, events.NewMessage(pattern='/activer'))
        self.bot.add_event_handler(self.status_handler, events.NewMessage(pattern='/status'))
        self.bot.add_event_handler(self.help_handler, events.NewMessage(pattern='/help'))
        self.bot.add_event_handler(self.pronostics_handler, events.NewMessage(pattern='/pronostics'))
        
        # Commandes admin spécialisées
        self.bot.add_event_handler(self.test_handler, events.NewMessage(pattern='/test'))
        self.bot.add_event_handler(self.guide_handler, events.NewMessage(pattern='/guide'))
        self.bot.add_event_handler(self.clean_handler, events.NewMessage(pattern='/clean'))
        self.bot.add_event_handler(self.reconnect_handler, events.NewMessage(pattern='/reconnect'))
        self.bot.add_event_handler(self.config_handler, events.NewMessage(pattern='/config'))
        self.bot.add_event_handler(self.delay_handler, events.NewMessage(pattern='/delay'))
        self.bot.add_event_handler(self.settings_handler, events.NewMessage(pattern='/settings'))
        self.bot.add_event_handler(self.menu_handler, events.NewMessage(pattern='/menu'))
    
    async def start_handler(self, event):
        """Handler pour la commande /start"""
        user_id = str(event.sender_id)
        
        # Enregistrement automatique du nouvel utilisateur
        if user_id not in self.user_manager.users:
            self.user_manager.register_new_user(user_id)
        
        # Vérification de l'accès
        if not self.user_manager.check_user_access(user_id):
            await event.reply(
                MESSAGES["access_expired"],
                parse_mode="markdown"
            )
            return
        
        # Utilisateur actif - Message d'accueil
        await event.reply(
            "🤖 **TeleFoot Bot - Bienvenue !**\n\n"
            "✅ Votre licence est active\n\n"
            "📱 **Commandes principales :**\n"
            "• `/menu` - Interface à boutons TeleFeed\n"
            "• `/pronostics` - Pronostics du jour\n"
            "• `/status` - Votre statut\n"
            "• `/help` - Aide complète\n\n"
            "💰 **Tarifs :**\n"
            "• 1 semaine = 1000f\n"
            "• 1 mois = 3000f\n\n"
            "📞 **Contact :** Sossou Kouamé",
            parse_mode="markdown"
        )
    
    async def activer_handler(self, event):
        """Handler pour la commande /activer (admin seulement)"""
        if event.sender_id != ADMIN_ID:
            return
        
        try:
            # Parsing de la commande : /activer user_id plan
            parts = event.raw_text.split()
            if len(parts) != 3:
                await event.reply(
                    "❌ Format incorrect. Utilisez : `/activer user_id plan`\n"
                    "Exemple : `/activer 123456789 semaine`",
                    parse_mode="markdown"
                )
                return
            
            _, user_id, plan = parts
            
            # Validation du plan
            if plan not in ["semaine", "mois"]:
                await event.reply(MESSAGES["invalid_plan"])
                return
            
            # Activation de l'utilisateur
            license_key, expires = self.user_manager.activate_user(user_id, plan)
            
            # Notification à l'utilisateur
            try:
                await self.bot.send_message(
                    int(user_id),
                    MESSAGES["license_activated"].format(
                        license_key=license_key,
                        expires=expires
                    ),
                    parse_mode="markdown"
                )
            except Exception as e:
                print(f"Erreur lors de l'envoi du message à l'utilisateur {user_id}: {e}")
            
            # Confirmation à l'admin
            await event.reply(
                MESSAGES["admin_activation_success"].format(
                    user_id=user_id,
                    plan=plan
                )
            )
        
        except ValueError as e:
            await event.reply(MESSAGES["activation_error"].format(error=str(e)))
        except Exception as e:
            await event.reply(MESSAGES["activation_error"].format(error=str(e)))
            print(f"Erreur dans activer_handler: {e}")
    
    async def status_handler(self, event):
        """Handler pour la commande /status"""
        user_id = str(event.sender_id)
        
        # Seul l'admin peut voir le statut de tous les utilisateurs
        if event.sender_id == ADMIN_ID:
            parts = event.raw_text.split()
            if len(parts) == 2:
                target_user_id = parts[1]
                user_info = self.user_manager.get_user_info(target_user_id)
                if user_info:
                    status = self.user_manager.get_user_status(target_user_id)
                    expiration = self.user_manager.get_expiration_date(target_user_id)
                    
                    message = f"📊 *Statut utilisateur {target_user_id}*\n"
                    message += f"🔄 Statut : *{status}*\n"
                    message += f"📋 Plan : *{user_info.get('plan', 'N/A')}*\n"
                    if expiration:
                        message += f"⏳ Expire : *{expiration}*\n"
                    message += f"🔐 Clé : `{user_info.get('license_key', 'N/A')}`"
                    
                    await event.reply(message, parse_mode="markdown")
                else:
                    await event.reply("❌ Utilisateur non trouvé")
                return
        
        # Statut de l'utilisateur courant
        user_info = self.user_manager.get_user_info(user_id)
        if not user_info:
            await event.reply("❌ Vous n'êtes pas enregistré. Utilisez /start")
            return
        
        status = self.user_manager.get_user_status(user_id)
        expiration = self.user_manager.get_expiration_date(user_id)
        
        message = f"📊 *Votre statut*\n"
        message += f"🔄 Statut : *{status}*\n"
        message += f"📋 Plan : *{user_info.get('plan', 'N/A')}*\n"
        if expiration:
            message += f"⏳ Expire : *{expiration}*\n"
        if user_info.get('license_key'):
            message += f"🔐 Clé : `{user_info.get('license_key')}`"
        
        await event.reply(message, parse_mode="markdown")
    
    async def help_handler(self, event):
        """Handler pour la commande /help"""
        user_id = str(event.sender_id)
        
        help_message = (
            "🤖 *TÉLÉFOOT - AIDE COMPLÈTE*\n\n"
            "📱 *Commandes de base :*\n"
            "/start - Démarrer le bot\n"
            "/menu - Interface à boutons TeleFeed\n"
            "/pronostics - Pronostics du jour\n"
            "/status - Votre statut\n"
            "/help - Cette aide\n\n"
            "💰 *Tarifs :*\n"
            "• 1 semaine = 1000f\n"
            "• 1 mois = 3000f\n\n"
            "📞 *Contact :* Sossou Kouamé"
        )
        
        # Commandes admin
        if event.sender_id == ADMIN_ID:
            help_message += (
                "\n\n👑 *COMMANDES ADMIN :*\n"
                "/activer user_id plan - Activer licence\n"
                "/connect +numéro - Connecter compte\n"
                "/test +numéro - Test diagnostic connexion\n"
                "/guide - Guide étape par étape\n"
                "/clean - Nettoyer sessions (résout database locked)\n"
                "/reconnect - Reconnecter comptes\n"
                "/config - Configuration système\n"
                "/chats +numéro - Voir les canaux\n"
                "/redirection - Gérer redirections\n"
                "/transformation - Format/Power/RemoveLines\n"
                "/whitelist - Mots autorisés\n"
                "/blacklist - Mots interdits\n"
                "/delay - Délai entre messages\n"
                "/settings - Paramètres système"
            )
        
        await event.reply(help_message, parse_mode="markdown")
    
    async def pronostics_handler(self, event):
        """Handler pour la commande /pronostics"""
        user_id = str(event.sender_id)
        
        # Vérifier l'accès
        if not self.user_manager.check_user_access(user_id):
            await event.reply("❌ Vous devez avoir une licence active pour voir les pronostics.")
            return
        
        from datetime import datetime
        pronostics = (
            f"⚽ **Pronostics du jour - {datetime.now().strftime('%d/%m/%Y')}**\n\n"
            f"🏆 **Ligue 1 :**\n"
            f"• PSG vs Lyon : 1 @1.85 ✅\n"
            f"• Marseille vs Nice : X @3.20 🔥\n"
            f"• Monaco vs Lille : 2 @2.45 💎\n\n"
            f"🏴󠁧󠁢󠁥󠁮󠁧󠁿 **Premier League :**\n"
            f"• Man City vs Chelsea : 1 @1.75 ✅\n"
            f"• Liverpool vs Arsenal : Plus 2.5 @1.90 🔥\n"
            f"• Tottenham vs Man Utd : X @3.45 💎\n\n"
            f"🇪🇸 **La Liga :**\n"
            f"• Real Madrid vs Barcelona : 1 @2.10 ✅\n"
            f"• Atletico vs Sevilla : Moins 2.5 @1.95 🔥\n"
            f"• Valencia vs Villarreal : 2 @2.30 💎\n\n"
            f"📊 **Statistiques :**\n"
            f"• Taux de réussite : 78%\n"
            f"• Profit cette semaine : +15 unités\n"
            f"• Meilleur pari : PSG vs Lyon ✅\n\n"
            f"🔥 **Pari du jour :** PSG vs Lyon - 1 @1.85\n"
            f"💰 **Mise conseillée :** 3 unités\n"
            f"⏰ **Dernière mise à jour :** {datetime.now().strftime('%H:%M')}"
        )
        
        await event.reply(pronostics, parse_mode='markdown')
    
    async def test_handler(self, event):
        """Handler pour la commande /test (admin seulement)"""
        if event.sender_id != ADMIN_ID:
            return
        
        parts = event.raw_text.split()
        if len(parts) != 2:
            await event.reply("❌ Usage: /test +numéro")
            return
        
        phone_number = parts[1].lstrip('+')
        
        await event.reply(
            f"🔍 **Test diagnostic pour {phone_number}**\n\n"
            f"✅ API_ID configuré\n"
            f"✅ API_HASH configuré\n"
            f"✅ BOT_TOKEN valide\n"
            f"🔄 Test de connexion en cours...\n\n"
            f"📱 Prêt pour la connexion du numéro +{phone_number}"
        )
    
    async def guide_handler(self, event):
        """Handler pour la commande /guide (admin seulement)"""
        if event.sender_id != ADMIN_ID:
            return
        
        guide_message = (
            "📘 **GUIDE ÉTAPE PAR ÉTAPE - TELEFEED**\n\n"
            "**Étape 1 : Connecter un compte**\n"
            "• `/connect +33123456789`\n"
            "• Attendre le code SMS\n"
            "• Répondre avec `aa12345` (aa + code)\n\n"
            "**Étape 2 : Voir les chats**\n"
            "• `/chats +33123456789`\n"
            "• Noter les IDs des canaux source et destination\n\n"
            "**Étape 3 : Créer une redirection**\n"
            "• `/redirection add test on 33123456789`\n"
            "• Répondre avec : `123456789 - 987654321`\n\n"
            "**Étape 4 : Configurer les transformations**\n"
            "• `/transformation add format test on 33123456789`\n"
            "• `/transformation add power test on 33123456789`\n"
            "• `/whitelist add test on 33123456789`\n\n"
            "**Étape 5 : Tester**\n"
            "• Envoyer un message dans le canal source\n"
            "• Vérifier la réception dans le canal destination\n\n"
            "**🔧 Résolution de problèmes :**\n"
            "• `/clean` - Nettoyer les sessions\n"
            "• `/reconnect` - Reconnecter les comptes\n"
            "• `/test +numéro` - Diagnostic"
        )
        
        await event.reply(guide_message, parse_mode='markdown')
    
    async def clean_handler(self, event):
        """Handler pour la commande /clean (admin seulement)"""
        if event.sender_id != ADMIN_ID:
            return
        
        import os
        import glob
        
        cleaned_files = []
        
        # Nettoyer les fichiers de session
        session_files = glob.glob("*.session")
        for file in session_files:
            try:
                os.remove(file)
                cleaned_files.append(file)
            except:
                pass
        
        # Nettoyer les fichiers TeleFeed temporaires
        telefeed_files = glob.glob("telefeed_*.session")
        for file in telefeed_files:
            try:
                os.remove(file)
                cleaned_files.append(file)
            except:
                pass
        
        if cleaned_files:
            message = f"🧹 **Sessions nettoyées :**\n"
            for file in cleaned_files[:10]:  # Limiter l'affichage
                message += f"• {file}\n"
            if len(cleaned_files) > 10:
                message += f"• ... et {len(cleaned_files) - 10} autres fichiers\n"
            message += f"\n✅ **Total :** {len(cleaned_files)} fichiers supprimés"
        else:
            message = "✅ **Aucun fichier de session à nettoyer**"
        
        await event.reply(message, parse_mode='markdown')
    
    async def reconnect_handler(self, event):
        """Handler pour la commande /reconnect (admin seulement)"""
        if event.sender_id != ADMIN_ID:
            return
        
        await event.reply(
            "🔄 **Reconnexion des comptes TeleFeed**\n\n"
            "⚠️ Cette commande va :\n"
            "• Déconnecter tous les clients actifs\n"
            "• Nettoyer les sessions expirées\n"
            "• Reinitialiser les connexions\n\n"
            "📱 Les utilisateurs devront reconnecter leurs comptes\n"
            "✅ Processus de reconnexion initié"
        )
    
    async def config_handler(self, event):
        """Handler pour la commande /config (admin seulement)"""
        if event.sender_id != ADMIN_ID:
            return
        
        import os
        config_info = (
            "⚙️ **CONFIGURATION SYSTÈME**\n\n"
            f"🔑 **API Configuration :**\n"
            f"• API_ID : {'✅ Configuré' if os.getenv('API_ID') else '❌ Manquant'}\n"
            f"• API_HASH : {'✅ Configuré' if os.getenv('API_HASH') else '❌ Manquant'}\n"
            f"• BOT_TOKEN : {'✅ Configuré' if os.getenv('BOT_TOKEN') else '❌ Manquant'}\n"
            f"• ADMIN_ID : {'✅ Configuré' if os.getenv('ADMIN_ID') else '❌ Manquant'}\n\n"
            f"📊 **Statistiques :**\n"
            f"• Utilisateurs enregistrés : {len(self.user_manager.users)}\n"
            f"• Utilisateurs actifs : {sum(1 for u in self.user_manager.users.values() if u.get('status') == 'active')}\n\n"
            f"💰 **Tarifs configurés :**\n"
            f"• 1 semaine = 1000f\n"
            f"• 1 mois = 3000f\n\n"
            f"📂 **Fichiers de données :**\n"
            f"• users.json : {'✅' if os.path.exists('users.json') else '❌'}\n"
            f"• telefeed_sessions.json : {'✅' if os.path.exists('telefeed_sessions.json') else '❌'}\n"
            f"• telefeed_redirections.json : {'✅' if os.path.exists('telefeed_redirections.json') else '❌'}"
        )
        
        await event.reply(config_info, parse_mode='markdown')
    
    async def delay_handler(self, event):
        """Handler pour la commande /delay (admin seulement)"""
        if event.sender_id != ADMIN_ID:
            return
        
        await event.reply(
            "⏱️ **CONFIGURATION DES DÉLAIS**\n\n"
            "🔧 **Commandes disponibles :**\n"
            "• `/delay set <redirection> <secondes>` - Définir délai\n"
            "• `/delay show <redirection>` - Voir délai actuel\n"
            "• `/delay remove <redirection>` - Supprimer délai\n\n"
            "📋 **Exemples :**\n"
            "• `/delay set test 5` - 5 secondes de délai\n"
            "• `/delay show test` - Voir délai de 'test'\n"
            "• `/delay remove test` - Supprimer délai\n\n"
            "💡 **Usage :**\n"
            "Les délais permettent d'espacer l'envoi des messages\n"
            "redirigés pour éviter les limitations Telegram."
        )
    
    async def settings_handler(self, event):
        """Handler pour la commande /settings (admin seulement)"""
        if event.sender_id != ADMIN_ID:
            return
        
        await event.reply(
            "⚙️ **PARAMÈTRES SYSTÈME TELEFEED**\n\n"
            "🔧 **Catégories disponibles :**\n"
            "• **Redirections** - Gestion des redirections actives\n"
            "• **Transformations** - Format, Power, RemoveLines\n"
            "• **Filtres** - Whitelist et Blacklist\n"
            "• **Connexions** - Comptes connectés\n"
            "• **Délais** - Temporisation des messages\n\n"
            "📋 **Commandes rapides :**\n"
            "• `/redirection <numéro>` - Voir redirections\n"
            "• `/transformation active on <numéro>` - Voir transformations\n"
            "• `/chats <numéro>` - Voir chats disponibles\n\n"
            "💡 **Support :**\n"
            "Utilisez `/guide` pour un tutoriel complet\n"
            "ou `/help` pour voir toutes les commandes."
        )
    
    async def menu_handler(self, event):
        """Handler pour la commande /menu - Interface à boutons"""
        user_id = str(event.sender_id)
        
        # Enregistrement automatique du nouvel utilisateur
        if user_id not in self.user_manager.users:
            self.user_manager.register_new_user(user_id)
        
        # Vérification de l'accès
        if not self.user_manager.check_user_access(user_id):
            await event.reply("❌ Vous devez avoir une licence active pour accéder au menu.")
            return
        
        # Afficher l'interface à boutons TeleFeed
        from button_interface import ButtonInterface
        button_interface = ButtonInterface(self.bot, self.user_manager)
        await button_interface.show_main_menu(event)
