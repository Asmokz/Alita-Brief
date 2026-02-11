"""Point d'entrée principal d'Alita Bot."""

import sys
import time

from alita.config import Config
from alita.utils.logger import logger
from alita.database.db import test_connection


def wait_for_db(max_retries: int = 30, delay: int = 2):
    """Attend que la base de données soit disponible."""
    for i in range(max_retries):
        if test_connection():
            return True
        logger.info("Attente DB... tentative %d/%d", i + 1, max_retries)
        time.sleep(delay)

    logger.error("Impossible de se connecter à la DB après %d tentatives", max_retries)
    return False


def main():
    """Démarre Alita Bot."""
    logger.info("=" * 50)
    logger.info("Démarrage Alita Bot v1.0")
    logger.info("=" * 50)

    # Vérifications de configuration
    if not Config.DISCORD_BOT_TOKEN:
        logger.error("DISCORD_BOT_TOKEN non configuré !")
        sys.exit(1)

    if not Config.OPENWEATHER_API_KEY:
        logger.warning("OPENWEATHER_API_KEY non configuré - météo désactivée")

    if not Config.DISCORD_WEBHOOK_URL:
        logger.warning("DISCORD_WEBHOOK_URL non configuré - briefing auto désactivé")

    # Attendre la DB
    logger.info("Connexion à la base de données...")
    if not wait_for_db():
        sys.exit(1)

    # Lancer le bot Discord
    logger.info("Lancement du bot Discord...")
    from alita.bot.discord_bot import run_bot
    run_bot()


if __name__ == "__main__":
    main()
