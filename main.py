#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot Telegram Téléfoot avec système de gestion de licences
Utilise Telethon pour la communication avec l'API Telegram
"""

import asyncio
import signal
import sys
import os
from datetime import datetime
from telethon import TelegramClient
from telethon.errors import AuthKeyError, FloodWaitError

from config import API_ID, API_HASH, BOT_TOKEN, ADMIN_ID
from user_manager import UserManager
from bot_handlers import BotHandlers
from telefeed_commands import register_all_handlers
from button_interface import ButtonInterface

class TelefootBot:
    """Bot Telegram principal avec gestion de licences"""
    
    def __init__(self):
        self.client = None
        self.user_manager = UserManager()
        self.handlers = None
        self.button_interface = None
        self.running = False
    
    async def initialize(self):
        """Initialise le client Telegram et les handlers"""
        try:
            # Création du client Telegram
            self.client = TelegramClient(
                'bot_session', 
                API_ID, 
                API_HASH
            )
            
            # Démarrage avec le token bot
            await self.client.start(bot_token=BOT_TOKEN)
            
            # Vérification que le bot est bien connecté
            me = await self.client.get_me()
            print(f"🤖 Bot connecté : @{me.username} ({me.id})")
            
            # Initialisation des handlers
            self.handlers = BotHandlers(self.client, self.user_manager)
            
            # Initialisation de l'interface à boutons
            self.button_interface = ButtonInterface(self.client, self.user_manager)
            
            # Enregistrement des handlers TeleFeed
            await register_all_handlers(self.client, ADMIN_ID, API_ID, API_HASH)
            
            # Restaurer automatiquement les sessions TeleFeed existantes
            from telefeed_commands import telefeed_manager
            await self.restore_telefeed_sessions(telefeed_manager)
            
            print("✅ Bot initialisé avec succès")
            print("🚀 Fonctionnalités TeleFeed activées")
            return True
            
        except AuthKeyError:
            print("❌ Erreur d'authentification (API_HASH ou BOT_TOKEN invalide)")
            return False
        except FloodWaitError as e:
            print(f"❌ Limite de taux dépassée, attendre {e.seconds} secondes")
            return False
        except Exception as e:
            print(f"❌ Erreur d'initialisation : {e}")
            return False
    
    async def restore_telefeed_sessions(self, telefeed_manager):
        """Restaure automatiquement les sessions TeleFeed existantes"""
        print("🔄 Restauration des sessions TeleFeed...")
        
        restored_count = 0
        total_sessions = len(telefeed_manager.sessions)
        
        for phone_number, session_data in telefeed_manager.sessions.items():
            if isinstance(session_data, dict) and session_data.get('connected'):
                if phone_number.startswith('temp_'):
                    continue  # Ignorer les sessions temporaires
                
                try:
                    session_name = f"telefeed_{phone_number}"
                    
                    # Vérifier si le fichier de session existe
                    if os.path.exists(f"{session_name}.session"):
                        from config import API_ID, API_HASH
                        from telethon import TelegramClient
                        
                        client = TelegramClient(session_name, API_ID, API_HASH)
                        await client.connect()
                        
                        # Vérifier si la session est toujours valide
                        if await client.is_user_authorized():
                            telefeed_manager.clients[phone_number] = client
                            # Marquer la session comme restaurée
                            telefeed_manager.sessions[phone_number]['restored_at'] = datetime.now().isoformat()
                            
                            # Configurer les gestionnaires de redirection
                            await telefeed_manager.setup_redirection_handlers(client, phone_number)
                            
                            restored_count += 1
                            print(f"✅ Session restaurée pour {phone_number}")
                        else:
                            print(f"⚠️ Session expirée pour {phone_number}")
                            # Marquer la session comme expirée
                            telefeed_manager.sessions[phone_number]['connected'] = False
                            telefeed_manager.sessions[phone_number]['expired_at'] = datetime.now().isoformat()
                            try:
                                await client.disconnect()
                            except:
                                pass
                    else:
                        print(f"⚠️ Fichier de session manquant pour {phone_number}")
                        # Marquer la session comme manquante
                        telefeed_manager.sessions[phone_number]['connected'] = False
                        telefeed_manager.sessions[phone_number]['missing_file'] = True
                        
                except Exception as e:
                    print(f"❌ Erreur lors de la restauration de {phone_number}: {e}")
                    # Marquer la session comme en erreur
                    telefeed_manager.sessions[phone_number]['connected'] = False
                    telefeed_manager.sessions[phone_number]['error'] = str(e)
        
        # Sauvegarder les changements
        telefeed_manager.save_all_data()
        print(f"🔄 {restored_count}/{total_sessions} sessions TeleFeed restaurées")
    
    async def start(self):
        """Démarre le bot"""
        if not await self.initialize():
            return False
        
        self.running = True
        print("🚀 Bot démarré et en attente de messages...")
        
        try:
            # Nettoyage périodique des utilisateurs expirés
            asyncio.create_task(self.cleanup_task())
            
            # Boucle principale
            if self.client:
                await self.client.run_until_disconnected()
            
        except KeyboardInterrupt:
            print("\n⏹️  Arrêt du bot demandé")
        except Exception as e:
            print(f"❌ Erreur durant l'exécution : {e}")
        finally:
            await self.stop()
    
    async def cleanup_task(self):
        """Tâche de nettoyage périodique"""
        while self.running:
            try:
                # Attendre 1 heure
                await asyncio.sleep(3600)
                
                # Nettoyer les utilisateurs expirés
                cleaned = self.user_manager.cleanup_expired_users()
                if cleaned > 0:
                    print(f"🧹 {cleaned} utilisateurs expirés nettoyés")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"❌ Erreur dans cleanup_task : {e}")
    
    async def stop(self):
        """Arrête le bot proprement"""
        self.running = False
        if self.client and self.client.is_connected():
            await self.client.disconnect()
        print("⏹️  Bot arrêté")

def signal_handler(sig, frame):
    """Gestionnaire de signal pour arrêt propre"""
    print(f"\n🛑 Signal {sig} reçu, arrêt du bot...")
    sys.exit(0)

async def main():
    """Fonction principale"""
    # Gestion des signaux pour arrêt propre
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Création et démarrage du bot
    bot = TelefootBot()
    
    try:
        await bot.start()
    except Exception as e:
        print(f"❌ Erreur fatale : {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        # Lancement du bot
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Au revoir !")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Erreur critique : {e}")
        sys.exit(1)
