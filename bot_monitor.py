
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Système de monitoring pour le bot Téléfoot
"""

import json
import time
from datetime import datetime
import asyncio
import os

class BotMonitor:
    def __init__(self):
        self.stats_file = "bot_stats.json"
        self.load_stats()
    
    def load_stats(self):
        """Charge les statistiques du bot"""
        try:
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                self.stats = json.load(f)
        except:
            self.stats = {
                "total_users": 0,
                "active_users": 0,
                "commands_used": {},
                "daily_activity": {},
                "start_time": datetime.now().isoformat(),
                "last_update": datetime.now().isoformat()
            }
    
    def save_stats(self):
        """Sauvegarde les statistiques"""
        self.stats["last_update"] = datetime.now().isoformat()
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur sauvegarde stats: {e}")
    
    def log_command(self, user_id, command):
        """Enregistre l'utilisation d'une commande"""
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Compteur de commandes
        if command not in self.stats["commands_used"]:
            self.stats["commands_used"][command] = 0
        self.stats["commands_used"][command] += 1
        
        # Activité quotidienne
        if today not in self.stats["daily_activity"]:
            self.stats["daily_activity"][today] = {
                "users": set(),
                "commands": 0
            }
        
        self.stats["daily_activity"][today]["users"].add(user_id)
        self.stats["daily_activity"][today]["commands"] += 1
        
        # Convertir les sets en listes pour JSON
        self.stats["daily_activity"][today]["users"] = list(self.stats["daily_activity"][today]["users"])
        
        self.save_stats()
    
    def get_stats_summary(self):
        """Retourne un résumé des statistiques"""
        today = datetime.now().strftime("%Y-%m-%d")
        today_stats = self.stats["daily_activity"].get(today, {"users": [], "commands": 0})
        
        most_used = max(self.stats["commands_used"].items(), key=lambda x: x[1]) if self.stats["commands_used"] else ("N/A", 0)
        
        return {
            "users_today": len(today_stats["users"]),
            "commands_today": today_stats["commands"],
            "total_commands": sum(self.stats["commands_used"].values()),
            "most_used_command": most_used[0],
            "most_used_count": most_used[1],
            "uptime_days": (datetime.now() - datetime.fromisoformat(self.stats["start_time"])).days
        }

# Instance globale
monitor = BotMonitor()
