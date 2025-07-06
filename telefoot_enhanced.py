#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot Telegram Téléfoot Enhanced avec TeleFeed
Système complet de gestion de licences et de redirection de messages
"""

import os
import json
import re
import asyncio
import signal
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, PhoneCodeExpiredError
from telethon.tl.types import User, Chat, Channel

# Configuration
API_ID = int(os.getenv('API_ID', '0'))
API_HASH = os.getenv('API_HASH', '')
BOT_TOKEN = os.getenv('BOT_TOKEN', '')
ADMIN_ID = int(os.getenv('ADMIN_ID', '0'))

# Plans de licence
PLANS = {
    'weekly': {'duration': 7, 'price': 1000},
    'monthly': {'duration': 30, 'price': 3000}
}

# Données globales
users = {}
telefeed_sessions = {}
telefeed_redirections = {}
telefeed_transformations = {}
telefeed_whitelist = {}
telefeed_blacklist = {}
telefeed_settings = {}
telefeed_chats = {}
telefeed_clients = {}
pending_connections = {}

def load_json(filename):
    """Charge un fichier JSON"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except:
        return {}

def save_json(filename, data):
    """Sauvegarde un fichier JSON"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except:
        return False

def load_all_data():
    """Charge toutes les données"""
    global users, telefeed_sessions, telefeed_redirections, telefeed_transformations
    global telefeed_whitelist, telefeed_blacklist, telefeed_settings, telefeed_chats
    
    users = load_json('users.json')
    telefeed_sessions = load_json('telefeed_sessions.json')
    telefeed_redirections = load_json('telefeed_redirections.json')
    telefeed_transformations = load_json('telefeed_transformations.json')
    telefeed_whitelist = load_json('telefeed_whitelist.json')
    telefeed_blacklist = load_json('telefeed_blacklist.json')
    telefeed_settings = load_json('telefeed_settings.json')
    telefeed_chats = load_json('telefeed_chats.json')

def save_all_data():
    """Sauvegarde toutes les données"""
    save_json('users.json', users)
    save_json('telefeed_sessions.json', telefeed_sessions)
    save_json('telefeed_redirections.json', telefeed_redirections)
    save_json('telefeed_transformations.json', telefeed_transformations)
    save_json('telefeed_whitelist.json', telefeed_whitelist)
    save_json('telefeed_blacklist.json', telefeed_blacklist)
    save_json('telefeed_settings.json', telefeed_settings)
    save_json('telefeed_chats.json', telefeed_chats)

def is_user_active(user_id):
    """Vérifie si un utilisateur a une licence active"""
    user_data = users.get(str(user_id))
    if not user_data or user_data.get('status') != 'active':
        return False
    
    expire_date = user_data.get('expires')
    if expire_date:
        expire_datetime = datetime.fromisoformat(expire_date)
        return datetime.now() < expire_datetime
    return False

def activate_user(user_id, plan):
    """Active un utilisateur avec un plan"""
    if plan not in PLANS:
        return False
    
    user_id = str(user_id)
    if user_id not in users:
        users[user_id] = {}
    
    duration = PLANS[plan]['duration']
    expires = datetime.now() + timedelta(days=duration)
    
    users[user_id].update({
        'status': 'active',
        'plan': plan,
        'expires': expires.isoformat(),
        'activated_at': datetime.now().isoformat()
    })
    
    save_all_data()
    return True

def get_user_info(user_id):
    """Récupère les informations d'un utilisateur"""
    return users.get(str(user_id))

def apply_transformations(text, phone_number, redirection_id):
    """Applique les transformations sur le texte"""
    if not text:
        return text
    
    # Format transformation
    format_data = telefeed_transformations.get(phone_number, {}).get(redirection_id, {}).get('format')
    if format_data:
        template = format_data.get('template', '[[Message.Text]]')
        text = template.replace('[[Message.Text]]', text)
    
    # Power transformation
    power_data = telefeed_transformations.get(phone_number, {}).get(redirection_id, {}).get('power')
    if power_data:
        rules = power_data.get('rules', [])
        for rule in rules:
            if '=' in rule:
                pattern, replacement = rule.split('=', 1)
                try:
                    text = re.sub(pattern, replacement, text, flags=re.MULTILINE | re.DOTALL)
                except:
                    pass
            elif '","' in rule:
                rule = rule.strip('"')
                if '","' in rule:
                    old, new = rule.split('","', 1)
                    text = text.replace(old, new)
    
    # Remove lines transformation
    remove_lines_data = telefeed_transformations.get(phone_number, {}).get(redirection_id, {}).get('removeLines')
    if remove_lines_data:
        keywords = remove_lines_data.get('keywords', [])
        lines = text.split('\n')
        filtered_lines = []
        
        for line in lines:
            should_remove = False
            for keyword in keywords:
                if keyword in line:
                    should_remove = True
                    break
            if not should_remove:
                filtered_lines.append(line)
        
        text = '\n'.join(filtered_lines)
    
    return text

def should_process_message(text, phone_number, redirection_id):
    """Vérifie si le message doit être traité"""
    # Vérifier la blacklist
    blacklist_data = telefeed_blacklist.get(phone_number, {}).get(redirection_id, {})
    if blacklist_data and blacklist_data.get('active', False):
        patterns = blacklist_data.get('patterns', [])
        for pattern in patterns:
            if isinstance(pattern, str):
                if pattern.startswith('"') and pattern.endswith('"'):
                    if pattern[1:-1] in text:
                        return False
                else:
                    try:
                        if re.search(pattern, text, re.MULTILINE | re.DOTALL):
                            return False
                    except:
                        pass
    
    # Vérifier la whitelist
    whitelist_data = telefeed_whitelist.get(phone_number, {}).get(redirection_id, {})
    if whitelist_data and whitelist_data.get('active', False):
        patterns = whitelist_data.get('patterns', [])
        if patterns:
            for pattern in patterns:
                if isinstance(pattern, str):
                    if pattern.startswith('"') and pattern.endswith('"'):
                        if pattern[1:-1] in text:
                            return True
                    else:
                        try:
                            if re.search(pattern, text, re.MULTILINE | re.DOTALL):
                                return True
                        except:
                            pass
            return False
    
    return True

# Créer le client bot
bot = TelegramClient('telefeed_bot', API_ID, API_HASH)

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Commande /start"""
    user_id = str(event.sender_id)
    
    if user_id not in users:
        users[user_id] = {
            'status': 'waiting',
            'registered_at': datetime.now().isoformat()
        }
        save_all_data()
    
    welcome_message = (
        "🚀 **Bienvenue sur Téléfoot Enhanced !**\n\n"
        "🎯 **Fonctionnalités :**\n"
        "• Pronostics football quotidiens\n"
        "• Système TeleFeed complet\n"
        "• Redirection de messages\n"
        "• Transformations avancées\n\n"
        "💰 **Tarifs :**\n"
        "• 1 semaine = 1000f\n"
        "• 1 mois = 3000f\n\n"
        "📞 **Contact :** @SossouKouame\n"
        "🔑 **Commandes :** /help"
    )
    
    await event.reply(welcome_message, parse_mode='markdown')

@bot.on(events.NewMessage(pattern='/help'))
async def help_handler(event):
    """Commande /help"""
    help_message = (
        "🤖 **Commandes disponibles :**\n\n"
        "**📋 Général :**\n"
        "• /start - Démarrer le bot\n"
        "• /status - Voir votre statut\n"
        "• /help - Afficher cette aide\n\n"
        "**🚀 TeleFeed (Utilisateurs actifs) :**\n"
        "• /connect <numéro> - Connecter un compte\n"
        "• /chats <numéro> - Voir les chats\n"
        "• /redirection add <nom> on <numéro> - Ajouter redirection\n"
        "• /redirection remove <nom> on <numéro> - Supprimer\n"
        "• /redirection <numéro> - Lister les redirections\n"
        "• /transformation add <type> <nom> on <numéro> - Transformer\n"
        "• /whitelist add <nom> on <numéro> - Filtrer\n"
        "• /blacklist add <nom> on <numéro> - Bloquer\n\n"
        "**💡 Exemple complet :**\n"
        "1. `/connect 33123456789`\n"
        "2. `aa12345` (code reçu)\n"
        "3. `/chats 33123456789`\n"
        "4. `/redirection add test on 33123456789`\n"
        "5. `123456789 - 987654321`\n\n"
        "**📞 Support :** @SossouKouame"
    )
    
    await event.reply(help_message, parse_mode='markdown')

@bot.on(events.NewMessage(pattern='/status'))
async def status_handler(event):
    """Commande /status"""
    user_id = str(event.sender_id)
    
    if event.sender_id == ADMIN_ID:
        parts = event.raw_text.split()
        if len(parts) == 2:
            target_user_id = parts[1]
            user_info = get_user_info(target_user_id)
            if user_info:
                active = "✅ Actif" if is_user_active(target_user_id) else "❌ Expiré"
                message = (
                    f"📊 **Utilisateur {target_user_id}**\n"
                    f"🔄 Statut : {active}\n"
                    f"📋 Plan : {user_info.get('plan', 'N/A')}\n"
                    f"⏰ Expire : {user_info.get('expires', 'N/A')}\n"
                    f"📅 Activé : {user_info.get('activated_at', 'N/A')}"
                )
                await event.reply(message, parse_mode='markdown')
            else:
                await event.reply("❌ Utilisateur non trouvé")
            return
    
    # Statut personnel
    user_info = get_user_info(user_id)
    if not user_info:
        await event.reply("❌ Vous n'êtes pas enregistré. Contactez l'administrateur.")
        return
    
    active = "✅ Actif" if is_user_active(user_id) else "❌ Expiré"
    message = (
        f"📊 **Votre statut**\n"
        f"🔄 Statut : {active}\n"
        f"📋 Plan : {user_info.get('plan', 'N/A')}\n"
        f"⏰ Expire : {user_info.get('expires', 'N/A')}\n"
        f"📅 Activé : {user_info.get('activated_at', 'N/A')}"
    )
    
    await event.reply(message, parse_mode='markdown')

@bot.on(events.NewMessage(pattern=r'/activer (\w+) (\w+)'))
async def activer_handler(event):
    """Commande /activer (admin seulement)"""
    if event.sender_id != ADMIN_ID:
        await event.reply("❌ Commande réservée aux administrateurs")
        return
    
    user_id = event.pattern_match.group(1)
    plan = event.pattern_match.group(2)
    
    if plan not in PLANS:
        await event.reply("❌ Plan invalide. Utilisez: weekly ou monthly")
        return
    
    if activate_user(user_id, plan):
        duration = PLANS[plan]['duration']
        price = PLANS[plan]['price']
        
        await event.reply(
            f"✅ **Utilisateur {user_id} activé !**\n"
            f"📋 Plan : {plan}\n"
            f"⏰ Durée : {duration} jours\n"
            f"💰 Prix : {price}f"
        )
        
        # Notifier l'utilisateur
        try:
            await bot.send_message(
                int(user_id),
                f"🎉 **Votre licence a été activée !**\n"
                f"📋 Plan : {plan}\n"
                f"⏰ Durée : {duration} jours\n"
                f"🚀 Vous avez maintenant accès à toutes les fonctionnalités TeleFeed !"
            )
        except:
            pass
    else:
        await event.reply("❌ Erreur lors de l'activation")

@bot.on(events.NewMessage(pattern=r'/connect (\d+)'))
async def connect_handler(event):
    """Commande /connect"""
    if not is_user_active(event.sender_id):
        await event.reply("❌ Vous devez avoir une licence active pour utiliser TeleFeed.")
        return
    
    phone_number = event.pattern_match.group(1)
    
    await event.reply("🔌 Connexion en cours...")
    
    try:
        session_name = f"telefeed_{phone_number}"
        client = TelegramClient(session_name, API_ID, API_HASH)
        
        await client.connect()
        
        if not await client.is_user_authorized():
            result = await client.send_code_request(phone_number)
            
            # Stocker temporairement
            pending_connections[event.sender_id] = {
                'phone_number': phone_number,
                'phone_code_hash': result.phone_code_hash,
                'client': client
            }
            
            await event.reply(
                f"📱 Code envoyé à {phone_number}\n"
                f"💡 Répondez avec: aa + votre code\n"
                f"📝 Exemple: aa12345"
            )
        else:
            telefeed_clients[phone_number] = client
            telefeed_sessions[phone_number] = {
                'connected': True,
                'connected_at': datetime.now().isoformat()
            }
            save_all_data()
            await event.reply(f"✅ Compte {phone_number} connecté avec succès!")
            
    except Exception as e:
        await event.reply(f"❌ Erreur: {str(e)}")

@bot.on(events.NewMessage(pattern=r'^aa(\d+)$'))
async def verify_code_handler(event):
    """Vérification du code TeleFeed"""
    if not is_user_active(event.sender_id):
        return
    
    if event.sender_id not in pending_connections:
        await event.reply("❌ Aucune connexion en attente.")
        return
    
    code = event.pattern_match.group(1)
    connection_data = pending_connections[event.sender_id]
    
    try:
        await connection_data['client'].sign_in(
            connection_data['phone_number'],
            code,
            phone_code_hash=connection_data['phone_code_hash']
        )
        
        phone_number = connection_data['phone_number']
        telefeed_clients[phone_number] = connection_data['client']
        telefeed_sessions[phone_number] = {
            'connected': True,
            'connected_at': datetime.now().isoformat()
        }
        save_all_data()
        
        del pending_connections[event.sender_id]
        
        await event.reply(f"✅ Compte {phone_number} connecté avec succès!")
        
    except SessionPasswordNeededError:
        await event.reply("🔐 Authentification 2FA requise. Envoyez votre mot de passe.")
    except Exception as e:
        await event.reply(f"❌ Erreur: {str(e)}")

@bot.on(events.NewMessage(pattern=r'/chats (\d+)'))
async def chats_handler(event):
    """Commande /chats"""
    if not is_user_active(event.sender_id):
        await event.reply("❌ Vous devez avoir une licence active pour utiliser TeleFeed.")
        return
    
    phone_number = event.pattern_match.group(1)
    
    if phone_number not in telefeed_clients:
        await event.reply(f"❌ Compte {phone_number} non connecté. Utilisez /connect {phone_number}")
        return
    
    await event.reply("📋 Récupération des chats...")
    
    try:
        client = telefeed_clients[phone_number]
        chats = []
        
        async for dialog in client.iter_dialogs(limit=50):
            chat_type = 'unknown'
            if isinstance(dialog.entity, User):
                chat_type = 'user'
            elif isinstance(dialog.entity, Chat):
                chat_type = 'group'
            elif isinstance(dialog.entity, Channel):
                chat_type = 'channel' if dialog.entity.broadcast else 'supergroup'
            
            chats.append({
                'id': dialog.id,
                'title': dialog.title or dialog.name,
                'type': chat_type
            })
        
        if not chats:
            await event.reply("📭 Aucun chat trouvé.")
            return
        
        # Sauvegarder
        telefeed_chats[phone_number] = chats
        save_all_data()
        
        message = "📋 **Chats disponibles:**\n\n"
        for chat in chats[:15]:  # Limiter à 15 chats
            emoji = "👤" if chat['type'] == 'user' else "👥" if chat['type'] == 'group' else "📢"
            message += f"{emoji} `{chat['id']}` - {chat['title']} ({chat['type']})\n"
        
        if len(chats) > 15:
            message += f"\n... et {len(chats) - 15} autres chats"
        
        await event.reply(message, parse_mode='markdown')
        
    except Exception as e:
        await event.reply(f"❌ Erreur: {str(e)}")

@bot.on(events.NewMessage(pattern=r'/redirection add (\w+) on (\d+)'))
async def add_redirection_handler(event):
    """Commande /redirection add"""
    if not is_user_active(event.sender_id):
        await event.reply("❌ Vous devez avoir une licence active pour utiliser TeleFeed.")
        return
    
    redirection_id = event.pattern_match.group(1)
    phone_number = event.pattern_match.group(2)
    
    await event.reply(
        f"🔄 Configuration de la redirection **{redirection_id}**\n\n"
        f"📝 Envoyez maintenant les IDs au format:\n"
        f"**SOURCE - DESTINATION**\n\n"
        f"📋 Exemples:\n"
        f"• `123456789 - 987654321`\n"
        f"• `123,456 - 789,012`\n"
        f"• Utilisez /chats {phone_number} pour voir les IDs",
        parse_mode='markdown'
    )
    
    # Attendre la réponse
    def check_response(new_event):
        return (new_event.sender_id == event.sender_id and 
                new_event.chat_id == event.chat_id and 
                ' - ' in new_event.raw_text)
    
    try:
        response = await bot.wait_for(events.NewMessage(func=check_response), timeout=60)
        
        # Parser la réponse
        parts = response.raw_text.split(' - ')
        if len(parts) != 2:
            await event.reply("❌ Format invalide. Utilisez: SOURCE - DESTINATION")
            return
        
        sources = [int(x.strip()) for x in parts[0].split(',')]
        destinations = [int(x.strip()) for x in parts[1].split(',')]
        
        # Ajouter la redirection
        if phone_number not in telefeed_redirections:
            telefeed_redirections[phone_number] = {}
        
        telefeed_redirections[phone_number][redirection_id] = {
            'sources': sources,
            'destinations': destinations,
            'created_at': datetime.now().isoformat(),
            'active': True
        }
        
        # Paramètres par défaut
        if phone_number not in telefeed_settings:
            telefeed_settings[phone_number] = {}
        
        telefeed_settings[phone_number][redirection_id] = {
            'process_reply': True,
            'process_edit': True,
            'process_delete': True,
            'process_me': False,
            'process_forward': False,
            'process_raw': False,
            'process_duplicates': True,
            'delay_spread_mode': False
        }
        
        save_all_data()
        await event.reply(f"✅ Redirection **{redirection_id}** créée avec succès!")
        
    except asyncio.TimeoutError:
        await event.reply("⏰ Timeout. Recommencez la configuration.")
    except ValueError:
        await event.reply("❌ IDs invalides. Utilisez uniquement des nombres.")

@bot.on(events.NewMessage(pattern=r'/redirection remove (\w+) on (\d+)'))
async def remove_redirection_handler(event):
    """Commande /redirection remove"""
    if not is_user_active(event.sender_id):
        await event.reply("❌ Vous devez avoir une licence active pour utiliser TeleFeed.")
        return
    
    redirection_id = event.pattern_match.group(1)
    phone_number = event.pattern_match.group(2)
    
    if (phone_number in telefeed_redirections and 
        redirection_id in telefeed_redirections[phone_number]):
        del telefeed_redirections[phone_number][redirection_id]
        
        if (phone_number in telefeed_settings and 
            redirection_id in telefeed_settings[phone_number]):
            del telefeed_settings[phone_number][redirection_id]
        
        save_all_data()
        await event.reply(f"✅ Redirection **{redirection_id}** supprimée.")
    else:
        await event.reply("❌ Redirection non trouvée.")

@bot.on(events.NewMessage(pattern=r'/redirection (\d+)'))
async def list_redirections_handler(event):
    """Commande /redirection (lister)"""
    if not is_user_active(event.sender_id):
        await event.reply("❌ Vous devez avoir une licence active pour utiliser TeleFeed.")
        return
    
    phone_number = event.pattern_match.group(1)
    
    redirections = telefeed_redirections.get(phone_number, {})
    
    if not redirections:
        await event.reply(f"📭 Aucune redirection active pour {phone_number}")
        return
    
    message = f"🔄 **Redirections actives pour {phone_number}:**\n\n"
    
    for redir_id, data in redirections.items():
        status = "✅" if data.get('active', True) else "❌"
        sources = ', '.join(map(str, data.get('sources', [])))
        destinations = ', '.join(map(str, data.get('destinations', [])))
        
        message += f"{status} **{redir_id}**\n"
        message += f"📤 Sources: `{sources}`\n"
        message += f"📥 Destinations: `{destinations}`\n\n"
    
    await event.reply(message, parse_mode='markdown')

@bot.on(events.NewMessage(pattern=r'/transformation add (\w+) (\w+) on (\d+)'))
async def add_transformation_handler(event):
    """Commande /transformation add"""
    if not is_user_active(event.sender_id):
        await event.reply("❌ Vous devez avoir une licence active pour utiliser TeleFeed.")
        return
    
    feature = event.pattern_match.group(1)
    redirection_id = event.pattern_match.group(2)
    phone_number = event.pattern_match.group(3)
    
    if feature not in ['format', 'power', 'removeLines']:
        await event.reply("❌ Fonctionnalité non supportée. Utilisez: format, power, removeLines")
        return
    
    await event.reply(
        f"⚙️ Configuration de la transformation **{feature}** pour **{redirection_id}**\n\n"
        f"📝 Envoyez maintenant votre configuration:"
    )
    
    # Attendre la réponse
    def check_response(new_event):
        return (new_event.sender_id == event.sender_id and 
                new_event.chat_id == event.chat_id)
    
    try:
        response = await bot.wait_for(events.NewMessage(func=check_response), timeout=120)
        
        # Initialiser la structure
        if phone_number not in telefeed_transformations:
            telefeed_transformations[phone_number] = {}
        if redirection_id not in telefeed_transformations[phone_number]:
            telefeed_transformations[phone_number][redirection_id] = {}
        
        # Configurer selon le type
        if feature == 'format':
            telefeed_transformations[phone_number][redirection_id]['format'] = {
                'template': response.raw_text,
                'active': True
            }
        elif feature == 'power':
            rules = response.raw_text.split('\n')
            telefeed_transformations[phone_number][redirection_id]['power'] = {
                'rules': rules,
                'active': True
            }
        elif feature == 'removeLines':
            keywords = [k.strip() for k in response.raw_text.split(',')]
            telefeed_transformations[phone_number][redirection_id]['removeLines'] = {
                'keywords': keywords,
                'active': True
            }
        
        save_all_data()
        await event.reply(f"✅ Transformation **{feature}** configurée pour **{redirection_id}**!")
        
    except asyncio.TimeoutError:
        await event.reply("⏰ Timeout. Recommencez la configuration.")

@bot.on(events.NewMessage(pattern=r'/whitelist add (\w+) on (\d+)'))
async def add_whitelist_handler(event):
    """Commande /whitelist add"""
    if not is_user_active(event.sender_id):
        await event.reply("❌ Vous devez avoir une licence active pour utiliser TeleFeed.")
        return
    
    redirection_id = event.pattern_match.group(1)
    phone_number = event.pattern_match.group(2)
    
    await event.reply(
        f"⚪ Configuration de la whitelist pour **{redirection_id}**\n\n"
        f"📝 Envoyez les mots-clés (un par ligne):"
    )
    
    def check_response(new_event):
        return (new_event.sender_id == event.sender_id and 
                new_event.chat_id == event.chat_id)
    
    try:
        response = await bot.wait_for(events.NewMessage(func=check_response), timeout=60)
        
        patterns = response.raw_text.split('\n')
        
        if phone_number not in telefeed_whitelist:
            telefeed_whitelist[phone_number] = {}
        
        telefeed_whitelist[phone_number][redirection_id] = {
            'patterns': patterns,
            'active': True
        }
        
        save_all_data()
        await event.reply(f"✅ Whitelist configurée pour **{redirection_id}**!")
        
    except asyncio.TimeoutError:
        await event.reply("⏰ Timeout. Recommencez la configuration.")

@bot.on(events.NewMessage(pattern=r'/blacklist add (\w+) on (\d+)'))
async def add_blacklist_handler(event):
    """Commande /blacklist add"""
    if not is_user_active(event.sender_id):
        await event.reply("❌ Vous devez avoir une licence active pour utiliser TeleFeed.")
        return
    
    redirection_id = event.pattern_match.group(1)
    phone_number = event.pattern_match.group(2)
    
    await event.reply(
        f"⚫ Configuration de la blacklist pour **{redirection_id}**\n\n"
        f"📝 Envoyez les mots-clés à bloquer (un par ligne):"
    )
    
    def check_response(new_event):
        return (new_event.sender_id == event.sender_id and 
                new_event.chat_id == event.chat_id)
    
    try:
        response = await bot.wait_for(events.NewMessage(func=check_response), timeout=60)
        
        patterns = response.raw_text.split('\n')
        
        if phone_number not in telefeed_blacklist:
            telefeed_blacklist[phone_number] = {}
        
        telefeed_blacklist[phone_number][redirection_id] = {
            'patterns': patterns,
            'active': True
        }
        
        save_all_data()
        await event.reply(f"✅ Blacklist configurée pour **{redirection_id}**!")
        
    except asyncio.TimeoutError:
        await event.reply("⏰ Timeout. Recommencez la configuration.")

@bot.on(events.NewMessage(pattern='/pronostics'))
async def pronostics_handler(event):
    """Commande /pronostics"""
    if not is_user_active(event.sender_id):
        await event.reply("❌ Vous devez avoir une licence active pour voir les pronostics.")
        return
    
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

# Handler pour les messages redirigés
@bot.on(events.NewMessage)
async def handle_message_redirection(event):
    """Gestionnaire principal pour les redirections"""
    # Vérifier tous les comptes connectés
    for phone_number, client in telefeed_clients.items():
        if client == event.client:
            # Vérifier les redirections pour ce numéro
            redirections = telefeed_redirections.get(phone_number, {})
            
            for redir_id, redir_data in redirections.items():
                if not redir_data.get('active', True):
                    continue
                
                # Vérifier si ce chat est dans les sources
                if event.chat_id in redir_data.get('sources', []):
                    text = event.raw_text or ''
                    
                    # Vérifier les filtres
                    if not should_process_message(text, phone_number, redir_id):
                        continue
                    
                    # Appliquer les transformations
                    processed_text = apply_transformations(text, phone_number, redir_id)
                    
                    # Envoyer vers les destinations
                    for dest_id in redir_data.get('destinations', []):
                        try:
                            await client.send_message(dest_id, processed_text)
                        except Exception as e:
                            print(f"Erreur lors de l'envoi vers {dest_id}: {e}")

async def main():
    """Fonction principale"""
    print("🚀 Téléfoot Enhanced - Chargement...")
    
    # Charger les données
    load_all_data()
    
    # Démarrer le bot
    await bot.start(bot_token=BOT_TOKEN)
    
    # Vérifier la connexion
    me = await bot.get_me()
    print(f"🤖 Bot connecté : @{me.username}")
    
    print("✅ Téléfoot Enhanced démarré avec succès!")
    print("🚀 Fonctionnalités TeleFeed activées")
    print("📱 En attente de messages...")
    
    # Boucle principale
    try:
        await bot.run_until_disconnected()
    except KeyboardInterrupt:
        print("\n⏹️  Arrêt du bot demandé")
    except Exception as e:
        print(f"❌ Erreur: {e}")
    finally:
        # Nettoyer les clients
        for client in telefeed_clients.values():
            await client.disconnect()
        print("🔌 Clients déconnectés")

if __name__ == "__main__":
    asyncio.run(main())