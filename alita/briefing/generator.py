"""Orchestration de la génération du briefing matinal."""

import traceback
from datetime import datetime

import discord
import requests

from alita.config import Config
from alita.database.db import get_session
from alita.database.models import BriefingLog, ConfigDB
from alita.modules import yahoo_finance, weather, moto_score, ollama_client, portfolio
from alita.briefing.templates import build_briefing_embed
from alita.utils.logger import logger
from alita.utils.helpers import tronquer


def get_config_value(cle: str, defaut: str = "") -> str:
    """Récupère une valeur de configuration depuis la DB."""
    try:
        with get_session() as session:
            config = session.query(ConfigDB).filter_by(cle=cle).first()
            return config.valeur if config else defaut
    except Exception:
        return defaut


async def generer_briefing() -> dict:
    """Génère le briefing complet.

    Retourne un dict avec : ok, embeds, erreurs
    """
    erreurs = []
    logger.info("=== Début génération briefing ===")

    # 1. Données CAC40
    logger.info("Récupération données CAC40...")
    try:
        cac40_data = yahoo_finance.get_cac40_movers()
    except Exception as e:
        logger.error("Erreur CAC40 : %s", e)
        cac40_data = {"top_gainers": [], "top_losers": [], "performance_globale": 0}
        erreurs.append(f"CAC40 : {e}")

    # 2. Analyse LLM du CAC40 (avec fallback)
    analyse_cac40_text = None
    if cac40_data.get("top_gainers"):
        logger.info("Génération analyse CAC40 via Ollama...")
        try:
            analyse_cac40_text = ollama_client.analyse_cac40(
                cac40_data["performance_globale"],
                cac40_data["top_gainers"],
                cac40_data["top_losers"],
            )
        except Exception as e:
            logger.warning("Ollama CAC40 échoué (fallback sans analyse) : %s", e)
            erreurs.append(f"Ollama CAC40 : {e}")

    if not analyse_cac40_text:
        analyse_cac40_text = "*Analyse IA indisponible*"

    # 3. Portfolio
    logger.info("Récupération portfolio...")
    try:
        portfolio_data = portfolio.get_portfolio_pour_briefing()
    except Exception as e:
        logger.error("Erreur portfolio : %s", e)
        portfolio_data = {"actions": [], "total_investi": 0, "total_actuel": 0, "gain_total": 0, "gain_pct": 0}
        erreurs.append(f"Portfolio : {e}")

    # 4. Alertes LLM sur portfolio (avec fallback)
    alertes_text = None
    if portfolio_data.get("actions"):
        logger.info("Génération alertes portfolio via Ollama...")
        try:
            # Préparer les données pour le LLM
            pf_summary = "\n".join(
                f"{a['ticker']} ({a['nom']}) : {a['quantite']}x, achat {a['prix_achat']}€, "
                f"actuel {a['prix_actuel']}€, variation jour {a['variation_jour']:+.2f}%"
                for a in portfolio_data["actions"]
            )

            # Historique 5j pour chaque action
            hist_summary = ""
            for a in portfolio_data["actions"]:
                hist = yahoo_finance.get_ticker_history(a["ticker"], "5d")
                if hist:
                    hist_lines = ", ".join(f"{h['date']}: {h['cloture']}€" for h in hist)
                    hist_summary += f"{a['ticker']} : {hist_lines}\n"

            alertes_text = ollama_client.analyse_portfolio_alertes(pf_summary, hist_summary)
        except Exception as e:
            logger.warning("Ollama alertes échoué : %s", e)
            erreurs.append(f"Ollama alertes : {e}")

    # 5. Météo
    ville = get_config_value("meteo_ville", "Marseille")
    logger.info("Récupération météo pour %s...", ville)
    try:
        meteo_data = weather.get_weather(ville)
    except Exception as e:
        logger.error("Erreur météo : %s", e)
        meteo_data = None
        erreurs.append(f"Météo : {e}")

    # 6. Score moto
    seuil_vent = float(get_config_value("moto_seuil_vent", "20"))
    seuil_pluie = float(get_config_value("moto_seuil_pluie", "50"))
    moto_data = moto_score.calculer_score_moto(meteo_data, seuil_vent, seuil_pluie)

    # 7. Construction des embeds
    logger.info("Construction des embeds Discord...")
    embeds = build_briefing_embed(
        cac40_data=cac40_data,
        analyse_cac40=analyse_cac40_text,
        portfolio_data=portfolio_data,
        alertes=alertes_text,
        meteo=meteo_data,
        moto_score=moto_data,
    )

    logger.info("=== Briefing généré avec succès (%d embeds, %d erreurs) ===", len(embeds), len(erreurs))

    return {
        "ok": len(erreurs) == 0,
        "embeds": embeds,
        "erreurs": erreurs,
    }


async def envoyer_briefing_webhook(embeds: list[discord.Embed]) -> bool:
    """Envoie le briefing via Discord webhook.

    Retourne True si l'envoi est réussi.
    """
    webhook_url = Config.DISCORD_WEBHOOK_URL

    if not webhook_url:
        logger.error("DISCORD_WEBHOOK_URL non configuré")
        return False

    try:
        webhook = discord.SyncWebhook.from_url(webhook_url)
        webhook.send(
            username="Alita Briefing",
            embeds=embeds,
        )
        logger.info("Briefing envoyé via webhook")
        return True
    except Exception as e:
        logger.error("Erreur envoi webhook : %s", e)
        return False


async def run_briefing():
    """Exécute le briefing complet : génération + envoi + log."""
    try:
        result = await generer_briefing()
        embeds = result.get("embeds", [])

        if embeds:
            envoi_ok = await envoyer_briefing_webhook(embeds)
        else:
            envoi_ok = False

        # Log en DB
        contenu = f"{len(embeds)} embeds, erreurs: {result.get('erreurs', [])}"
        log_briefing(
            statut="SUCCESS" if envoi_ok else "ERREUR",
            contenu=contenu,
            erreur="; ".join(result.get("erreurs", [])) if not envoi_ok else None,
        )

        if result.get("erreurs"):
            logger.warning("Briefing envoyé avec %d erreurs : %s", len(result["erreurs"]), result["erreurs"])

    except Exception as e:
        logger.error("Erreur critique briefing : %s\n%s", e, traceback.format_exc())
        log_briefing(statut="ERREUR", erreur=str(e))

        # Notification d'erreur critique via webhook
        try:
            await envoyer_erreur_critique(str(e))
        except Exception:
            pass


def log_briefing(statut: str, contenu: str = None, erreur: str = None):
    """Enregistre un log de briefing en DB."""
    try:
        with get_session() as session:
            log = BriefingLog(
                date_envoi=datetime.utcnow(),
                contenu=contenu,
                statut=statut,
                message_erreur=erreur,
            )
            session.add(log)
    except Exception as e:
        logger.error("Erreur log briefing DB : %s", e)


async def envoyer_erreur_critique(erreur: str):
    """Envoie une notification d'erreur critique via webhook."""
    webhook_url = Config.DISCORD_WEBHOOK_URL
    if not webhook_url:
        return

    embed = discord.Embed(
        title="🚨 Erreur Critique Alita",
        description=f"```\n{tronquer(erreur, 2000)}\n```",
        color=0xE74C3C,
    )
    embed.set_footer(text="Vérifiez les logs : /logs")

    try:
        webhook = discord.SyncWebhook.from_url(webhook_url)
        webhook.send(username="Alita Alertes", embeds=[embed])
    except Exception as e:
        logger.error("Impossible d'envoyer l'alerte critique : %s", e)
