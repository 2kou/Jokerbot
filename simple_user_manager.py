#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gestionnaire d'utilisateurs simplifié pour PythonAnywhere
Version allégée sans dépendances externes
"""

import json
import os
from datetime import datetime, timedelta
import uuid

class SimpleUserManager:
    """Gestionnaire simplifié des utilisateurs pour PythonAnywhere"""
    
    def __init__(self, users_file='users.json'):
        self.users_file = users_file
        self.users = self.load_users()
        self.plans = {
            "semaine": {"duration_days": 7, "price": "1000f"},
            "mois": {"duration_days": 30, "price": "3000f"}
        }
        self.messages = {
            "access_expired": (
                "⛔ *Accès expiré ou non activé.*\n"
                "Contactez *Sossou Kouamé* pour activer votre licence.\n"
                "💵 *1 semaine = 1000f | 1 mois = 3000f*"
            ),
            "invalid_plan": "❌ Plan invalide. Choisissez `semaine` ou `mois`",
            "license_activated": (
                "🎉 *Votre licence a été activée*\n"
                "🔐 Clé : `{license_key}`\n"
                "⏳ Expire : *{expires}*"
            )
        }
    
    def load_users(self):
        """Charge les utilisateurs depuis le fichier JSON"""
        try:
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Erreur lecture utilisateurs: {e}")
            return {}
    
    def save_users(self):
        """Sauvegarde les utilisateurs"""
        try:
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erreur sauvegarde utilisateurs: {e}")
            return False
    
    def register_new_user(self, user_id):
        """Enregistre un nouvel utilisateur"""
        user_data = {
            "status": "waiting",
            "plan": "trial",
            "license_key": None,
            "start_time": None,
            "expires": None,
            "created_at": datetime.now().isoformat()
        }
        
        self.users[str(user_id)] = user_data
        self.save_users()
        return user_data
    
    def activate_user(self, user_id, plan):
        """Active un utilisateur"""
        if plan not in self.plans:
            raise ValueError(f"Plan invalide: {plan}")
        
        now = datetime.now()
        delta = timedelta(days=self.plans[plan]["duration_days"])
        expires = now + delta
        
        # Générer une clé de licence
        license_key = str(uuid.uuid4()).split("-")[0].upper()
        
        # Mettre à jour les données
        self.users[str(user_id)] = {
            "status": "active",
            "plan": plan,
            "license_key": license_key,
            "start_time": now.isoformat(),
            "expires": expires.isoformat(),
            "activated_at": now.isoformat()
        }
        
        self.save_users()
        return license_key, expires.strftime("%d/%m/%Y")
    
    def check_user_access(self, user_id):
        """Vérifie l'accès d'un utilisateur"""
        user_data = self.users.get(str(user_id))
        if not user_data:
            return False
        
        if user_data["status"] != "active":
            return False
        
        if not user_data.get("expires"):
            return False
        
        try:
            expires_date = datetime.fromisoformat(user_data["expires"])
            return expires_date > datetime.now()
        except:
            return False
    
    def get_user_info(self, user_id):
        """Récupère les infos d'un utilisateur"""
        return self.users.get(str(user_id))
    
    def get_user_status(self, user_id):
        """Retourne le statut d'un utilisateur"""
        user_data = self.get_user_info(user_id)
        if not user_data:
            return "non_enregistré"
        
        if user_data["status"] != "active":
            return user_data["status"]
        
        if self.check_user_access(user_id):
            return "actif"
        else:
            return "expiré"
    
    def get_expiration_date(self, user_id):
        """Retourne la date d'expiration"""
        user_data = self.get_user_info(user_id)
        if user_data and user_data.get("expires"):
            try:
                expires_date = datetime.fromisoformat(user_data["expires"])
                return expires_date.strftime("%d/%m/%Y")
            except:
                return None
        return None
    
    def get_stats(self):
        """Statistiques simples"""
        total = len(self.users)
        active = sum(1 for u in self.users.values() 
                    if u.get("status") == "active" and 
                    self.check_user_access(list(self.users.keys())[list(self.users.values()).index(u)]))
        
        return {
            "total_users": total,
            "active_users": active,
            "waiting_users": total - active
        }