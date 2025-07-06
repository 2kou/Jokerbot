#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WSGI Configuration pour PythonAnywhere
Téléfoot Bot Webhook Application
"""

import sys
import os

# Chemin vers votre projet (remplacez 'votreusername' par votre nom d'utilisateur)
project_home = '/home/votreusername/mysite'

# Ajouter le répertoire du projet au Python path
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Charger les variables d'environnement depuis le fichier .env
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(project_home, '.env'))
    print("✅ Variables d'environnement chargées")
except ImportError:
    print("⚠️ python-dotenv non installé, utilisez les variables d'environnement système")
except Exception as e:
    print(f"⚠️ Erreur lors du chargement des variables: {e}")

# Importer l'application Flask
try:
    from webhook_app import app as application
    print("✅ Application Flask chargée")
except Exception as e:
    print(f"❌ Erreur lors de l'importation de l'application: {e}")
    raise

# Configuration pour PythonAnywhere
if __name__ == "__main__":
    application.run(debug=False)