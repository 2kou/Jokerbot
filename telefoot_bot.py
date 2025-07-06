#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bot Telegram Téléfoot avec système de gestion de licences
Version simplifiée basée sur le code source fourni
"""

from telethon.sync import TelegramClient, events
import datetime
import uuid
import json
import os

# ==== CONFIGURATION ====
API_ID = int(os.getenv('API_ID', '29177661'))
API_HASH = os.getenv('API_HASH', 'a8639172fa8d35dbfd8ea46286d349ab')
BOT_TOKEN = os.getenv('BOT_TOKEN', '7573497633:AAHk9K15yTCiJP-zruJrc9v8eK8I9XhjyH4')
ADMIN_ID = int(os.getenv('ADMIN_ID', '1190237801'))

# ==== FICHIERS ====
USERS_FILE = "users.json"

# ==== GESTION UTILISATEURS ====

def load_users():
    """Charge les utilisateurs depuis le fichier JSON"""
    try:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print(f"Erreur de lecture du fichier {USERS_FILE}")
        return {}

def save_users(users):
    """Sauvegarde les utilisateurs dans le fichier JSON"""
    try:
        with open(USERS_FILE, "w", encoding='utf-8') as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Erreur lors de la sauvegarde : {e}")

def register_new_user(user_id):
    """Enregistre un nouvel utilisateur avec statut d'attente"""
    return {
        "status": "waiting",
        "plan": "trial",
        "license_key": None,
        "start_time": None,
        "expires": None,
        "created_at": datetime.datetime.utcnow().isoformat()
    }

def activate_user(users, user_id, plan):
    """Active un utilisateur avec un plan donné"""
    now = datetime.datetime.utcnow()
    if plan == "semaine":
        delta = datetime.timedelta(days=7)
    elif plan == "mois":
        delta = datetime.timedelta(days=30)
    else:
        raise ValueError("Plan invalide")
    
    expires = now + delta
    key = str(uuid.uuid4()).split("-")[0].upper()
    
    users[user_id] = {
        "status": "active",
        "plan": plan,
        "license_key": key,
        "start_time": now.isoformat(),
        "expires": expires.isoformat(),
        "activated_at": now.isoformat()
    }
    return key, expires.date()

def check_user_access(user_data):
    """Vérifie si l'utilisateur a accès au service"""
    if user_data["status"] != "active":
        return False
    if user_data["expires"] is None:
        return False
    try:
        return datetime.datetime.fromisoformat(user_data["expires"]) > datetime.datetime.utcnow()
    except (ValueError, TypeError):
        return False

def get_user_status(users, user_id):
    """Retourne le statut d'un utilisateur"""
    if user_id not in users:
        return "non_enregistré"
    
    user_data = users[user_id]
    if user_data["status"] != "active":
        return user_data["status"]
    
    if check_user_access(user_data):
        return "actif"
    else:
        return "expiré"

def get_expiration_date(users, user_id):
    """Retourne la date d'expiration d'un utilisateur"""
    if user_id not in users:
        return None
    
    user_data = users[user_id]
    if user_data.get("expires"):
        try:
            expires_date = datetime.datetime.fromisoformat(user_data["expires"])
            return expires_date.strftime("%d/%m/%Y")
        except (ValueError, TypeError):
            return None
    return None

# ==== INITIALISATION ====

print("🤖 Initialisation du bot Téléfoot...")

# Chargement des utilisateurs
users = load_users()

# Création du client bot
try:
    bot = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
    print("✅ Bot connecté avec succès")
except Exception as e:
    print(f"❌ Erreur de connexion : {e}")
    exit(1)

# ==== HANDLERS ====

@bot.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    """Handler pour la commande /start"""
    user_id = str(event.sender_id)
    
    # Enregistrement automatique du nouvel utilisateur
    if user_id not in users:
        users[user_id] = register_new_user(user_id)
        save_users(users)
        print(f"👤 Nouvel utilisateur enregistré : {user_id}")

    # Accès automatique pour l'administrateur (vous)
    if event.sender_id == ADMIN_ID:
        # Activation automatique avec accès permanent pour l'admin
        users[user_id] = {
            "status": "active",
            "plan": "admin",
            "license_key": "ADMIN-ACCESS",
            "start_time": datetime.datetime.utcnow().isoformat(),
            "expires": (datetime.datetime.utcnow() + datetime.timedelta(days=365*10)).isoformat(),  # 10 ans
            "activated_at": datetime.datetime.utcnow().isoformat()
        }
        save_users(users)
        await event.reply(
            "👑 *Accès Administrateur Activé*\n"
            "✅ *Bienvenue Boss ! Vous avez un accès total.*\n"
            "🔧 Utilisez /help pour voir toutes vos commandes admin.",
            parse_mode="markdown"
        )
        return

    # Vérification de l'accès pour les autres utilisateurs
    if not check_user_access(users[user_id]):
        await event.reply(
            "⛔ *Accès expiré ou non activé.*\n"
            "Contactez *Sossou Kouamé* pour activer votre licence.\n"
            "💵 *1 semaine = 1000f | 1 mois = 3000f*",
            parse_mode="markdown"
        )
        return

    # Utilisateur actif
    await event.reply("✅ *Bienvenue ! Votre accès est actif.*", parse_mode="markdown")

@bot.on(events.NewMessage(pattern='/activer'))
async def activer_handler(event):
    """Handler pour la commande /activer (admin seulement)"""
    if event.sender_id != ADMIN_ID:
        await event.reply("❌ Commande réservée aux administrateurs.")
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
            await event.reply("❌ Plan invalide. Choisissez `semaine` ou `mois`")
            return

        # Activation de l'utilisateur
        license_key, expires = activate_user(users, user_id, plan)
        save_users(users)
        
        print(f"✅ Utilisateur {user_id} activé pour 1 {plan}")

        # Notification à l'utilisateur
        try:
            await bot.send_message(int(user_id),
                f"🎉 *Votre licence a été activée*\n"
                f"🔐 Clé : `{license_key}`\n"
                f"⏳ Expire : *{expires}*",
                parse_mode="markdown"
            )
        except Exception as e:
            print(f"Erreur lors de l'envoi du message à l'utilisateur {user_id}: {e}")

        # Confirmation à l'admin
        await event.reply(f"✅ Utilisateur {user_id} activé pour 1 {plan}")

    except Exception as e:
        await event.reply(f"❌ Erreur : {e}")
        print(f"Erreur dans activer_handler: {e}")

@bot.on(events.NewMessage(pattern='/status'))
async def status_handler(event):
    """Handler pour la commande /status"""
    user_id = str(event.sender_id)
    
    # Seul l'admin peut voir le statut de tous les utilisateurs
    if event.sender_id == ADMIN_ID:
        parts = event.raw_text.split()
        if len(parts) == 2:
            target_user_id = parts[1]
            if target_user_id in users:
                user_info = users[target_user_id]
                status = get_user_status(users, target_user_id)
                expiration = get_expiration_date(users, target_user_id)
                
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
    if user_id not in users:
        await event.reply("❌ Vous n'êtes pas enregistré. Utilisez /start")
        return
    
    user_info = users[user_id]
    status = get_user_status(users, user_id)
    expiration = get_expiration_date(users, user_id)
    
    message = f"📊 *Votre statut*\n"
    message += f"🔄 Statut : *{status}*\n"
    message += f"📋 Plan : *{user_info.get('plan', 'N/A')}*\n"
    if expiration:
        message += f"⏳ Expire : *{expiration}*\n"
    if user_info.get('license_key'):
        message += f"🔐 Clé : `{user_info.get('license_key')}`"
    
    await event.reply(message, parse_mode="markdown")

@bot.on(events.NewMessage(pattern='/help'))
async def help_handler(event):
    """Handler pour la commande /help"""
    help_message = (
        "🤖 *Commandes disponibles :*\n\n"
        "/start - Démarrer le bot\n"
        "/status - Voir votre statut\n"
        "/help - Afficher cette aide\n\n"
        "💰 *Tarifs :*\n"
        "• 1 semaine = 1000f\n"
        "• 1 mois = 3000f\n\n"
        "📞 *Contact :* Sossou Kouamé"
    )
    
    # Commandes admin
    if event.sender_id == ADMIN_ID:
        help_message += (
            "\n\n👑 *Commandes admin :*\n"
            "/activer user_id plan - Activer un utilisateur\n"
            "/status user_id - Voir le statut d'un utilisateur"
        )
    
    await event.reply(help_message, parse_mode="markdown")

@bot.on(events.NewMessage(pattern='/pronostics'))
async def pronostics_handler(event):
    """Handler pour les pronostics du jour"""
    user_id = str(event.sender_id)
    
    # Vérification de l'accès
    if user_id not in users or (event.sender_id != ADMIN_ID and not check_user_access(users[user_id])):
        await event.reply(
            "⛔ *Accès requis pour voir les pronostics*\n"
            "Contactez *Sossou Kouamé* pour activer votre licence.",
            parse_mode="markdown"
        )
        return
    
    # Pronostics du jour
    pronostics = (
        "🎯 *PRONOSTICS TÉLÉFOOT DU JOUR*\n\n"
        "⚽ **MATCHS PREMIUM** ⚽\n\n"
        
        "🏆 *Ligue 1*\n"
        "• PSG vs Lyon - **1** (Victoire PSG) - Cote: 1.85\n"
        "• Marseille vs Nice - **X** (Match nul) - Cote: 3.20\n\n"
        
        "🏆 *Premier League*\n"
        "• Man City vs Arsenal - **1** (Victoire City) - Cote: 2.10\n"
        "• Chelsea vs Liverpool - **2** (Victoire Liverpool) - Cote: 2.75\n\n"
        
        "🏆 *Liga*\n"
        "• Real Madrid vs Barcelona - **1** (Victoire Real) - Cote: 2.45\n"
        "• Atletico vs Sevilla - **Plus de 2.5 buts** - Cote: 1.95\n\n"
        
        "💎 **COMBO SÛRE DU JOUR**\n"
        "PSG Victoire + Man City Victoire + Plus de 1.5 buts Real-Barca\n"
        "**Cote combinée: 7.85** 🚀\n\n"
        
        "📊 *Statistiques*: 78% de réussite cette semaine\n"
        "💰 *Conseil*: Mise recommandée 2-5% de votre bankroll"
    )
    
    await event.reply(pronostics, parse_mode="markdown")

@bot.on(events.NewMessage(pattern='/vip'))
async def vip_handler(event):
    """Handler pour les pronostics VIP"""
    user_id = str(event.sender_id)
    
    # Vérification de l'accès
    if user_id not in users or (event.sender_id != ADMIN_ID and not check_user_access(users[user_id])):
        await event.reply(
            "⛔ *Accès VIP requis*\n"
            "Contactez *Sossou Kouamé* pour votre abonnement VIP.",
            parse_mode="markdown"
        )
        return
    
    vip_tips = (
        "💎 *PRONOSTICS VIP TÉLÉFOOT* 💎\n\n"
        "🔥 **MATCH INSIDE DU JOUR** 🔥\n\n"
        
        "⭐ *Information Privilégiée*\n"
        "Bayern Munich vs Dortmund\n"
        "🎯 **Plus de 3.5 buts** - Cote: 3.85\n"
        "📋 Source: Contact direct avec l'équipe\n\n"
        
        "🏆 *TRIPLE VIP*\n"
        "1. Juventus Victoire (vs Inter) - Cote: 2.30\n"
        "2. Brighton +1.5 Handicap - Cote: 1.65\n"
        "3. Moins de 2.5 buts (Milan vs Roma) - Cote: 2.15\n"
        "**Cote combinée: 8.15** 💰\n\n"
        
        "🎰 *PARI RISQUÉ HAUTE COTE*\n"
        "Score exact: Manchester United 2-1 Tottenham\n"
        "**Cote: 12.50** ⚡\n\n"
        
        "📈 *Confiance*: 85% sur le triple VIP\n"
        "💡 *Stratégie*: Mise progressive recommandée"
    )
    
    await event.reply(vip_tips, parse_mode="markdown")

@bot.on(events.NewMessage(pattern='/statistiques'))
async def stats_handler(event):
    """Handler pour les statistiques"""
    user_id = str(event.sender_id)
    
    # Vérification de l'accès
    if user_id not in users or (event.sender_id != ADMIN_ID and not check_user_access(users[user_id])):
        await event.reply(
            "⛔ *Accès requis pour voir les statistiques*",
            parse_mode="markdown"
        )
        return
    
    stats = (
        "📊 *STATISTIQUES TÉLÉFOOT* 📊\n\n"
        
        "📈 **PERFORMANCE MENSUELLE**\n"
        "✅ Pronostics gagnants: 23/30\n"
        "❌ Pronostics perdants: 7/30\n"
        "📊 Taux de réussite: **76.7%**\n\n"
        
        "💰 **BÉNÉFICES**\n"
        "💵 Gain moyen par pari: +2.85 unités\n"
        "📈 ROI mensuel: **+47%**\n"
        "🏆 Meilleure série: 8 gains consécutifs\n\n"
        
        "🎯 **SPÉCIALITÉS**\n"
        "⚽ Ligue 1: 82% de réussite\n"
        "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League: 74% de réussite\n"
        "🇪🇸 Liga: 79% de réussite\n"
        "🇮🇹 Serie A: 71% de réussite\n\n"
        
        "📅 **CETTE SEMAINE**\n"
        "Lundi: ✅ PSG Victoire (Gagné)\n"
        "Mardi: ✅ Plus de 2.5 Liverpool-City (Gagné)\n"
        "Mercredi: ❌ Real Madrid Victoire (Perdu)\n"
        "Jeudi: ✅ Milan-Inter Nul (Gagné)\n"
        "Vendredi: ✅ Combo Ligue 1 (Gagné)\n\n"
        
        "🔥 **EN FORME**: 4 gains sur 5 cette semaine!"
    )
    
    await event.reply(stats, parse_mode="markdown")

@bot.on(events.NewMessage(pattern='/matchs'))
async def matchs_handler(event):
    """Handler pour le programme des matchs"""
    user_id = str(event.sender_id)
    
    # Vérification de l'accès
    if user_id not in users or (event.sender_id != ADMIN_ID and not check_user_access(users[user_id])):
        await event.reply(
            "⛔ *Accès requis pour voir le programme*",
            parse_mode="markdown"
        )
        return
    
    matchs = (
        "📅 *PROGRAMME DES MATCHS* 📅\n\n"
        
        "🕘 **AUJOURD'HUI**\n"
        "⏰ 15h00: Lens vs Rennes (Ligue 1)\n"
        "⏰ 17h00: Brighton vs Newcastle (Premier League)\n"
        "⏰ 20h00: PSG vs Lyon (Ligue 1) 🔥\n"
        "⏰ 22h30: Real Madrid vs Barcelona (Liga) ⭐\n\n"
        
        "🕘 **DEMAIN**\n"
        "⏰ 14h30: Man City vs Arsenal (Premier League)\n"
        "⏰ 16h00: Milan vs Inter (Serie A)\n"
        "⏰ 18h00: Bayern vs Dortmund (Bundesliga)\n"
        "⏰ 20h45: Juventus vs Napoli (Serie A)\n\n"
        
        "🔥 **MATCHS À SUIVRE**\n"
        "⭐ Real vs Barca: El Clasico - Pronostic disponible\n"
        "⭐ PSG vs Lyon: Choc au sommet - Analyse VIP\n"
        "⭐ Man City vs Arsenal: Title race - Stats premium\n\n"
        
        "📱 *Conseil*: Activez les notifications pour ne rien rater!"
    )
    
    await event.reply(matchs, parse_mode="markdown")

@bot.on(events.NewMessage(pattern='/admin_access'))
async def admin_access_handler(event):
    """Commande spéciale pour activer l'accès admin"""
    if event.sender_id == ADMIN_ID:
        user_id = str(event.sender_id)
        # Activation automatique avec accès permanent pour l'admin
        users[user_id] = {
            "status": "active",
            "plan": "admin",
            "license_key": "ADMIN-ACCESS",
            "start_time": datetime.datetime.utcnow().isoformat(),
            "expires": (datetime.datetime.utcnow() + datetime.timedelta(days=365*10)).isoformat(),  # 10 ans
            "activated_at": datetime.datetime.utcnow().isoformat()
        }
        save_users(users)
        await event.reply(
            "👑 *ACCÈS ADMINISTRATEUR TOTAL ACTIVÉ*\n"
            "✅ *Vous avez maintenant un accès permanent de 10 ans*\n"
            "🔐 Clé : `ADMIN-ACCESS`\n"
            "🔧 Toutes les commandes admin sont disponibles",
            parse_mode="markdown"
        )
        print(f"👑 Accès administrateur activé pour {user_id}")
    else:
        await event.reply("❌ Cette commande est réservée au propriétaire du bot.")

# ==== LANCEMENT ====

print("🚀 Bot Téléfoot lancé avec succès...")
print("📱 En attente de messages...")

try:
    bot.run_until_disconnected()
except KeyboardInterrupt:
    print("\n⏹️  Arrêt du bot demandé")
except Exception as e:
    print(f"❌ Erreur durant l'exécution : {e}")
finally:
    print("👋 Bot arrêté")