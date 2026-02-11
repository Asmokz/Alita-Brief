"""Bot Discord principal."""

import discord
from discord.ext import commands

from alita.config import Config
from alita.bot.commands import setup_commands
from alita.briefing.scheduler import BriefingScheduler
from alita.database.db import test_connection
from alita.utils.logger import logger


class AlitaBot(commands.Bot):
    """Bot Discord Alita avec scheduler intégré."""

    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True

        super().__init__(
            command_prefix="!",
            intents=intents,
            description="Alita - Briefing matinal automatisé",
        )

        self.scheduler: BriefingScheduler | None = None

    async def setup_hook(self):
        """Appelé au démarrage du bot."""
        # Enregistrer les commandes slash
        await setup_commands(self)

        # Synchroniser les commandes avec Discord
        try:
            synced = await self.tree.sync()
            logger.info("%d commandes synchronisées avec Discord", len(synced))
        except Exception as e:
            logger.error("Erreur sync commandes : %s", e)

    async def on_ready(self):
        """Appelé quand le bot est connecté et prêt."""
        logger.info("Bot connecté en tant que %s (ID: %s)", self.user.name, self.user.id)

        # Tester la connexion DB
        if test_connection():
            logger.info("Connexion DB OK")
        else:
            logger.error("Connexion DB échouée !")

        # Démarrer le scheduler
        self.scheduler = BriefingScheduler(self.loop)
        self.scheduler.start()

        # Statut du bot
        await self.change_presence(
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name="les marchés 📊",
            )
        )

        logger.info("Alita Bot prêt !")

    async def on_command_error(self, ctx, error):
        """Gestion globale des erreurs de commandes."""
        if isinstance(error, commands.CommandNotFound):
            return
        logger.error("Erreur commande : %s", error)

    async def close(self):
        """Nettoyage à l'arrêt du bot."""
        if self.scheduler:
            self.scheduler.stop()
        await super().close()
        logger.info("Bot arrêté proprement")


def run_bot():
    """Lance le bot Discord."""
    token = Config.DISCORD_BOT_TOKEN

    if not token:
        logger.error("DISCORD_BOT_TOKEN non défini !")
        raise ValueError("DISCORD_BOT_TOKEN manquant dans la configuration")

    bot = AlitaBot()
    bot.run(token, log_handler=None)  # On gère nos propres logs
