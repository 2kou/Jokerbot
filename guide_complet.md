# 🤖 GUIDE COMPLET - BOT TÉLÉFOOT AVANCÉ

## 📋 FONCTIONS PRINCIPALES

### 1. 🔐 GESTION DES LICENCES

#### `/start`
**Description :** Démarre le bot et vérifie votre accès
**Utilisation :** `/start`
**Exemple :**
```
Utilisateur normal : Affiche les tarifs et demande l'activation
Admin (vous) : Accès direct avec menu administrateur
```

#### `/activer`
**Description :** Active un utilisateur (admin uniquement)
**Utilisation :** `/activer <user_id> <semaine|mois>`
**Exemples :**
```
/activer 123456789 semaine    → Active pour 7 jours
/activer 987654321 mois       → Active pour 30 jours
```

#### `/status`
**Description :** Affiche le statut d'un utilisateur
**Utilisation :** 
- `/status` (votre statut)
- `/status <user_id>` (admin uniquement)
**Exemples :**
```
/status                → Votre statut personnel
/status 123456789      → Statut de l'utilisateur 123456789
```

### 2. ⚽ FONCTIONS TÉLÉFOOT

#### `/pronostics`
**Description :** Affiche les pronostics football du jour
**Utilisation :** `/pronostics`
**Contenu :**
- Pronostics Ligue 1, Premier League, Liga
- Cotes et conseils de mise
- Combos sûres
- Statistiques de performance

#### `/vip` (Ajout possible)
**Description :** Pronostics VIP avec analyses détaillées
**Utilisation :** `/vip`
**Contenu :**
- Informations privilégiées
- Analyses approfondies
- Paris à haute cote
- Stratégies avancées

#### `/statistiques` (Ajout possible)
**Description :** Performance et statistiques détaillées
**Utilisation :** `/statistiques`
**Contenu :**
- Taux de réussite par championnat
- ROI mensuel
- Historique des gains/pertes
- Meilleures séries

#### `/matchs` (Ajout possible)
**Description :** Programme des matchs
**Utilisation :** `/matchs`
**Contenu :**
- Matchs du jour et de demain
- Horaires et chaînes
- Matchs recommandés

### 3. 📡 GESTION DES CONNEXIONS

#### `/connect`
**Description :** Connecte un compte Telegram pour les redirections
**Utilisation :** `/connect <numéro>`
**Exemples :**
```
/connect +33612345678     → Connecte un numéro français
/connect +1234567890      → Connecte un numéro international
```
**Processus :**
1. Bot envoie un code SMS au numéro
2. Vous recevez : "📱 Code envoyé au +33612345678"
3. Utilisez `/code` pour confirmer

#### `/code`
**Description :** Confirme la connexion avec le code SMS
**Utilisation :** `/code <code_reçu>`
**Exemples :**
```
/code 12345      → Confirme avec le code reçu
/code 67890      → Autre exemple de code
```

### 4. 🔄 GESTION DES REDIRECTIONS

#### `/redirections`
**Description :** Affiche les redirections actives
**Utilisation :** `/redirections`
**Affichage :**
- Liste des redirections configurées
- Nombre de canaux sources/destinations
- Statut des options (édition/suppression)

#### `/add_redirect`
**Description :** Guide pour ajouter une redirection
**Utilisation :** `/add_redirect`
**Guide fourni :**
```python
add_redirection(
    name='ma_redirection',
    session='session_+33612345678',
    sources=[-1001234567890],
    destinations=[-1009876543210]
)
```

### 5. 📋 AIDE ET INFORMATION

#### `/help`
**Description :** Affiche l'aide complète
**Utilisation :** `/help`
**Contenu :**
- Toutes les commandes disponibles
- Tarifs et services
- Commandes admin (pour vous)
- Informations de contact

---

## 🔧 FONCTIONS AVANCÉES (Code)

### Configuration des Redirections

#### `add_redirection(name, session, sources, destinations)`
**Description :** Ajoute une redirection de canaux
**Paramètres :**
- `name` : Nom de la redirection
- `session` : Session du compte connecté
- `sources` : Liste des IDs de canaux sources
- `destinations` : Liste des IDs de canaux destinations

**Exemple :**
```python
add_redirection(
    name="news_redirect",
    session="session_+33612345678",
    sources=[-1001234567890, -1001111111111],
    destinations=[-1009876543210]
)
```

### Système de Filtres

#### Filtres de contenu (filters.json)
```json
{
  "ma_redirection": {
    "ignore": ["photo", "video", "audio", "text"]
  }
}
```

#### Transformations de format (format.json)
```json
{
  "ma_redirection": {
    "template": "🎯 [[Message.Text]]"
  }
}
```

#### Délais entre messages (delay.json)
```json
{
  "ma_redirection": {
    "seconds": 5
  }
}
```

#### Whitelist/Blacklist (whitelist.json, blacklist.json)
```json
{
  "ma_redirection": [
    "mot_autorisé",
    "expression.*regex"
  ]
}
```

### Transformations Avancées

#### Suppression de lignes (removeLines.json)
```json
{
  "ma_redirection": [
    "publicité",
    "spam",
    "@canal_concurrent"
  ]
}
```

#### Transformations regex (power.json)
```json
{
  "ma_redirection": [
    ["ancien_texte", "nouveau_texte"],
    ["https://t.me/\\w+", ""],
    ["\\d{10,}", "[NUMERO_MASQUE]"]
  ]
}
```

---

## 💡 EXEMPLES D'UTILISATION COMPLETS

### Exemple 1 : Activation d'un utilisateur
```
Admin : /activer 123456789 semaine
Bot : ✅ Utilisateur 123456789 activé jusqu'au 11/07/2025 15:30
→ L'utilisateur reçoit automatiquement une notification
```

### Exemple 2 : Connexion d'un compte
```
Admin : /connect +33612345678
Bot : 📱 Code envoyé au +33612345678. Utilisez /code XXXXX pour confirmer

Admin : /code 54321
Bot : ✅ Compte +33612345678 connecté avec succès !
```

### Exemple 3 : Configuration complète d'une redirection
```python
# 1. Connecter le compte
# /connect +33612345678
# /code 54321

# 2. Configurer la redirection
add_redirection(
    name="crypto_news",
    session="session_+33612345678",
    sources=[-1001234567890],  # Canal source crypto
    destinations=[-1009876543210, -1008888888888]  # Mes canaux
)

# 3. Ajouter des filtres (optionnel)
# Dans filters.json :
{
  "crypto_news": {
    "ignore": ["photo"]  # Ignore les photos
  }
}

# 4. Ajouter un format (optionnel)
# Dans format.json :
{
  "crypto_news": {
    "template": "🚀 CRYPTO NEWS: [[Message.Text]]"
  }
}
```

### Exemple 4 : Vérification du statut
```
Utilisateur : /status
Bot : 📊 Votre statut Téléfoot
     🔄 Statut : ✅ Actif
     📋 Plan : semaine
     ⏰ Expire : 11/07/2025 15:30

Admin : /status 123456789
Bot : 📊 Statut utilisateur 123456789
     🔄 Statut : ❌ Expiré
     📋 Plan : mois
     ⏰ Expire : 01/07/2025 10:00
```

---

## 🎯 COMMANDES RAPIDES (Résumé)

**👑 Admin (vous) :**
- `/activer user_id semaine/mois` - Activer des utilisateurs
- `/connect +numéro` - Connecter un compte
- `/code XXXXX` - Confirmer connexion
- `/status user_id` - Voir statut utilisateur
- `/redirections` - Gérer redirections

**👤 Utilisateurs :**
- `/start` - Démarrer
- `/pronostics` - Voir pronostics
- `/status` - Mon statut
- `/help` - Aide

**🔧 Configuration :**
- `add_redirection()` - Ajouter redirection
- Fichiers JSON pour filtres/transformations
- Sessions de comptes connectés

---

## 📞 SUPPORT

**Contact :** Sossou Kouamé
**Tarifs :** 1 semaine = 1000f | 1 mois = 3000f
**Votre ID Admin :** 1190237801 (accès total)