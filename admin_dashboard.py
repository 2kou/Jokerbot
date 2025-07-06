
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard administrateur pour le bot Téléfoot
"""

import json
from datetime import datetime, timedelta
import os

def load_json(file):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def generate_admin_report():
    """Génère un rapport complet pour l'admin"""
    # Charger les données
    users = load_json("users.json")
    stats = load_json("bot_stats.json")
    
    # Statistiques utilisateurs
    total_users = len(users)
    active_users = sum(1 for user in users.values() 
                      if user.get("status") == "active" and 
                      datetime.fromisoformat(user.get("expires", "2000-01-01")) > datetime.now())
    
    expired_users = sum(1 for user in users.values() 
                       if user.get("status") == "active" and 
                       datetime.fromisoformat(user.get("expires", "2000-01-01")) <= datetime.now())
    
    waiting_users = sum(1 for user in users.values() if user.get("status") == "waiting")
    
    # Revenus estimés
    revenue_week = sum(1000 for user in users.values() if user.get("plan") == "semaine")
    revenue_month = sum(3000 for user in users.values() if user.get("plan") == "mois")
    total_revenue = revenue_week + revenue_month
    
    # Expirations prochaines (7 jours)
    next_week = datetime.now() + timedelta(days=7)
    expiring_soon = [user_id for user_id, user in users.items() 
                    if user.get("expires") and 
                    datetime.fromisoformat(user.get("expires")) <= next_week and
                    datetime.fromisoformat(user.get("expires")) > datetime.now()]
    
    report = f"""
📊 *RAPPORT ADMINISTRATEUR TÉLÉFOOT*

👥 **UTILISATEURS**
• Total: {total_users}
• Actifs: {active_users} ✅
• Expirés: {expired_users} ❌
• En attente: {waiting_users} ⏳

💰 **REVENUS**
• Semaine (1000f): {revenue_week//1000} = {revenue_week}f
• Mois (3000f): {revenue_month//3000} = {revenue_month}f
• **Total: {total_revenue}f** 💵

⚠️ **EXPIRATIONS PROCHAINES (7 jours)**
• {len(expiring_soon)} utilisateurs à renouveler

📈 **ACTIVITÉ**
• Commandes totales: {stats.get('commands_used', {}).get('total', 0)}
• Commande populaire: {max(stats.get('commands_used', {}).items(), key=lambda x: x[1])[0] if stats.get('commands_used') else 'N/A'}

🔧 **ACTIONS RECOMMANDÉES**
• Contacter les utilisateurs qui expirent bientôt
• Proposer des offres de renouvellement
• Analyser les commandes populaires
"""
    
    return report

def get_user_details(user_id):
    """Obtient les détails d'un utilisateur"""
    users = load_json("users.json")
    user = users.get(user_id)
    
    if not user:
        return "❌ Utilisateur non trouvé"
    
    status = "✅ Actif" if (user.get("status") == "active" and 
                          datetime.fromisoformat(user.get("expires", "2000-01-01")) > datetime.now()) else "❌ Inactif"
    
    return f"""
👤 **DÉTAILS UTILISATEUR {user_id}**

🔄 Statut: {status}
📋 Plan: {user.get('plan', 'N/A')}
🔐 Clé: {user.get('license_key', 'N/A')}
📅 Activé: {user.get('activated_at', 'N/A')}
⏰ Expire: {user.get('expire_at', 'N/A')}
"""

if __name__ == "__main__":
    print(generate_admin_report())
