# Téléfoot Bot - Telegram License Management System

## Overview

This is a Telegram bot built with Python that manages user licenses for a sports/football service. The bot implements a subscription-based access system with different plans (weekly/monthly) and includes administrative controls for license activation.

## System Architecture

### Core Components
- **Main Bot Controller** (`main.py`): TelefootBot class managing the bot lifecycle
- **User Management** (`user_manager.py`): Handles user registration, license activation, and data persistence
- **Bot Handlers** (`bot_handlers.py`): Manages Telegram commands and events
- **Configuration** (`config.py`): Centralized configuration for API keys, plans, and messages

### Technology Stack
- **Telethon**: Async Telegram client library for bot communication
- **Python 3**: Core runtime environment
- **JSON**: File-based data storage for user information
- **Environment Variables**: Configuration management

## Key Components

### 1. Bot Controller (TelefootBot)
- Manages Telegram client initialization and connection
- Handles bot startup and shutdown procedures
- Coordinates between user management and message handlers
- Implements graceful error handling for API connection issues

### 2. User Manager
- **Registration**: Automatic user registration on first contact
- **License Management**: Handles plan activation and expiration tracking
- **Data Persistence**: JSON-based storage for user data and licenses
- **Access Control**: Validates user permissions and subscription status

### 3. Bot Handlers
- **Command Processing**: Handles `/start`, `/activer`, `/status`, `/help` commands
- **Admin Controls**: Restricted activation commands for administrators
- **User Interaction**: Provides feedback and status messages to users

### 4. Configuration Management
- **API Configuration**: Telegram API credentials and bot token
- **Plan Management**: Subscription plans with pricing and duration
- **Message Templates**: Localized messages in French for user interactions

## Data Flow

1. **User Registration**: New users are automatically registered with "waiting" status
2. **License Activation**: Admin uses `/activer` command to activate user licenses
3. **Access Validation**: Each user interaction checks current license status
4. **Data Persistence**: All user data is saved to JSON file after modifications

### User States
- **Waiting**: New users awaiting license activation
- **Active**: Users with valid, non-expired licenses
- **Expired**: Users with expired licenses requiring renewal

## External Dependencies

### Required APIs
- **Telegram Bot API**: Core bot functionality via Telethon
- **Environment Variables**: API_ID, API_HASH, BOT_TOKEN, ADMIN_ID

### Python Packages
- `telethon`: Telegram client library
- `asyncio`: Async programming support
- `json`: Data serialization
- `datetime`: Time and date handling
- `uuid`: License key generation

## Deployment Strategy

### Environment Setup
- Python 3.7+ runtime required
- Environment variables for API configuration
- File system access for JSON data storage
- Persistent storage for user data across restarts

### Data Storage
- JSON file-based storage (`users.json`)
- No database server required
- Automatic file creation and error recovery
- UTF-8 encoding for international character support

### Security Considerations
- Admin-only activation commands
- User ID validation for access control
- Secure API token management via environment variables

## User Preferences

Preferred communication style: Simple, everyday language.

## Recent Changes

- **July 05, 2025**: TeleFoot Bot v2.0 - Système Avancé Complet + Redirection Authentique CONFIRMÉE
  - ✅ **Problème "MO" résolu** : Messages n'apparaissent plus avec signature utilisateur
  - ✅ **Redirection authentique active** : System `from_peer` implémenté et fonctionnel
  - ✅ **Logs confirmés** : "Message normal envoyé" - redirection discrète opérationnelle
  - ✅ **Système d'approbation** : Nouveaux utilisateurs → Admin → Essai 24h
  - ✅ **Licences personnalisées** : Format unique user_id+moitié_id+date+72390
  - ✅ **Limitation intelligente** : 1 redirection (essai), 10 (semaine), 50 (mois)
  - ✅ **Workflow complet** : /start → approbation → /payer → validation → /valider_licence
  - ✅ **PythonAnywhere prêt** : Flask + Webhook + Monitoring complet
  - ✅ **Interface admin** : Approbations, paiements, statistiques en temps réel
  - ✅ **Sécurité renforcée** : Validation stricte, licences non-partageables

- **July 05, 2025**: Système de redirection TeleFeed 100% opérationnel
  - ✅ Correction des IDs de canaux (format négatif Telegram)
  - ✅ Redirection automatique confirmée : -1001178062153 → -4922594370
  - ✅ Logs de débogage : "Message redirigé de X vers Y via Z"
  - ✅ Gestionnaires attachés aux bons clients TeleFeed
  - ✅ Système de filtrage et transformation fonctionnel
  - ✅ Hébergement Replit avec limitation 2h/24h identifiée

- **July 05, 2025**: Système de persistance des sessions TeleFeed complètement fonctionnel
  - ✅ Sessions automatiquement restaurées au démarrage du bot (confirmé)
  - ✅ Plus jamais besoin de se reconnecter après redémarrage
  - ✅ Fonction `restore_telefeed_sessions()` intégrée dans `main.py`
  - ✅ Logs de restauration visibles : "Session restaurée pour NUMERO"
  - ✅ Nouvelle commande `/sessions` pour l'admin pour monitoring
  - ✅ Fichiers `.session` conservés et restaurés automatiquement
  - ✅ Gestion complète des erreurs et sessions expirées

- **July 05, 2025**: Interface à boutons TeleFeed complète implémentée
  - Interface utilisateur à boutons exactement conforme aux captures d'écran fournies
  - Menu principal avec 16 boutons organisés : Connect, Getting Started Guide, Redirection, Transformation, etc.
  - Navigation hiérarchique avec boutons "Retour" pour une expérience utilisateur fluide
  - Menus spécialisés pour chaque fonctionnalité : Whitelist, Blacklist, Delay, Settings, etc.
  - Documentation interactive intégrée dans chaque menu avec exemples d'utilisation
  - Nouvelle commande /menu pour accéder à l'interface à boutons
  - Système de gestion des callbacks avec routage intelligent
  - Interface conforme aux standards TeleFeed avec toutes les fonctionnalités documentées
  
- **July 05, 2025**: Système TeleFeed complet intégré
  - Implementation complète des fonctionnalités TeleFeed selon documentation
  - Commandes admin complètes : /test, /guide, /clean, /reconnect, /config, /delay, /settings
  - Système de redirections de messages entre canaux Telegram
  - Transformations avancées : format, power, removeLines
  - Filtres whitelist/blacklist avec support regex
  - Gestion des sessions et diagnostic intégré
  - Guide étape par étape pour configuration TeleFeed
  - Interface d'aide complète conforme aux spécifications utilisateur

- **July 04, 2025**: Système de saisie de code simplifié
  - Nouveau format de confirmation : l'utilisateur peut maintenant saisir directement "aa" + code (ex: aa5673)
  - Suppression de l'obligation d'utiliser la commande /code
  - Système automatique de détection des codes de confirmation
  - Instructions mises à jour pour guider les utilisateurs
  - Amélioration de l'expérience utilisateur pour la connexion de comptes

- **July 04, 2025**: Bot Telegram Téléfoot Avancé déployé
  - Système de gestion de licences complet
  - Fonctionnalités Téléfoot ajoutées : pronostics football quotidiens
  - Système de redirection entre canaux Telegram
  - Filtres et transformations de messages configurables
  - Administration avancée avec accès total pour l'utilisateur
  - Tarification : 1 semaine = 1000f, 1 mois = 3000f
  - Bot connecté et opérationnel avec toutes fonctionnalités

## Changelog

Changelog:
- July 04, 2025. Initial setup and bot deployment