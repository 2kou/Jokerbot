#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot Telegram Téléfoot Avancé avec système de redirection et gestion de licences
"""

from telethon.sync import TelegramClient
from telethon import events
import json, time, re
from datetime import datetime, timedelta
import asyncio
import os

# Configuration
api_id = int(os.getenv('API_ID', '29177661'))
api_hash = os.getenv('API_HASH', 'a8639172fa8d35dbfd8ea46286d349ab')
BOT_TOKEN = os.getenv('BOT_TOKEN', '7573497633:AAHk9K15yTCiJP-zruJrc9v8eK8I9XhjyH4')
ADMIN_ID = int(os.getenv('ADMIN_ID', '1190237801'))

# ========== BASE UTILS ==========

def load_json(file):
    """Charge un fichier JSON"""
    try:
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_json(file, data):
    """Sauvegarde des données dans un fichier JSON"""
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ========== 1. CONNECT ==========

async def connect_account(phone_number):
    """Connecte un compte utilisateur avec délai d'expiration de 30 secondes"""
    from telethon.errors import FloodWaitError, PhoneNumberInvalidError
    from telethon.tl.functions.auth import SendCodeRequest
    from telethon.tl.types import CodeSettings
    import time
    
    client = TelegramClient(f'session_{phone_number}', api_id, api_hash)
    
    try:
        await client.connect()
        
        if await client.is_user_authorized():
            print(f"✅ Compte {phone_number} déjà connecté")
            return client, "already_connected"
        
        # Configuration personnalisée du code avec délai étendu
        code_settings = CodeSettings(
            allow_flashcall=False,
            current_number=False,
            allow_app_hash=False,
            allow_missed_call=False,
            logout_tokens=None
        )
        
        # Demander le code avec paramètres personnalisés
        code_request = await client(SendCodeRequest(
            phone_number=phone_number,
            api_id=api_id,
            api_hash=api_hash,
            settings=code_settings
        ))
        
        # Enregistrer le timestamp pour tracking
        timestamp = int(time.time())
        
        print(f"📱 Code envoyé au {phone_number}")
        print(f"🔢 Hash du code : {code_request.phone_code_hash}")
        print(f"⏰ Timestamp : {timestamp}")
        
        return client, "code_requested", code_request.phone_code_hash, timestamp
        
    except PhoneNumberInvalidError:
        print(f"❌ Numéro de téléphone invalide : {phone_number}")
        return None, "invalid_phone", None
    except FloodWaitError as e:
        print(f"❌ Limite de taux atteinte, attendre {e.seconds} secondes")
        return None, "flood_wait", e.seconds
    except Exception as e:
        print(f"❌ Erreur de connexion : {e}")
        return None, "error", str(e)

async def complete_auth(client, phone_number, code, phone_code_hash, password=None):
    """Complète l'authentification avec hash du code"""
    from telethon.errors import (
        PhoneCodeExpiredError, PhoneCodeInvalidError, 
        SessionPasswordNeededError, FloodWaitError
    )
    
    try:
        # Utiliser le hash pour éviter l'expiration
        if password:
            await client.sign_in(phone_number, code, password=password, phone_code_hash=phone_code_hash)
        else:
            await client.sign_in(phone_number, code, phone_code_hash=phone_code_hash)
        
        print(f"✅ Authentification réussie pour {phone_number}")
        return True, "success", None
        
    except PhoneCodeExpiredError:
        print("❌ Le code a expiré. Demandez un nouveau code.")
        return False, "expired", "Code expiré"
    except PhoneCodeInvalidError:
        print("❌ Code incorrect.")
        return False, "invalid_code", "Code incorrect"
    except SessionPasswordNeededError:
        print("🔐 Mot de passe requis (2FA activé)")
        return False, "password_needed", "Mot de passe 2FA requis"
    except FloodWaitError as e:
        print(f"❌ Limite de taux, attendre {e.seconds} secondes")
        return False, "flood_wait", f"Attendre {e.seconds} secondes"
    except Exception as e:
        print(f"❌ Erreur d'authentification : {e}")
        return False, "error", str(e)

# ========== 2. REDIRECTION ==========

def add_redirection(name, session, sources, destinations):
    """Ajoute une redirection de canaux"""
    data = load_json("redirections.json")
    data[name] = {
        "session": session,
        "sources": sources,
        "destinations": destinations,
        "settings": {
            "edit": True,
            "delete": True
        }
    }
    save_json("redirections.json", data)
    print(f"✅ Redirection '{name}' ajoutée")

# ========== 12. LICENCE SYSTEM ==========

def is_user_active(user_id):
    """Vérifie si un utilisateur a une licence active"""
    db = load_json("users.json")
    user = db.get(str(user_id))
    if not user: 
        return False
    try:
        expire_date = datetime.strptime(user["expire_at"], "%Y-%m-%d %H:%M:%S")
        return datetime.now() < expire_date
    except:
        return False

def activate_user(user_id, duration):
    """Active un utilisateur avec une durée donnée"""
    db = load_json("users.json")
    days = 7 if duration == "semaine" else 30
    expire = datetime.now() + timedelta(days=days)
    db[str(user_id)] = {
        "expire_at": expire.strftime("%Y-%m-%d %H:%M:%S"),
        "activated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "plan": duration
    }
    save_json("users.json", db)
    return expire.strftime("%d/%m/%Y %H:%M")

def get_user_info(user_id):
    """Récupère les informations d'un utilisateur"""
    db = load_json("users.json")
    return db.get(str(user_id))

# ========== FILTERS & TRANSFORMS ==========

def should_ignore(event, redir_name):
    """Vérifie si un message doit être ignoré"""
    filters = load_json("filters.json")
    ignored = filters.get(redir_name, {}).get("ignore", [])
    if event.photo and "photo" in ignored: return True
    if event.audio and "audio" in ignored: return True
    if event.video and "video" in ignored: return True
    if event.text and "text" in ignored: return True
    return False

def clean_message(event, redir_name):
    """Nettoie un message selon les règles"""
    cleaner = load_json("cleaner.json")
    remove = cleaner.get(redir_name, {}).get("remove", [])
    msg = event.message.to_dict()
    if "caption" in remove: msg["message"] = ""
    if "text" in remove and event.text: msg["message"] = ""
    return msg

def transform_format(text, redir_name):
    """Transforme le format d'un message"""
    formats = load_json("format.json")
    tpl = formats.get(redir_name, {}).get("template", "[[Message.Text]]")
    return tpl.replace("[[Message.Text]]", text)

def transform_power(text, redir_name):
    """Applique des transformations regex"""
    powers = load_json("power.json")
    rules = powers.get(redir_name, [])
    for rule in rules:
        if len(rule) >= 2:
            search, replace = rule[0], rule[1]
            text = re.sub(search, replace, text)
    return text

def transform_removelines(text, redir_name):
    """Supprime des lignes selon les règles"""
    rules = load_json("removeLines.json").get(redir_name, [])
    lines = text.split("\n")
    return "\n".join(line for line in lines if not any(k in line for k in rules))

def match_whitelist(text, redir_name):
    """Vérifie si le texte correspond à la whitelist"""
    whitelist = load_json("whitelist.json")
    rules = whitelist.get(redir_name, [])
    if not rules: return True  # Si pas de whitelist, on autorise
    return any(re.search(r, text, re.IGNORECASE) for r in rules)

def match_blacklist(text, redir_name):
    """Vérifie si le texte correspond à la blacklist"""
    blacklist = load_json("blacklist.json")
    rules = blacklist.get(redir_name, [])
    return any(re.search(r, text, re.IGNORECASE) for r in rules)

# ========== DELAY SYSTEM ==========

last_sent = {}

def can_send(redir_name, delay_secs):
    """Vérifie si on peut envoyer un message (système de délai)"""
    now = time.time()
    if redir_name not in last_sent or now - last_sent[redir_name] >= delay_secs:
        last_sent[redir_name] = now
        return True
    return False

# ========== INITIALISATION BOT ==========

print("🤖 Initialisation du bot Téléfoot Avancé...")

try:
    # Création du client bot
    bot = TelegramClient('telefoot_bot', api_id, api_hash).start(bot_token=BOT_TOKEN)
    print("✅ Bot connecté avec succès")
except Exception as e:
    print(f"❌ Erreur de connexion du bot : {e}")
    exit(1)

# Variables globales pour gérer les connexions en cours
pending_connections = {}

# ========== BOT HANDLERS ==========

@bot.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    """Handler pour la commande /start"""
    user_id = str(event.sender_id)
    
    # Accès automatique pour l'admin
    if event.sender_id == ADMIN_ID:
        await event.reply(
            "👑 *ACCÈS ADMINISTRATEUR*\n"
            "✅ Bienvenue Boss ! Accès total activé.\n\n"
            "🔧 *Commandes disponibles :*\n"
            "/activer - Activer des utilisateurs\n"
            "/status - Voir le statut des utilisateurs\n"
            "/redirections - Gérer les redirections\n"
            "/pronostics - Voir les pronostics\n"
            "/help - Aide complète",
            parse_mode="markdown"
        )
        return
    
    # Vérification pour les autres utilisateurs
    if not is_user_active(user_id):
        await event.reply(
            "⛔ *Accès requis pour utiliser Téléfoot*\n\n"
            "📱 *Services disponibles :*\n"
            "• Pronostics quotidiens\n"
            "• Analyses VIP\n"
            "• Statistiques détaillées\n"
            "• Redirections de canaux\n\n"
            "💰 *Tarifs :*\n"
            "• 1 semaine = 1000f\n"
            "• 1 mois = 3000f\n\n"
            "📞 Contactez *Sossou Kouamé* pour l'activation",
            parse_mode="markdown"
        )
        return
    
    await event.reply(
        "✅ *Bienvenue sur Téléfoot !*\n\n"
        "🎯 *Services actifs :*\n"
        "/pronostics - Pronostics du jour\n"
        "/vip - Analyses VIP\n"
        "/statistiques - Performance\n"
        "/matchs - Programme\n"
        "/redirections - Gérer vos redirections\n"
        "/help - Aide complète",
        parse_mode="markdown"
    )

@bot.on(events.NewMessage(pattern="/activer"))
async def activer_handler(event):
    """Handler pour activer des utilisateurs"""
    if event.sender_id != ADMIN_ID:
        return await event.reply("⛔ Seul l'administrateur peut activer des comptes.")
    
    parts = event.raw_text.split()
    if len(parts) != 3:
        return await event.reply(
            "❌ *Utilisation :* `/activer <user_id> <semaine|mois>`\n"
            "*Exemple :* `/activer 123456789 semaine`",
            parse_mode="markdown"
        )
    
    user_id = parts[1]
    duration = parts[2]
    
    if duration not in ["semaine", "mois"]:
        return await event.reply("⛔ Durée invalide. Choisir : semaine ou mois.")
    
    try:
        expire = activate_user(user_id, duration)
        await event.respond(f"✅ Utilisateur {user_id} activé jusqu'au {expire}")
        
        # Notification à l'utilisateur
        try:
            await bot.send_message(
                int(user_id), 
                f"🎉 *Votre accès Téléfoot a été activé !*\n"
                f"⏰ Expire le : *{expire}*\n"
                f"📋 Plan : *{duration}*\n\n"
                f"Utilisez /start pour commencer !",
                parse_mode="markdown"
            )
        except:
            pass
            
    except Exception as e:
        await event.reply(f"❌ Erreur lors de l'activation : {e}")

@bot.on(events.NewMessage(pattern="/status"))
async def status_handler(event):
    """Handler pour voir le statut"""
    user_id = str(event.sender_id)
    
    # Admin peut voir le statut d'autres utilisateurs
    if event.sender_id == ADMIN_ID:
        parts = event.raw_text.split()
        if len(parts) == 2:
            target_user = parts[1]
            user_info = get_user_info(target_user)
            if user_info:
                active = "✅ Actif" if is_user_active(target_user) else "❌ Expiré"
                await event.reply(
                    f"📊 *Statut utilisateur {target_user}*\n"
                    f"🔄 Statut : {active}\n"
                    f"📋 Plan : {user_info.get('plan', 'N/A')}\n"
                    f"⏰ Expire : {user_info.get('expire_at', 'N/A')}\n"
                    f"📅 Activé : {user_info.get('activated_at', 'N/A')}",
                    parse_mode="markdown"
                )
            else:
                await event.reply("❌ Utilisateur non trouvé")
            return
    
    # Statut personnel
    user_info = get_user_info(user_id)
    if not user_info:
        await event.reply("❌ Vous n'êtes pas enregistré. Contactez l'administrateur.")
        return
    
    active = "✅ Actif" if is_user_active(user_id) else "❌ Expiré"
    await event.reply(
        f"📊 *Votre statut Téléfoot*\n"
        f"🔄 Statut : {active}\n"
        f"📋 Plan : {user_info.get('plan', 'N/A')}\n"
        f"⏰ Expire : {user_info.get('expire_at', 'N/A')}",
        parse_mode="markdown"
    )

@bot.on(events.NewMessage(pattern="/pronostics"))
async def pronostics_handler(event):
    """Handler pour les pronostics"""
    user_id = str(event.sender_id)
    
    if event.sender_id != ADMIN_ID and not is_user_active(user_id):
        await event.reply("⛔ Accès requis. Contactez l'administrateur.")
        return
    
    pronostics = (
        "🎯 *PRONOSTICS TÉLÉFOOT DU JOUR*\n\n"
        "⚽ **SÉLECTIONS PREMIUM** ⚽\n\n"
        
        "🏆 *Ligue 1 Française*\n"
        "• PSG vs Lyon - **1** (Victoire PSG) - Cote: 1.85 ⭐\n"
        "• Marseille vs Nice - **X** (Match nul) - Cote: 3.20\n"
        "• Monaco vs Rennes - **Plus de 2.5 buts** - Cote: 1.75\n\n"
        
        "🏆 *Premier League*\n"
        "• Man City vs Arsenal - **1** (Victoire City) - Cote: 2.10 🔥\n"
        "• Chelsea vs Liverpool - **2** (Victoire Liverpool) - Cote: 2.75\n"
        "• Tottenham vs Newcastle - **Plus de 1.5 buts** - Cote: 1.45\n\n"
        
        "🏆 *Liga Espagnole*\n"
        "• Real Madrid vs Barcelona - **1** (Victoire Real) - Cote: 2.45 ⚡\n"
        "• Atletico vs Sevilla - **Plus de 2.5 buts** - Cote: 1.95\n"
        "• Valencia vs Villarreal - **X2** (Nul ou Villarreal) - Cote: 1.65\n\n"
        
        "💎 **COMBO SÛRE DU JOUR**\n"
        "PSG Victoire + Man City Victoire + Plus de 1.5 buts Real-Barca\n"
        "**Cote combinée: 7.85** 🚀\n\n"
        
        "📊 *Performance* : 78% de réussite cette semaine\n"
        "💰 *Conseil* : Mise recommandée 2-5% de votre bankroll\n"
        "⏰ *Mise à jour* : " + datetime.now().strftime("%d/%m/%Y %H:%M")
    )
    
    await event.reply(pronostics, parse_mode="markdown")

@bot.on(events.NewMessage(pattern="/redirections"))
async def redirections_handler(event):
    """Handler pour gérer les redirections"""
    user_id = str(event.sender_id)
    
    if event.sender_id != ADMIN_ID and not is_user_active(user_id):
        await event.reply("⛔ Accès requis pour gérer les redirections.")
        return
    
    redirections = load_json("redirections.json")
    
    if not redirections:
        await event.reply(
            "📋 *Aucune redirection configurée*\n\n"
            "Pour ajouter une redirection :\n"
            "1. Utilisez la fonction `add_redirection()`\n"
            "2. Configurez vos canaux sources et destinations\n"
            "3. Relancez le bot",
            parse_mode="markdown"
        )
        return
    
    msg = "📋 *Redirections actives :*\n\n"
    for name, config in redirections.items():
        sources = len(config.get("sources", []))
        destinations = len(config.get("destinations", []))
        msg += f"• **{name}**\n"
        msg += f"  Sources: {sources} canaux\n"
        msg += f"  Destinations: {destinations} canaux\n"
        msg += f"  Édition: {'✅' if config.get('settings', {}).get('edit') else '❌'}\n"
        msg += f"  Suppression: {'✅' if config.get('settings', {}).get('delete') else '❌'}\n\n"
    
    await event.reply(msg, parse_mode="markdown")

@bot.on(events.NewMessage(pattern="/help"))
async def help_handler(event):
    """Handler pour l'aide"""
    user_id = str(event.sender_id)
    
    help_msg = (
        "🤖 *TÉLÉFOOT - GUIDE COMPLET*\n\n"
        
        "📱 **Commandes Utilisateur :**\n"
        "/start - Démarrer le bot\n"
        "/pronostics - Pronostics du jour\n"
        "/status - Votre statut d'abonnement\n"
        "/redirections - Vos redirections actives\n"
        "/help - Cette aide\n\n"
        
        "💰 **Tarifs :**\n"
        "• 1 semaine = 1000f\n"
        "• 1 mois = 3000f\n\n"
        
        "🎯 **Services inclus :**\n"
        "• Pronostics quotidiens premium\n"
        "• Analyses détaillées\n"
        "• Redirection de canaux\n"
        "• Support client\n\n"
        
        "📞 **Contact :** Sossou Kouamé"
    )
    
    # Commandes admin
    if event.sender_id == ADMIN_ID:
        help_msg += (
            "\n\n👑 **Commandes Administrateur :**\n"
            "/activer user_id durée - Activer un utilisateur\n"
            "/status user_id - Statut d'un utilisateur\n"
            "• Accès total à toutes les fonctions\n"
            "• Gestion des redirections\n"
            "• Support utilisateurs"
        )
    
    await event.reply(help_msg, parse_mode="markdown")

@bot.on(events.NewMessage(pattern="/connect"))
async def connect_handler(event):
    """Handler pour connecter un compte utilisateur"""
    if event.sender_id != ADMIN_ID:
        await event.reply("⛔ Seul l'administrateur peut ajouter des comptes.")
        return
    
    parts = event.raw_text.split()
    if len(parts) != 2:
        await event.reply(
            "❌ *Utilisation :* `/connect +33612345678`\n"
            "*Format :* Numéro avec indicatif pays",
            parse_mode="markdown"
        )
        return
    
    phone_number = parts[1]
    
    try:
        result = await connect_account(phone_number)
        
        if len(result) == 4:
            client, status, phone_code_hash, timestamp = result
        elif len(result) == 3:
            client, status, phone_code_hash = result
            timestamp = None
        else:
            client, status = result[0], result[1]
            phone_code_hash = None
            timestamp = None
        
        if status == "code_requested":
            pending_connections[event.sender_id] = {
                "client": client,
                "phone": phone_number,
                "phone_code_hash": phone_code_hash
            }
            await event.reply(
                f"📱 *Code envoyé au {phone_number}*\n"
                f"⏰ *Vous avez 2 minutes pour saisir le code*\n"
                f"Utilisez `/code XXXXX` pour confirmer\n\n"
                f"💡 *Astuce :* Saisissez le code rapidement pour éviter l'expiration",
                parse_mode="markdown"
            )
        elif status == "already_connected":
            await event.reply(f"✅ Compte {phone_number} déjà connecté")
        elif status == "invalid_phone":
            await event.reply("❌ Numéro de téléphone invalide. Vérifiez le format (+indicatif pays)")
        elif status == "flood_wait":
            await event.reply(f"❌ Limite atteinte. Attendez {result[2]} secondes avant de réessayer.")
        else:
            await event.reply(f"❌ Erreur : {result[2] if len(result) > 2 else 'Erreur inconnue'}")
            
    except Exception as e:
        await event.reply(f"❌ Erreur de connexion : {e}")

@bot.on(events.NewMessage(pattern="/code"))
async def code_handler(event):
    """Handler pour confirmer le code d'authentification"""
    if event.sender_id != ADMIN_ID:
        return
    
    if event.sender_id not in pending_connections:
        await event.reply("❌ Aucune connexion en attente. Utilisez d'abord /connect")
        return
    
    parts = event.raw_text.split()
    if len(parts) != 2:
        await event.reply("❌ *Utilisation :* `/code 12345`", parse_mode="markdown")
        return
    
    code = parts[1]
    connection = pending_connections[event.sender_id]
    
    try:
        success, status, message = await complete_auth(
            connection["client"], 
            connection["phone"], 
            code,
            connection["phone_code_hash"]
        )
        
        if success:
            await event.reply(
                f"✅ *Compte {connection['phone']} connecté avec succès !*\n"
                f"🔧 Le compte peut maintenant être utilisé pour les redirections.\n"
                f"📋 Session sauvegardée : `session_{connection['phone']}`",
                parse_mode="markdown"
            )
            # Déconnecter le client temporaire
            await connection["client"].disconnect()
        else:
            if status == "expired":
                await event.reply(
                    "⏰ *Code expiré*\n"
                    "Utilisez `/connect` pour demander un nouveau code",
                    parse_mode="markdown"
                )
            elif status == "invalid_code":
                await event.reply(
                    "❌ *Code incorrect*\n"
                    "Vérifiez le code et réessayez avec `/code`",
                    parse_mode="markdown"
                )
            elif status == "password_needed":
                await event.reply(
                    "🔐 *Authentification à deux facteurs détectée*\n"
                    "Utilisez `/password votre_mot_de_passe` pour continuer",
                    parse_mode="markdown"
                )
            else:
                await event.reply(f"❌ Erreur : {message}")
            
    except Exception as e:
        await event.reply(f"❌ Erreur : {e}")
    finally:
        # Nettoyer la connexion en attente si succès ou erreur finale
        if event.sender_id in pending_connections and (success or status in ["expired", "invalid_code"]):
            del pending_connections[event.sender_id]

@bot.on(events.NewMessage(pattern="/password"))
async def password_handler(event):
    """Handler pour l'authentification 2FA"""
    if event.sender_id != ADMIN_ID:
        return
    
    if event.sender_id not in pending_connections:
        await event.reply("❌ Aucune connexion en attente.")
        return
    
    parts = event.raw_text.split(maxsplit=1)
    if len(parts) != 2:
        await event.reply("❌ *Utilisation :* `/password votre_mot_de_passe`", parse_mode="markdown")
        return
    
    password = parts[1]
    connection = pending_connections[event.sender_id]
    
    try:
        success, status, message = await complete_auth(
            connection["client"], 
            connection["phone"], 
            "",  # Code vide pour 2FA
            connection["phone_code_hash"],
            password
        )
        
        if success:
            await event.reply(
                f"✅ *Authentification 2FA réussie !*\n"
                f"🔧 Compte {connection['phone']} prêt pour les redirections.",
                parse_mode="markdown"
            )
            await connection["client"].disconnect()
        else:
            await event.reply(f"❌ Mot de passe incorrect : {message}")
            
    except Exception as e:
        await event.reply(f"❌ Erreur 2FA : {e}")
    finally:
        if event.sender_id in pending_connections:
            del pending_connections[event.sender_id]

@bot.on(events.NewMessage(pattern="/add_redirect"))
async def add_redirect_handler(event):
    """Handler pour ajouter une redirection"""
    if event.sender_id != ADMIN_ID:
        await event.reply("⛔ Seul l'administrateur peut gérer les redirections.")
        return
    
    await event.reply(
        "📋 *Configuration d'une nouvelle redirection*\n\n"
        "Pour ajouter une redirection, utilisez le code Python :\n"
        "```python\n"
        "add_redirection(\n"
        "    name='ma_redirection',\n"
        "    session='session_+33612345678',\n"
        "    sources=[-1001234567890],  # ID du canal source\n"
        "    destinations=[-1009876543210]  # ID du canal destination\n"
        ")\n"
        "```\n\n"
        "Redémarrez ensuite le bot pour appliquer les changements.",
        parse_mode="markdown"
    )

# ========== MESSAGE REDIRECTION HANDLERS ==========

@bot.on(events.NewMessage())
async def handle_redirection(event):
    """Gestionnaire principal pour les redirections"""
    if event.is_private or not event.text:
        return
    
    redirections = load_json("redirections.json")
    
    for redir_name, config in redirections.items():
        sources = config.get("sources", [])
        destinations = config.get("destinations", [])
        
        if event.chat_id in sources:
            # Vérifications des filtres
            if should_ignore(event, redir_name):
                continue
            
            text = event.text or ""
            
            # Whitelist/Blacklist
            if not match_whitelist(text, redir_name):
                continue
            if match_blacklist(text, redir_name):
                continue
            
            # Vérification du délai
            delay_config = load_json("delay.json")
            delay_secs = delay_config.get(redir_name, {}).get("seconds", 0)
            if not can_send(redir_name, delay_secs):
                continue
            
            # Transformations
            text = transform_removelines(text, redir_name)
            text = transform_power(text, redir_name)
            text = transform_format(text, redir_name)
            
            # Envoi vers les destinations
            for dest_id in destinations:
                try:
                    await bot.send_message(dest_id, text)
                    print(f"✅ Message redirigé: {redir_name} -> {dest_id}")
                except Exception as e:
                    print(f"❌ Erreur redirection {redir_name}: {e}")

@bot.on(events.MessageEdited())
async def handle_edit(event):
    """Gestionnaire des modifications de messages"""
    redirections = load_json("redirections.json")
    
    for redir_name, config in redirections.items():
        if event.chat_id in config.get("sources", []) and config.get("settings", {}).get("edit"):
            for dest in config.get("destinations", []):
                try:
                    await bot.edit_message(dest, event.id, event.text)
                except:
                    pass

@bot.on(events.MessageDeleted())
async def handle_delete(event):
    """Gestionnaire des suppressions de messages"""
    redirections = load_json("redirections.json")
    
    for redir_name, config in redirections.items():
        if hasattr(event, 'chat_id') and event.chat_id in config.get("sources", []):
            if config.get("settings", {}).get("delete"):
                for dest in config.get("destinations", []):
                    try:
                        await bot.delete_messages(dest, event.deleted_ids)
                    except:
                        pass

# ========== FONCTIONS UTILITAIRES ==========

def setup_example_config():
    """Configure des exemples de fichiers de configuration"""
    
    # Exemple de redirections
    if not os.path.exists("redirections.json"):
        save_json("redirections.json", {})
    
    # Exemple de filtres
    if not os.path.exists("filters.json"):
        save_json("filters.json", {
            "exemple": {
                "ignore": ["photo", "video"]
            }
        })
    
    # Exemple de formats
    if not os.path.exists("format.json"):
        save_json("format.json", {
            "exemple": {
                "template": "🎯 [[Message.Text]]"
            }
        })
    
    # Exemple de delay
    if not os.path.exists("delay.json"):
        save_json("delay.json", {
            "exemple": {
                "seconds": 5
            }
        })

# ========== LANCEMENT ==========

if __name__ == "__main__":
    print("🚀 Configuration des fichiers...")
    setup_example_config()
    
    print("🚀 Bot Téléfoot Avancé lancé avec succès...")
    print("📱 Fonctionnalités actives :")
    print("   • Gestion de licences")
    print("   • Pronostics football")
    print("   • Redirection de messages")
    print("   • Filtres et transformations")
    print("   • Administration complète")
    print("📡 En attente de messages...")
    
    try:
        bot.run_until_disconnected()
    except KeyboardInterrupt:
        print("\n⏹️ Arrêt du bot demandé")
    except Exception as e:
        print(f"❌ Erreur durant l'exécution : {e}")
    finally:
        print("👋 Bot arrêté")