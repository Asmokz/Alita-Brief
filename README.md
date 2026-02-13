# Alita Bot - Briefing Matinal Automatisé

Bot Discord pour le homelab ASMO-01 qui génère un briefing matinal automatique avec :
- Analyse CAC40 et portfolio personnel
- Météo et score moto
- Alertes via LLM local (Ollama/Mistral 7B)

## Prérequis

- Docker & Docker Compose
- Réseau Docker `asmo-network` existant
- Ollama avec Mistral 7B sur `localhost:11434`
- Compte Discord avec bot créé

## Installation

### 1. Créer le bot Discord

1. Aller sur https://discord.com/developers/applications
2. Cliquer "New Application" → nommer "Alita"
3. Onglet "Bot" → cliquer "Add Bot"
4. Copier le **Token** du bot
5. Activer **Message Content Intent** dans "Privileged Gateway Intents"
6. Onglet "OAuth2" → "URL Generator" :
   - Scopes : `bot`, `applications.commands`
   - Bot Permissions : `Send Messages`, `Embed Links`, `Read Message History`
7. Copier l'URL générée et l'ouvrir pour inviter le bot sur votre serveur

### 2. Créer un webhook Discord

1. Dans votre serveur Discord, aller dans les paramètres du channel cible
2. Intégrations → Webhooks → Nouveau webhook
3. Copier l'URL du webhook

### 3. Obtenir une clé OpenWeatherMap

1. Créer un compte sur https://openweathermap.org/
2. Aller dans "API Keys" et copier la clé

### 4. Obtenir une clé NewsAPI (optionnel)

1. Créer un compte gratuit sur https://newsapi.org/register
2. Copier votre API key
3. Ajouter dans `.env` :
```
NEWSAPI_KEY=votre_cle_ici
```

**Limite gratuite** : 100 requêtes/jour (largement suffisant pour 1 briefing quotidien)

### 5. Configurer l'environnement

```bash
cd /home/asmo/alita-briefing
cp .env.example .env
nano .env  # Remplir les valeurs
```

Variables à configurer :
| Variable | Description |
|---|---|
| `DISCORD_BOT_TOKEN` | Token du bot Discord |
| `DISCORD_WEBHOOK_URL` | URL du webhook Discord |
| `DB_PASSWORD` | Mot de passe MariaDB |
| `DB_ROOT_PASSWORD` | Mot de passe root MariaDB |
| `OPENWEATHER_API_KEY` | Clé API OpenWeatherMap |
| `NEWSAPI_KEY` | Clé API NewsAPI.org (optionnel) |

### 6. Lancer

```bash
docker-compose up -d
```

Vérifier les logs :
```bash
docker logs -f alita
```

## Commandes Discord

### Portfolio
| Commande | Description |
|---|---|
| `/portfolio add <ticker> <nom> <prix> <qté>` | Ajouter une action |
| `/portfolio remove <ticker>` | Retirer une action (soft delete) |
| `/portfolio list` | Afficher le portfolio avec perf temps réel |
| `/portfolio history <ticker>` | Historique des transactions |

### Configuration
| Commande | Description |
|---|---|
| `/config show` | Afficher la configuration |
| `/config set <param> <valeur>` | Modifier un paramètre |

Paramètres : `meteo_ville`, `briefing_heure`, `moto_seuil_vent`, `moto_seuil_pluie`

### Tests & Debug
| Commande | Description |
|---|---|
| `/briefing now` | Forcer un briefing immédiat |
| `/test yahoo <ticker>` | Tester Yahoo Finance |
| `/test ollama` | Tester la connexion Ollama |
| `/logs` | Afficher les 50 dernières lignes de log |

## Architecture

```
alita/
├── main.py              # Point d'entrée
├── config.py            # Configuration (.env)
├── bot/                 # Bot Discord
│   ├── discord_bot.py   # Bot principal
│   └── commands.py      # Commandes slash
├── briefing/            # Génération briefing
│   ├── generator.py     # Orchestration
│   ├── scheduler.py     # Cron 7h30
│   └── templates.py     # Embeds Discord
├── modules/             # Modules métier
│   ├── portfolio.py     # Logique portfolio
│   ├── yahoo_finance.py # API Yahoo Finance
│   ├── weather.py       # API OpenWeatherMap
│   ├── moto_score.py    # Calcul score moto
│   ├── news_api.py      # Client NewsAPI.org
│   └── ollama_client.py # Client LLM local
├── database/            # Base de données
│   ├── models.py        # Modèles SQLAlchemy
│   └── db.py            # Connexion
└── utils/               # Utilitaires
    ├── logger.py        # Logs avec rotation
    └── helpers.py       # Fonctions helpers
```

## Troubleshooting

### Le bot ne se connecte pas
- Vérifier `DISCORD_BOT_TOKEN` dans `.env`
- Vérifier que le bot est invité sur le serveur
- Vérifier les intents activés sur le portail développeur Discord

### Les commandes slash n'apparaissent pas
- Attendre quelques minutes (synchronisation Discord)
- Vérifier les permissions du bot (scope `applications.commands`)

### Erreur connexion DB
- Vérifier que le container `alita-db` est running : `docker ps`
- Vérifier les credentials dans `.env`

### Ollama ne répond pas
- Vérifier qu'Ollama tourne : `curl http://localhost:11434/api/tags`
- Vérifier que le modèle est installé : `ollama list`
- Le `extra_hosts` dans docker-compose permet l'accès via `host.docker.internal`

### Erreur Yahoo Finance
- Certains tickers peuvent être temporairement indisponibles
- Vérifier le format du ticker (ex: `AIR.PA` pour Euronext Paris)

### Briefing ne s'envoie pas
- Vérifier `DISCORD_WEBHOOK_URL` dans `.env`
- Consulter les logs : `docker logs alita` ou `/logs`
