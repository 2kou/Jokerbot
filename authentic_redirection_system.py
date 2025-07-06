#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Système de redirection authentique - Messages apparaissent vraiment du canal de destination
"""

import json
import os
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import logging
from telethon import TelegramClient, events
from telethon.tl.types import Channel, Chat, MessageMediaPhoto, MessageMediaDocument
from telethon.tl.functions.channels import GetParticipantRequest
from telethon.tl.functions.messages import ForwardMessagesRequest, SendMessageRequest
from telethon.errors import ChatAdminRequiredError, UserNotParticipantError

logger = logging.getLogger(__name__)

class AuthenticRedirectionSystem:
    """Système qui fait apparaître les messages comme vraiment envoyés par le canal de destination"""
    
    def __init__(self, user_manager):
        self.user_manager = user_manager
        self.active_clients = {}  # user_id -> TelegramClient
        self.channel_clients = {}  # channel_id -> TelegramClient (clients avec droits admin)
        self.redirections = {}    # user_id -> [redirections]
        self.message_mapping = {} # source_msg_id -> dest_msg_id (pour éditions)
        self.load_redirections()
    
    def load_redirections(self):
        """Charge les redirections depuis le fichier"""
        try:
            if os.path.exists('authentic_redirections.json'):
                with open('authentic_redirections.json', 'r', encoding='utf-8') as f:
                    self.redirections = json.load(f)
        except Exception as e:
            logger.error(f"Erreur chargement redirections: {e}")
            self.redirections = {}
    
    def save_redirections(self):
        """Sauvegarde les redirections"""
        try:
            with open('authentic_redirections.json', 'w', encoding='utf-8') as f:
                json.dump(self.redirections, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Erreur sauvegarde redirections: {e}")
    
    async def connect_channel_admin(self, user_id: str, phone: str, api_id: int, api_hash: str) -> Tuple[bool, str]:
        """Connecte un client avec les droits administrateur sur les canaux"""
        try:
            client = TelegramClient(f'admin_{user_id}', api_id, api_hash)
            await client.connect()
            
            if not await client.is_user_authorized():
                await client.send_code_request(phone)
                return False, "Code de vérification envoyé. Utilisez /verify_code pour confirmer."
            
            # Vérifier les droits administrateur sur les canaux
            admin_channels = await self.get_admin_channels(client)
            
            if not admin_channels:
                await client.disconnect()
                return False, "Aucun canal avec droits administrateur trouvé. Vous devez être admin des canaux pour la redirection authentique."
            
            self.active_clients[user_id] = client
            
            # Associer le client aux canaux où il est admin
            for channel_id in admin_channels:
                self.channel_clients[channel_id] = client
            
            await self.setup_authentic_handlers(user_id, client)
            
            return True, f"Client connecté avec droits admin sur {len(admin_channels)} canaux"
            
        except Exception as e:
            logger.error(f"Erreur connexion admin {user_id}: {e}")
            return False, f"Erreur de connexion: {str(e)}"
    
    async def get_admin_channels(self, client: TelegramClient) -> List[int]:
        """Récupère la liste des canaux où l'utilisateur est administrateur"""
        admin_channels = []
        
        try:
            async for dialog in client.iter_dialogs():
                if hasattr(dialog.entity, 'broadcast') or hasattr(dialog.entity, 'megagroup'):
                    try:
                        # Vérifier les droits administrateur
                        participant = await client(GetParticipantRequest(
                            channel=dialog.entity,
                            participant='me'
                        ))
                        
                        # Vérifier si l'utilisateur peut poster des messages
                        if hasattr(participant.participant, 'admin_rights'):
                            admin_rights = participant.participant.admin_rights
                            if admin_rights.post_messages or admin_rights.edit_messages:
                                admin_channels.append(dialog.entity.id)
                                logger.info(f"Droits admin confirmés sur {dialog.entity.title} ({dialog.entity.id})")
                        elif hasattr(participant.participant, 'creator') and participant.participant.creator:
                            admin_channels.append(dialog.entity.id)
                            logger.info(f"Créateur du canal {dialog.entity.title} ({dialog.entity.id})")
                            
                    except (ChatAdminRequiredError, UserNotParticipantError):
                        continue
                    except Exception as e:
                        logger.warning(f"Erreur vérification droits {dialog.entity.title}: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"Erreur récupération canaux admin: {e}")
        
        return admin_channels
    
    async def setup_authentic_handlers(self, user_id: str, client: TelegramClient):
        """Configure les gestionnaires pour redirection authentique"""
        
        @client.on(events.NewMessage)
        async def handle_authentic_message(event):
            await self.process_authentic_redirection(user_id, event, is_edit=False)
        
        @client.on(events.MessageEdited)
        async def handle_authentic_edit(event):
            await self.process_authentic_redirection(user_id, event, is_edit=True)
        
        logger.info(f"Gestionnaires authentiques configurés pour {user_id}")
    
    async def process_authentic_redirection(self, user_id: str, event, is_edit: bool = False):
        """Traite la redirection avec messages authentiques du canal de destination"""
        try:
            if not self.user_manager.check_user_access(user_id):
                return
            
            source_chat_id = event.chat_id
            user_redirections = self.redirections.get(user_id, [])
            
            for redirection in user_redirections:
                if not redirection.get('active', True):
                    continue
                
                if redirection['source'] == source_chat_id:
                    for dest_id in redirection['destinations']:
                        success = await self.send_authentic_message(
                            dest_id, event.message, source_chat_id, is_edit
                        )
                        
                        if success:
                            logger.info(f"Message authentique {'édité' if is_edit else 'envoyé'} vers {dest_id}")
                        else:
                            logger.warning(f"Échec redirection authentique vers {dest_id}")
        
        except Exception as e:
            logger.error(f"Erreur redirection authentique {user_id}: {e}")
    
    async def send_authentic_message(self, dest_channel_id: int, original_message, 
                                   source_id: int, is_edit: bool = False) -> bool:
        """Envoie un message qui apparaît vraiment comme venant du canal de destination"""
        try:
            # Récupérer le client administrateur du canal de destination
            admin_client = self.channel_clients.get(dest_channel_id)
            
            if not admin_client:
                logger.warning(f"Aucun client admin trouvé pour le canal {dest_channel_id}")
                return False
            
            # Obtenir l'entité du canal de destination
            dest_channel = await admin_client.get_entity(dest_channel_id)
            
            # Préparer le contenu du message
            message_text = original_message.message
            
            if is_edit and hasattr(original_message, 'id'):
                # Pour les éditions, chercher le message correspondant
                mapped_msg_id = self.message_mapping.get(f"{source_id}_{original_message.id}")
                
                if mapped_msg_id:
                    try:
                        # Éditer le message existant
                        await admin_client.edit_message(
                            dest_channel,
                            mapped_msg_id,
                            message_text,
                            parse_mode='html'
                        )
                        logger.info(f"Message {mapped_msg_id} édité dans {dest_channel_id}")
                        return True
                    except Exception as e:
                        logger.warning(f"Impossible d'éditer le message {mapped_msg_id}: {e}")
                        # Fallback: envoyer un nouveau message avec indication d'édition
                        message_text = f"📝 <i>[Message édité]</i>\n\n{message_text}"
            
            # Envoyer le message au nom du canal (apparaîtra comme venant du canal)
            if hasattr(original_message, 'media') and original_message.media:
                # Message avec média
                sent_message = await admin_client.send_file(
                    dest_channel,
                    original_message.media,
                    caption=message_text,
                    parse_mode='html'
                )
            else:
                # Message texte uniquement
                sent_message = await admin_client.send_message(
                    dest_channel,
                    message_text,
                    parse_mode='html'
                )
            
            # Enregistrer le mapping pour les éditions futures
            if hasattr(original_message, 'id') and hasattr(sent_message, 'id'):
                self.message_mapping[f"{source_id}_{original_message.id}"] = sent_message.id
            
            return True
            
        except Exception as e:
            logger.error(f"Erreur envoi message authentique vers {dest_channel_id}: {e}")
            return False
    
    async def add_authentic_redirection(self, user_id: str, source_id: int, 
                                      destination_ids: List[int]) -> Tuple[bool, str]:
        """Ajoute une redirection authentique avec vérification des droits admin"""
        try:
            if not self.user_manager.can_add_redirection(user_id):
                max_redirections = self.user_manager.get_user_max_redirections(user_id)
                current = self.user_manager.get_user_info(user_id).get('current_redirections', 0)
                return False, f"Limite atteinte: {current}/{max_redirections} redirections"
            
            client = self.active_clients.get(user_id)
            if not client:
                return False, "Client non connecté. Utilisez /connect_admin d'abord."
            
            # Vérifier l'accès au canal source
            try:
                source_entity = await client.get_entity(source_id)
            except Exception:
                return False, f"Impossible d'accéder au canal source {source_id}"
            
            # Vérifier les droits admin sur les canaux de destination
            valid_destinations = []
            for dest_id in destination_ids:
                if dest_id in self.channel_clients:
                    try:
                        dest_entity = await client.get_entity(dest_id)
                        valid_destinations.append({
                            'id': dest_id,
                            'title': getattr(dest_entity, 'title', str(dest_id))
                        })
                    except Exception:
                        logger.warning(f"Canal destination {dest_id} inaccessible")
                else:
                    logger.warning(f"Pas de droits admin sur le canal {dest_id}")
            
            if not valid_destinations:
                return False, "Aucun canal de destination avec droits administrateur trouvé"
            
            # Créer la redirection
            if user_id not in self.redirections:
                self.redirections[user_id] = []
            
            redirection = {
                'id': len(self.redirections[user_id]) + 1,
                'source': source_id,
                'source_name': getattr(source_entity, 'title', str(source_id)),
                'destinations': [d['id'] for d in valid_destinations],
                'destination_names': [d['title'] for d in valid_destinations],
                'active': True,
                'created_at': datetime.now().isoformat(),
                'type': 'authentic'
            }
            
            self.redirections[user_id].append(redirection)
            self.save_redirections()
            self.user_manager.add_redirection(user_id)
            
            dest_names = ', '.join([d['title'] for d in valid_destinations])
            return True, f"Redirection authentique créée: {redirection['source_name']} → {dest_names}"
            
        except Exception as e:
            logger.error(f"Erreur ajout redirection authentique {user_id}: {e}")
            return False, f"Erreur: {str(e)}"
    
    async def test_authentic_message(self, user_id: str, channel_id: int, test_message: str) -> Tuple[bool, str]:
        """Teste l'envoi authentique sur un canal"""
        try:
            admin_client = self.channel_clients.get(channel_id)
            
            if not admin_client:
                return False, f"Pas de droits admin sur le canal {channel_id}"
            
            channel = await admin_client.get_entity(channel_id)
            
            # Envoyer un message de test
            test_text = f"🧪 <b>Test de redirection authentique</b>\n\n{test_message}\n\n<i>Ce message apparaît comme venant du canal {channel.title}</i>"
            
            sent_message = await admin_client.send_message(
                channel,
                test_text,
                parse_mode='html'
            )
            
            return True, f"Message test envoyé avec succès vers {channel.title} (ID: {sent_message.id})"
            
        except Exception as e:
            logger.error(f"Erreur test message authentique: {e}")
            return False, f"Erreur: {str(e)}"
    
    async def get_user_admin_channels(self, user_id: str) -> List[Dict]:
        """Récupère les canaux où l'utilisateur est admin"""
        try:
            client = self.active_clients.get(user_id)
            if not client:
                return []
            
            admin_channels = []
            
            for channel_id, channel_client in self.channel_clients.items():
                if channel_client == client:
                    try:
                        entity = await client.get_entity(channel_id)
                        admin_channels.append({
                            'id': channel_id,
                            'title': getattr(entity, 'title', str(channel_id)),
                            'username': getattr(entity, 'username', None),
                            'members': getattr(entity, 'participants_count', 0)
                        })
                    except Exception as e:
                        logger.warning(f"Erreur récupération info canal {channel_id}: {e}")
            
            return admin_channels
            
        except Exception as e:
            logger.error(f"Erreur récupération canaux admin {user_id}: {e}")
            return []
    
    async def remove_authentic_redirection(self, user_id: str, redirection_id: int) -> Tuple[bool, str]:
        """Supprime une redirection authentique"""
        try:
            user_redirections = self.redirections.get(user_id, [])
            
            redirection_to_remove = None
            for i, redirection in enumerate(user_redirections):
                if redirection['id'] == redirection_id:
                    redirection_to_remove = i
                    break
            
            if redirection_to_remove is None:
                return False, "Redirection non trouvée"
            
            removed = user_redirections.pop(redirection_to_remove)
            self.save_redirections()
            self.user_manager.remove_redirection(user_id)
            
            return True, f"Redirection authentique supprimée: {removed.get('source_name', 'Canal')}"
            
        except Exception as e:
            logger.error(f"Erreur suppression redirection authentique {user_id}: {e}")
            return False, f"Erreur: {str(e)}"
    
    async def get_redirection_stats(self) -> Dict:
        """Statistiques des redirections authentiques"""
        total_redirections = 0
        active_users = len(self.active_clients)
        admin_channels = len(self.channel_clients)
        
        for user_redirections in self.redirections.values():
            total_redirections += len([r for r in user_redirections if r.get('active', True)])
        
        return {
            'active_users': active_users,
            'admin_channels': admin_channels,
            'total_redirections': total_redirections,
            'authentic_type': True
        }

# Instance globale
authentic_redirection_system = None

def get_authentic_redirection_system(user_manager):
    """Obtient l'instance du système de redirection authentique"""
    global authentic_redirection_system
    if authentic_redirection_system is None:
        authentic_redirection_system = AuthenticRedirectionSystem(user_manager)
    return authentic_redirection_system