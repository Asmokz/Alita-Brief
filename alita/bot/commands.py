"""Définition des commandes slash Discord."""

import discord
from discord import app_commands
from discord.ext import commands

from alita.modules import portfolio, yahoo_finance, ollama_client
from alita.modules.weather import get_weather
from alita.briefing.generator import generer_briefing, get_config_value
from alita.briefing.templates import build_portfolio_list_embed
from alita.database.db import get_session
from alita.database.models import ConfigDB
from alita.utils.logger import logger
from alita.utils.helpers import format_prix, format_pourcentage


class PortfolioCog(commands.Cog):
    """Commandes de gestion du portfolio."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="portfolio", description="Gestion du portfolio")
    @app_commands.describe(
        action="Action à effectuer",
        ticker="Ticker de l'action (ex: AIR.PA)",
        nom="Nom de l'action (pour add)",
        prix_achat="Prix d'achat (pour add)",
        quantite="Quantité (pour add)",
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="add", value="add"),
        app_commands.Choice(name="remove", value="remove"),
        app_commands.Choice(name="list", value="list"),
        app_commands.Choice(name="history", value="history"),
    ])
    async def portfolio_cmd(
        self,
        interaction: discord.Interaction,
        action: str,
        ticker: str = None,
        nom: str = None,
        prix_achat: float = None,
        quantite: int = None,
    ):
        await interaction.response.defer()

        if action == "add":
            if not all([ticker, nom, prix_achat, quantite]):
                await interaction.followup.send("❌ Usage : `/portfolio add <ticker> <nom> <prix_achat> <quantite>`")
                return

            result = portfolio.ajouter_action(ticker, nom, prix_achat, quantite)
            color = 0x2ECC71 if result["ok"] else 0xE74C3C
            embed = discord.Embed(description=result["message"], color=color)
            await interaction.followup.send(embed=embed)

        elif action == "remove":
            if not ticker:
                await interaction.followup.send("❌ Usage : `/portfolio remove <ticker>`")
                return

            result = portfolio.retirer_action(ticker)
            color = 0x2ECC71 if result["ok"] else 0xE74C3C
            embed = discord.Embed(description=result["message"], color=color)
            await interaction.followup.send(embed=embed)

        elif action == "list":
            data = portfolio.lister_portfolio()
            embed = build_portfolio_list_embed(data)
            await interaction.followup.send(embed=embed)

        elif action == "history":
            if not ticker:
                await interaction.followup.send("❌ Usage : `/portfolio history <ticker>`")
                return

            transactions = portfolio.historique_transactions(ticker)
            if not transactions:
                await interaction.followup.send(f"Aucune transaction trouvée pour {ticker.upper()}")
                return

            embed = discord.Embed(
                title=f"📜 Historique {ticker.upper()}",
                color=0x3498DB,
            )
            for t in transactions[:10]:
                emoji = {"ACHAT": "🟢", "VENTE": "🔴", "MODIFICATION": "🔵"}.get(t["type"], "⚪")
                value = f"Prix : {t['prix']}€ | Qté : {t['quantite']}"
                if t["note"]:
                    value += f"\n*{t['note']}*"
                embed.add_field(
                    name=f"{emoji} {t['type']} - {t['date']}",
                    value=value,
                    inline=False,
                )
            await interaction.followup.send(embed=embed)


class ConfigCog(commands.Cog):
    """Commandes de configuration."""

    PARAMS_VALIDES = {"meteo_ville", "briefing_heure", "moto_seuil_vent", "moto_seuil_pluie"}

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="config", description="Gestion de la configuration")
    @app_commands.describe(
        action="show ou set",
        parametre="Paramètre à modifier",
        valeur="Nouvelle valeur",
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="show", value="show"),
        app_commands.Choice(name="set", value="set"),
    ])
    async def config_cmd(
        self,
        interaction: discord.Interaction,
        action: str,
        parametre: str = None,
        valeur: str = None,
    ):
        if action == "show":
            embed = discord.Embed(title="⚙️ Configuration", color=0x3498DB)
            for param in sorted(self.PARAMS_VALIDES):
                val = get_config_value(param, "N/A")
                embed.add_field(name=param, value=f"`{val}`", inline=True)
            await interaction.response.send_message(embed=embed)

        elif action == "set":
            if not parametre or not valeur:
                await interaction.response.send_message("❌ Usage : `/config set <parametre> <valeur>`")
                return

            if parametre not in self.PARAMS_VALIDES:
                await interaction.response.send_message(
                    f"❌ Paramètre invalide. Valides : {', '.join(sorted(self.PARAMS_VALIDES))}"
                )
                return

            try:
                with get_session() as session:
                    config = session.query(ConfigDB).filter_by(cle=parametre).first()
                    if config:
                        config.valeur = valeur
                    else:
                        session.add(ConfigDB(cle=parametre, valeur=valeur))

                # Replanifier si l'heure change
                if parametre == "briefing_heure" and hasattr(self.bot, "scheduler"):
                    self.bot.scheduler.reschedule(valeur)

                embed = discord.Embed(
                    description=f"✅ `{parametre}` = `{valeur}`",
                    color=0x2ECC71,
                )
                await interaction.response.send_message(embed=embed)
            except Exception as e:
                await interaction.response.send_message(f"❌ Erreur : {e}")


class TestCog(commands.Cog):
    """Commandes de test et debug."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="briefing", description="Force la génération du briefing")
    @app_commands.describe(action="now pour forcer")
    async def briefing_cmd(self, interaction: discord.Interaction, action: str = "now"):
        if action != "now":
            await interaction.response.send_message("Usage : `/briefing now`")
            return

        await interaction.response.defer()
        await interaction.followup.send("⏳ Génération du briefing en cours...")

        try:
            result = await generer_briefing()
            embeds = result.get("embeds", [])

            if embeds:
                await interaction.followup.send(embeds=embeds)
                if result.get("erreurs"):
                    await interaction.followup.send(
                        f"⚠️ Briefing généré avec {len(result['erreurs'])} erreur(s) : "
                        + ", ".join(result["erreurs"])
                    )
            else:
                await interaction.followup.send("❌ Impossible de générer le briefing")
        except Exception as e:
            logger.error("Erreur /briefing now : %s", e)
            await interaction.followup.send(f"❌ Erreur : {e}")

    @app_commands.command(name="test", description="Tests de connexion")
    @app_commands.describe(
        service="Service à tester (yahoo, ollama)",
        ticker="Ticker pour test yahoo",
    )
    @app_commands.choices(service=[
        app_commands.Choice(name="yahoo", value="yahoo"),
        app_commands.Choice(name="ollama", value="ollama"),
    ])
    async def test_cmd(self, interaction: discord.Interaction, service: str, ticker: str = None):
        await interaction.response.defer()

        if service == "yahoo":
            if not ticker:
                await interaction.followup.send("❌ Usage : `/test yahoo <ticker>`")
                return

            data = yahoo_finance.get_ticker_price(ticker)
            if data:
                emoji = "🟢" if data["variation"] >= 0 else "🔴"
                embed = discord.Embed(
                    title=f"📊 {ticker.upper()}",
                    color=0x2ECC71 if data["variation"] >= 0 else 0xE74C3C,
                )
                embed.add_field(name="Prix actuel", value=f"{data['prix_actuel']}€", inline=True)
                embed.add_field(name="Variation", value=f"{emoji} {format_pourcentage(data['variation_pct'])}", inline=True)
                embed.add_field(name="Ouverture", value=f"{data['ouverture']}€", inline=True)
                embed.add_field(name="Volume", value=f"{data['volume']:,}", inline=True)
                await interaction.followup.send(embed=embed)
            else:
                await interaction.followup.send(f"❌ Impossible de récupérer les données pour {ticker}")

        elif service == "ollama":
            result = ollama_client.test_ollama()
            color = 0x2ECC71 if result["ok"] else 0xE74C3C
            emoji = "✅" if result["ok"] else "❌"
            embed = discord.Embed(
                title=f"{emoji} Test Ollama",
                description=result["message"],
                color=color,
            )
            embed.add_field(name="Modèle", value=result["modele"], inline=True)
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="logs", description="Affiche les derniers logs")
    async def logs_cmd(self, interaction: discord.Interaction):
        try:
            with open("/app/logs/alita.log", "r", encoding="utf-8") as f:
                lines = f.readlines()
            last_lines = lines[-50:] if len(lines) > 50 else lines
            content = "".join(last_lines)

            # Découper si trop long pour Discord (max 2000 chars)
            if len(content) > 1900:
                content = content[-1900:]

            await interaction.response.send_message(f"```\n{content}\n```")
        except FileNotFoundError:
            await interaction.response.send_message("Aucun fichier de log trouvé.")
        except Exception as e:
            await interaction.response.send_message(f"❌ Erreur lecture logs : {e}")


async def setup_commands(bot: commands.Bot):
    """Enregistre tous les cogs de commandes."""
    await bot.add_cog(PortfolioCog(bot))
    await bot.add_cog(ConfigCog(bot))
    await bot.add_cog(TestCog(bot))
    logger.info("Commandes Discord enregistrées")
