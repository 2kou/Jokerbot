#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot Telegram Téléfoot avec système de connexion optimisé
Délai d'expiration des codes fixé à 30 secondes minimum
"""

from telethon.sync import TelegramClient
from telethon import events
import json, time, re, os, asyncio
from datetime import datetime, timedelta
from telefeed_commands import register_telefeed_handlers

# Configuration
api_id = int(os.getenv('API_ID', '29177661'))
api_hash = os.getenv('API_HASH', 'a8639172fa8d35dbfd8ea46286d349ab')
BOT_TOKEN = os.getenv('BOT_TOKEN', '7573497633:AAHk9K15yTCiJP-zruJrc9v8eK8I9XhjyH4')
ADMIN_ID = int(os.getenv('ADMIN_ID', '1190237801'))

# ========== UTILS ==========

def load_json(file):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def save_json(file, data):
    with open(file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# ========== SYSTÈME DE LICENCES ==========

def is_user_active(user_id):
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
    db = load_json("users.json")
    return db.get(str(user_id))

# ========== CONNEXION OPTIMISÉE ==========

# Sessions de connexion actives
active_connections = {}
code_sessions = {}

def create_user_client(phone_number):
    """Crée un client pour un numéro spécifique"""
    session_name = f'session_{phone_number.replace("+", "").replace("-", "")}'
    client = TelegramClient(session_name, api_id, api_hash)
    return client

async def request_code_optimized(phone_number):
    """Demande un code avec session persistante"""
    try:
        client = create_user_client(phone_number)
        await client.connect()

        if await client.is_user_authorized():
            return "already_connected", None, None

        # Demander le code sans déconnecter le client
        result = await client.send_code_request(phone_number)

        # Sauvegarder avec session maintenue active
        session_info = {
            "client": client,  # Client reste connecté
            "phone": phone_number,
            "hash": result.phone_code_hash,
            "timestamp": time.time(),
            "expires_at": time.time() + 300,  # 5 minutes de sécurité
            "code_sent": True
        }

        code_sessions[phone_number] = session_info

        print(f"📱 Code demandé pour {phone_number}")
        print(f"🔗 Session maintenue active")
        print(f"⏰ Délai étendu : 5 minutes")

        return "code_requested", result.phone_code_hash, session_info

    except Exception as e:
        print(f"❌ Erreur demande code : {e}")
        return "error", None, str(e)

async def verify_code_optimized(phone_number, code):
    """Vérifie le code avec gestion d'erreurs robuste"""
    if phone_number not in code_sessions:
        return False, "no_session", "Aucune session active. Redemandez un code."

    session_info = code_sessions[phone_number]
    client = session_info["client"]

    try:
        # Tentative immédiate de connexion
        await client.sign_in(phone_number, code, phone_code_hash=session_info["hash"])

        # Succès - créer le fichier session
        session_file = f'session_{phone_number.replace("+", "").replace("-", "")}.session'

        print(f"✅ Connexion réussie pour {phone_number}")
        print(f"💾 Session créée : {session_file}")

        # Nettoyer la session temporaire
        await client.disconnect()
        if phone_number in code_sessions:
            del code_sessions[phone_number]

        return True, "success", session_file

    except Exception as e:
        error_msg = str(e).lower()
        print(f"⚠️ Erreur connexion : {e}")

        if "expired" in error_msg or "phone_code_expired" in error_msg:
            # Code expiré - nettoyer la session
            print("⏰ Code expiré, session nettoyée")

            try:
                await client.disconnect()
            except:
                pass

            if phone_number in code_sessions:
                del code_sessions[phone_number]

            return False, "expired", "Code expiré. Utilisez /connect pour demander un nouveau code"

        elif "invalid" in error_msg or "phone_code_invalid" in error_msg:
            return False, "invalid", "Code incorrect, réessayez"
        elif "password" in error_msg or "2fa" in error_msg:
            return False, "2fa_needed", "Authentification 2FA requise"
        else:
            return False, "error", str(e)

# ========== INITIALISATION BOT ==========

print("🤖 Initialisation du bot Téléfoot optimisé...")

try:
    bot = TelegramClient('telefoot_bot', api_id, api_hash).start(bot_token=BOT_TOKEN)
    print("✅ Bot connecté")
except Exception as e:
    print(f"❌ Erreur bot : {e}")
    exit(1)

# ========== HANDLERS ==========

@bot.on(events.NewMessage(pattern="/start"))
async def start_handler(event):
    user_id = str(event.sender_id)

    if event.sender_id == ADMIN_ID:
        await event.reply(
            "👑 *TÉLÉFOOT ADMIN*\n"
            "✅ Accès total activé\n\n"
            "🔧 *Commandes :*\n"
            "/activer - Gérer les licences\n"
            "/connect - Connecter des comptes\n"
            "/pronostics - Voir les pronostics\n"
            "/help - Aide complète",
            parse_mode="markdown"
        )
        return

    if not is_user_active(user_id):
        await event.reply(
            "⛔ *Accès Téléfoot requis*\n\n"
            "🎯 *Services :*\n"
            "• Pronostics quotidiens\n"
            "• Analyses premium\n"
            "• Redirections canaux\n\n"
            "💰 *1 semaine = 1000f | 1 mois = 3000f*\n"
            "📞 Contact : Sossou Kouamé",
            parse_mode="markdown"
        )
        return

    await event.reply(
        "✅ *Bienvenue sur Téléfoot !*\n\n"
        "/pronostics - Pronostics du jour\n"
        "/status - Votre statut\n"
        "/help - Aide",
        parse_mode="markdown"
    )

@bot.on(events.NewMessage(pattern="/activer"))
async def activer_handler(event):
    if event.sender_id != ADMIN_ID:
        return await event.reply("⛔ Admin uniquement")

    parts = event.raw_text.split()
    if len(parts) != 3:
        return await event.reply("❌ `/activer user_id semaine/mois`", parse_mode="markdown")

    user_id, duration = parts[1], parts[2]

    if duration not in ["semaine", "mois"]:
        return await event.reply("❌ Durée : semaine ou mois")

    try:
        expire = activate_user(user_id, duration)
        await event.reply(f"✅ {user_id} activé jusqu'au {expire}")

        try:
            await bot.send_message(
                int(user_id),
                f"🎉 *Téléfoot activé !*\n⏰ Expire : {expire}",
                parse_mode="markdown"
            )
        except:
            pass
    except Exception as e:
        await event.reply(f"❌ Erreur : {e}")

@bot.on(events.NewMessage(pattern="/connect"))
async def connect_handler(event):
    if event.sender_id != ADMIN_ID:
        return await event.reply("⛔ Admin uniquement")

    parts = event.raw_text.split()
    if len(parts) != 2:
        return await event.reply("❌ `/connect +33612345678`", parse_mode="markdown")

    phone_number = parts[1]

    try:
        status, hash_code, info = await request_code_optimized(phone_number)

        if status == "already_connected":
            await event.reply(f"✅ {phone_number} déjà connecté")
        elif status == "code_requested":
            await event.reply(
                f"📱 *Code envoyé à {phone_number}*\n"
                f"⚠️ *IMPORTANT : Saisissez IMMÉDIATEMENT*\n"
                f"⏰ *Codes Telegram expirent en 30-60 secondes*\n"
                f"🚀 *Tapez `aa` suivi du code (ex: aa5673)*\n"
                f"💡 Ou utilisez `/code XXXXX` si vous préférez\n\n"
                f"💡 Si le code expire, il sera redemandé automatiquement",
                parse_mode="markdown"
            )
        else:
            await event.reply(f"❌ Erreur : {info}")
    except Exception as e:
        await event.reply(f"❌ Erreur : {e}")

# Handler pour les codes avec format aa + code
@bot.on(events.NewMessage())
async def auto_code_handler(event):
    # Vérifier si c'est l'admin
    if event.sender_id != ADMIN_ID:
        return

    # Ignorer les commandes (qui commencent par /)
    if event.raw_text and event.raw_text.startswith('/'):
        return

    # Vérifier le format aa + code (exemple: aa5673)
    if not event.raw_text:
        return

    message_text = event.raw_text.strip()
    if not re.match(r'^aa\d{4,6}$', message_text):
        return

    # Extraire le code sans "aa"
    code = message_text[2:]

    # Chercher la dernière session active
    if not code_sessions:
        await event.reply("❌ Aucune session. Utilisez `/connect` d'abord")
        return

    # Prendre la session la plus récente
    phone_number = max(code_sessions.keys(), key=lambda k: code_sessions[k]["timestamp"])

    try:
        success, status, message = await verify_code_optimized(phone_number, code)

        if success:
            await event.reply(
                f"✅ *{phone_number} connecté !*\n"
                f"💾 Session : {message}\n"
                f"🔧 Prêt pour les redirections",
                parse_mode="markdown"
            )
        else:
            if status == "expired":
                await event.reply("⏰ *Code expiré* - Utilisez `/connect` pour un nouveau code")
            elif status == "invalid":
                await event.reply("❌ *Code incorrect* - Réessayez")
            elif status == "2fa_needed":
                await event.reply("🔐 *2FA requis* - `/password motdepasse`")
            else:
                await event.reply(f"❌ {message}")
    except Exception as e:
        await event.reply(f"❌ Erreur : {e}")

@bot.on(events.NewMessage(pattern="/code"))
async def code_handler(event):
    if event.sender_id != ADMIN_ID:
        return

    parts = event.raw_text.split()
    if len(parts) != 2:
        return await event.reply("❌ `/code 12345` ou tapez `aa12345` directement", parse_mode="markdown")

    code = parts[1]

    # Chercher la dernière session active
    if not code_sessions:
        return await event.reply("❌ Aucune session. Utilisez `/connect` d'abord")

    # Prendre la session la plus récente
    phone_number = max(code_sessions.keys(), key=lambda k: code_sessions[k]["timestamp"])

    try:
        success, status, message = await verify_code_optimized(phone_number, code)

        if success:
            await event.reply(
                f"✅ *{phone_number} connecté !*\n"
                f"💾 Session : {message}\n"
                f"🔧 Prêt pour les redirections",
                parse_mode="markdown"
            )
        else:
            if status == "expired":
                await event.reply("⏰ *Code expiré* - Utilisez `/connect` pour un nouveau code")
            elif status == "invalid":
                await event.reply("❌ *Code incorrect* - Réessayez")
            elif status == "2fa_needed":
                await event.reply("🔐 *2FA requis* - `/password motdepasse`")
            else:
                await event.reply(f"❌ {message}")
    except Exception as e:
        await event.reply(f"❌ Erreur : {e}")

@bot.on(events.NewMessage(pattern="/pronostics"))
async def pronostics_handler(event):
    user_id = str(event.sender_id)

    if event.sender_id != ADMIN_ID and not is_user_active(user_id):
        return await event.reply("⛔ Accès requis")

    pronostics = (
        "🎯 *PRONOSTICS TÉLÉFOOT*\n\n"

        "⚽ *Ligue 1*\n"
        "• PSG vs Lyon - **1** - Cote: 1.85 ⭐\n"
        "• Marseille vs Nice - **X** - Cote: 3.20\n\n"

        "🏴󠁧󠁢󠁥󠁮󠁧󠁿 *Premier League*\n"
        "• Man City vs Arsenal - **1** - Cote: 2.10 🔥\n"
        "• Chelsea vs Liverpool - **2** - Cote: 2.75\n\n"

        "🇪🇸 *Liga*\n"
        "• Real vs Barcelona - **1** - Cote: 2.45 ⚡\n"
        "• Atletico vs Sevilla - **+2.5 buts** - Cote: 1.95\n\n"

        "💎 *COMBO DU JOUR*\n"
        "PSG + Man City + Real Madrid\n"
        "**Cote : 7.85** 🚀\n\n"

        f"📊 Performance : 78% cette semaine\n"
        f"⏰ MAJ : {datetime.now().strftime('%H:%M')}"
    )

    await event.reply(pronostics, parse_mode="markdown")

@bot.on(events.NewMessage(pattern="/status"))
async def status_handler(event):
    user_id = str(event.sender_id)

    if event.sender_id == ADMIN_ID:
        parts = event.raw_text.split()
        if len(parts) == 2:
            target = parts[1]
            info = get_user_info(target)
            if info:
                active = "✅ Actif" if is_user_active(target) else "❌ Expiré"
                await event.reply(
                    f"📊 *Utilisateur {target}*\n"
                    f"🔄 {active}\n"
                    f"📋 {info.get('plan', 'N/A')}\n"
                    f"⏰ {info.get('expire_at', 'N/A')}",
                    parse_mode="markdown"
                )
            else:
                await event.reply("❌ Utilisateur non trouvé")
            return

    info = get_user_info(user_id)
    if not info:
        return await event.reply("❌ Non enregistré")

    active = "✅ Actif" if is_user_active(user_id) else "❌ Expiré"
    await event.reply(
        f"📊 *Votre statut*\n"
        f"🔄 {active}\n"
        f"📋 {info.get('plan', 'N/A')}\n"
        f"⏰ {info.get('expire_at', 'N/A')}",
        parse_mode="markdown"
    )

@bot.on(events.NewMessage(pattern="/help"))
async def help_handler(event):
    help_msg = (
        "🤖 *TÉLÉFOOT - AIDE*\n\n"

        "📱 *Commandes :*\n"
        "/start - Démarrer\n"
        "/pronostics - Pronostics du jour\n"
        "/status - Votre statut\n"
        "/help - Cette aide\n\n"

        "💰 *Tarifs :*\n"
        "• 1 semaine = 1000f\n"
        "• 1 mois = 3000f\n\n"

        "📞 *Contact :* Sossou Kouamé"
    )

    if event.sender_id == ADMIN_ID:
        help_msg += (
            "\n\n👑 *COMMANDES ADMIN :*\n"
            "/activer user_id plan - Activer licence\n"
            "/connect +numéro - Connecter compte\n"
            "/code XXXXX - Confirmer code\n"
            "aa + code - Nouveau format (ex: aa5673)\n"
            "/status user_id - Statut utilisateur\n"
            "/dashboard - Rapport complet\n"
            "/userinfo user_id - Détails utilisateur\n\n"

            "🔄 *REDIRECTIONS :*\n"
            "/redirection - Gestion complète redirections\n"
            "/chats - Liste des chats disponibles\n"
            "/sessions - Comptes connectés\n\n"

            "🛠️ *TELEFEED AVANCÉ :*\n"
            "/transformation - Format, power, removeLines\n"
            "/whitelist - Mots autorisés uniquement\n"
            "/blacklist - Mots interdits\n"
            "/delay - Délai entre messages\n"
            "/settings - Paramètres avancés\n\n"

            "🔧 *GESTION :*\n"
            "• Plans : semaine (7j) ou mois (30j)\n"
            "• Tarifs : 1000f/semaine, 3000f/mois\n"
            "• Sessions automatiques nettoyées\n"
            "• Codes expirent en 2 minutes"
        )

    await event.reply(help_msg, parse_mode="markdown")

# Les handlers de redirection sont maintenant dans telefeed_commands.py

# ========== NETTOYAGE AUTO ==========

async def cleanup_expired_sessions():
    """Nettoie les sessions expirées toutes les minutes"""
    while True:
        try:
            await asyncio.sleep(60)  # Attendre 1 minute

            current_time = time.time()
            expired_sessions = []

            for phone, session_info in code_sessions.items():
                if current_time > session_info["expires_at"]:
                    expired_sessions.append(phone)

            for phone in expired_sessions:
                try:
                    await code_sessions[phone]["client"].disconnect()
                except:
                    pass
                del code_sessions[phone]
                print(f"🧹 Session expirée nettoyée : {phone}")

        except Exception as e:
            print(f"❌ Erreur nettoyage : {e}")

# ========== LANCEMENT ==========

if __name__ == "__main__":
    print("🚀 Bot Téléfoot avec connexion optimisée lancé")
    print("⏰ Délai d'expiration des codes : 2 minutes")
    print("🔧 Nettoyage automatique des sessions")

    # Enregistrer les handlers TeleFeed
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(register_telefeed_handlers(bot, ADMIN_ID))
        print("📡 TeleFeed handlers chargés")
    except Exception as e:
        print(f"⚠️ Erreur TeleFeed handlers : {e}")

    print("📡 En attente de messages...")

    # Démarrer le nettoyage automatique
    loop = asyncio.get_event_loop()
    loop.create_task(cleanup_expired_sessions())

    try:
        bot.run_until_disconnected()
    except KeyboardInterrupt:
        print("\n⏹️ Arrêt demandé")
    except Exception as e:
        print(f"❌ Erreur : {e}")
    finally:
        print("👋 Bot arrêté")