#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Système de redirection avancé pour faire apparaître les messages comme venant du canal de destination
"""

import json
import os
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat
from advanced_user_manager import AdvancedUserManager

logger = logging.getLogger(__name__)

class ChannelRedirectionSystem:
    """Système de redirection qui fait apparaître les messages comme venant du canal de destination"""
    
    def __init__(self, user_manager: AdvancedUserManager):
        self.user_manager = user_manager
        self.active_clients = {}  # user_id -> TelegramClient
        self.redirections = {}    # user_id -> [{'source': id, 'destinations': [ids], 'active': bool}]
        self.load_redirections()
    
    def load_redirections(self):
        """Charge les redirections depuis le fichier"""
        try:
            if os.path.exists('redirections_advanced.json'):
                with open('redirections_advanced.json', 'r', encoding='utf-8') as f:
                    self.redirections = json.load(f)
        except Exception as e:
            logger.error(f"Erreur chargement redirections: {e}")
            self.redirections = {}
    
    def save_redirections(self):
        """Sauvegarde les redirections"""
        try:
            with open('redirections_advanced.json', 'w', encoding='utf-8') as f:
                json.dump(self.redirections, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erreur sauvegarde redirections: {e}")
    
    async def connect_user_client(self, user_id: str, phone: str, api_id: int, api_hash: str) -> Tuple[bool, str]:
        """Connecte un client Telegram pour un utilisateur"""
        try:
            client = TelegramClient(f'user_{user_id}', api_id, api_hash)
            await client.connect()
            
            if not await client.is_user_authorized():
                # Demander le code de vérification
                await client.send_code_request(phone)
                return False, "Code de vérification envoyé. Utilisez /verify_code pour confirmer."
            
            # Client autorisé
            self.active_clients[user_id] = client
            await self.setup_message_handlers(user_id)
            
            return True, "Client connecté avec succès"
            
        except Exception as e:
            logger.error(f"Erreur connexion client {user_id}: {e}")
            return False, f"Erreur de connexion: {str(e)}"
    
    async def verify_code(self, user_id: str, phone: str, code: str) -> Tuple[bool, str]:
        """Vérifie le code d'authentification"""
        try:
            if user_id not in self.active_clients:
                return False, "Aucune session en cours. Reconnectez-vous."
            
            client = self.active_clients[user_id]
            await client.sign_in(phone, code)
            
            if await client.is_user_authorized():
                await self.setup_message_handlers(user_id)
                return True, "Authentification réussie"
            else:
                return False, "Code incorrect"
                
        except Exception as e:
            logger.error(f"Erreur vérification code {user_id}: {e}")
            return False, f"Erreur: {str(e)}"
    
    async def setup_message_handlers(self, user_id: str):
        """Configure les gestionnaires de messages pour les redirections"""
        if user_id not in self.active_clients:
            return
        
        client = self.active_clients[user_id]
        
        @client.on(events.NewMessage)
        async def handle_new_message(event):
            await self.process_message_for_redirection(user_id, event, is_edit=False)
        
        @client.on(events.MessageEdited)
        async def handle_edited_message(event):
            await self.process_message_for_redirection(user_id, event, is_edit=True)
        
        logger.info(f"Gestionnaires de messages configurés pour l'utilisateur {user_id}")
    
    async def process_message_for_redirection(self, user_id: str, event, is_edit: bool = False):
        """Traite un message pour redirection avec apparence du canal de destination"""
        try:
            # Vérifier l'accès utilisateur
            if not self.user_manager.check_user_access(user_id):
                return
            
            # Récupérer les redirections de l'utilisateur
            user_redirections = self.redirections.get(user_id, [])
            if not user_redirections:
                return
            
            source_chat_id = event.chat_id
            message_text = event.message.message
            
            # Chercher les redirections correspondantes
            for redirection in user_redirections:
                if not redirection.get('active', True):
                    continue
                
                if redirection['source'] == source_chat_id:
                    # Rediriger vers toutes les destinations
                    for dest_id in redirection['destinations']:
                        await self.send_message_as_channel(
                            user_id, dest_id, message_text, event.message, is_edit
                        )
                        
                        logger.info(f"Message {'édité' if is_edit else 'redirigé'} de {source_chat_id} vers {dest_id} pour utilisateur {user_id}")
        
        except Exception as e:
            logger.error(f"Erreur traitement message redirection {user_id}: {e}")
    
    async def send_message_as_channel(self, user_id: str, dest_chat_id: int, text: str, 
                                    original_message, is_edit: bool = False):
        """Envoie un message qui apparaît comme venant du canal de destination"""
        try:
            if user_id not in self.active_clients:
                return False
            
            client = self.active_clients[user_id]
            
            # Obtenir l'entité du canal de destination
            dest_entity = await client.get_entity(dest_chat_id)
            
            # Vérifier les permissions dans le canal
            if hasattr(dest_entity, 'admin_rights') or hasattr(dest_entity, 'creator'):
                # L'utilisateur a les droits admin, peut poster au nom du canal
                
                if is_edit:
                    # Pour les éditions, nous devons retrouver le message correspondant
                    # Ici nous pourrions implémenter un système de mapping des messages
                    # Pour simplifier, nous envoyons un nouveau message avec indication
                    text = f"📝 *[Message édité]*\n\n{text}"
                
                # Envoyer le message au nom du canal
                await client.send_message(dest_entity, text, parse_mode='markdown')
                return True
            else:
                # L'utilisateur n'a pas les droits, envoyer un message normal avec indication
                formatted_text = f"🔄 *[Redirection]*\n\n{text}"
                await client.send_message(dest_entity, formatted_text, parse_mode='markdown')
                return True
                
        except Exception as e:
            logger.error(f"Erreur envoi message canal {user_id}: {e}")
            return False
    
    async def add_redirection(self, user_id: str, source_id: int, destination_ids: List[int]) -> Tuple[bool, str]:
        """Ajoute une redirection si l'utilisateur a la capacité"""
        try:
            # Vérifier la capacité de l'utilisateur
            if not self.user_manager.can_add_redirection(user_id):
                max_redirections = self.user_manager.get_user_max_redirections(user_id)
                current = self.user_manager.get_user_info(user_id).get('current_redirections', 0)
                return False, f"Limite atteinte: {current}/{max_redirections} redirections"
            
            # Vérifier que l'utilisateur a accès aux canaux
            if user_id not in self.active_clients:
                return False, "Client Telegram non connecté. Utilisez /connect d'abord."
            
            client = self.active_clients[user_id]
            
            # Vérifier l'accès au canal source
            try:
                source_entity = await client.get_entity(source_id)
            except Exception:
                return False, f"Impossible d'accéder au canal source {source_id}"
            
            # Vérifier l'accès aux canaux de destination
            accessible_destinations = []
            for dest_id in destination_ids:
                try:
                    dest_entity = await client.get_entity(dest_id)
                    accessible_destinations.append(dest_id)
                except Exception:
                    logger.warning(f"Canal destination {dest_id} inaccessible pour {user_id}")
            
            if not accessible_destinations:
                return False, "Aucun canal de destination accessible"
            
            # Ajouter la redirection
            if user_id not in self.redirections:
                self.redirections[user_id] = []
            
            redirection = {
                'id': len(self.redirections[user_id]) + 1,
                'source': source_id,
                'destinations': accessible_destinations,
                'active': True,
                'created_at': datetime.now().isoformat(),
                'source_name': getattr(source_entity, 'title', str(source_id))
            }
            
            self.redirections[user_id].append(redirection)
            self.save_redirections()
            
            # Mettre à jour le compteur utilisateur
            self.user_manager.add_redirection(user_id)
            
            dest_names = []
            for dest_id in accessible_destinations:
                try:
                    entity = await client.get_entity(dest_id)
                    dest_names.append(getattr(entity, 'title', str(dest_id)))
                except:
                    dest_names.append(str(dest_id))
            
            return True, f"Redirection ajoutée: {redirection['source_name']} → {', '.join(dest_names)}"
            
        except Exception as e:
            logger.error(f"Erreur ajout redirection {user_id}: {e}")
            return False, f"Erreur: {str(e)}"
    
    async def remove_redirection(self, user_id: str, redirection_id: int) -> Tuple[bool, str]:
        """Supprime une redirection"""
        try:
            user_redirections = self.redirections.get(user_id, [])
            
            # Trouver la redirection
            redirection_to_remove = None
            for i, redirection in enumerate(user_redirections):
                if redirection['id'] == redirection_id:
                    redirection_to_remove = i
                    break
            
            if redirection_to_remove is None:
                return False, "Redirection non trouvée"
            
            # Supprimer la redirection
            removed = user_redirections.pop(redirection_to_remove)
            self.save_redirections()
            
            # Mettre à jour le compteur utilisateur
            self.user_manager.remove_redirection(user_id)
            
            return True, f"Redirection supprimée: {removed.get('source_name', 'Canal')}"
            
        except Exception as e:
            logger.error(f"Erreur suppression redirection {user_id}: {e}")
            return False, f"Erreur: {str(e)}"
    
    async def list_user_redirections(self, user_id: str) -> List[Dict]:
        """Liste les redirections d'un utilisateur"""
        try:
            user_redirections = self.redirections.get(user_id, [])
            
            if user_id in self.active_clients:
                client = self.active_clients[user_id]
                
                # Enrichir avec les noms des canaux
                for redirection in user_redirections:
                    try:
                        # Nom du canal source
                        if 'source_name' not in redirection:
                            source_entity = await client.get_entity(redirection['source'])
                            redirection['source_name'] = getattr(source_entity, 'title', str(redirection['source']))
                        
                        # Noms des canaux de destination
                        if 'destination_names' not in redirection:
                            dest_names = []
                            for dest_id in redirection['destinations']:
                                try:
                                    dest_entity = await client.get_entity(dest_id)
                                    dest_names.append(getattr(dest_entity, 'title', str(dest_id)))
                                except:
                                    dest_names.append(str(dest_id))
                            redirection['destination_names'] = dest_names
                    except Exception as e:
                        logger.warning(f"Erreur enrichissement redirection {user_id}: {e}")
            
            return user_redirections
            
        except Exception as e:
            logger.error(f"Erreur liste redirections {user_id}: {e}")
            return []
    
    async def get_user_channels(self, user_id: str) -> List[Dict]:
        """Récupère la liste des canaux accessibles à l'utilisateur"""
        try:
            if user_id not in self.active_clients:
                return []
            
            client = self.active_clients[user_id]
            channels = []
            
            async for dialog in client.iter_dialogs():
                if hasattr(dialog.entity, 'broadcast') or hasattr(dialog.entity, 'megagroup'):
                    channel_info = {
                        'id': dialog.entity.id,
                        'title': dialog.entity.title,
                        'username': getattr(dialog.entity, 'username', None),
                        'is_broadcast': getattr(dialog.entity, 'broadcast', False),
                        'is_megagroup': getattr(dialog.entity, 'megagroup', False),
                        'member_count': getattr(dialog.entity, 'participants_count', 0)
                    }
                    channels.append(channel_info)
            
            return channels
            
        except Exception as e:
            logger.error(f"Erreur récupération canaux {user_id}: {e}")
            return []
    
    async def disconnect_user(self, user_id: str):
        """Déconnecte un utilisateur"""
        try:
            if user_id in self.active_clients:
                client = self.active_clients[user_id]
                await client.disconnect()
                del self.active_clients[user_id]
                logger.info(f"Utilisateur {user_id} déconnecté")
        except Exception as e:
            logger.error(f"Erreur déconnexion {user_id}: {e}")
    
    async def get_redirection_stats(self) -> Dict:
        """Statistiques des redirections"""
        total_redirections = 0
        active_users = len(self.active_clients)
        
        for user_redirections in self.redirections.values():
            total_redirections += len([r for r in user_redirections if r.get('active', True)])
        
        return {
            'active_users': active_users,
            'total_redirections': total_redirections,
            'connected_clients': list(self.active_clients.keys())
        }

# Instance globale du système de redirection
redirection_system = None

def get_redirection_system(user_manager: AdvancedUserManager) -> ChannelRedirectionSystem:
    """Obtient l'instance du système de redirection"""
    global redirection_system
    if redirection_system is None:
        redirection_system = ChannelRedirectionSystem(user_manager)
    return redirection_system