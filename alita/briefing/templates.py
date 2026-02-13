"""Templates de messages Discord pour le briefing."""

import discord
from datetime import datetime

from alita.utils.helpers import format_prix, format_pourcentage, couleur_variation


def build_briefing_embed(
    cac40_data: dict,
    analyse_cac40: str,
    portfolio_data: dict,
    alertes: str,
    meteo: dict,
    moto_score: dict,
    world_news: list = None,
    tech_news: list = None,
) -> list[discord.Embed]:
    """Construit les embeds Discord pour le briefing matinal.

    Retourne une liste d'embeds (Discord limite à 6000 chars par embed).
    """
    embeds = []
    maintenant = datetime.now().strftime("%d/%m/%Y à %H:%M")

    # --- Embed 1 : Header + CAC40 ---
    embed_cac = discord.Embed(
        title="📊 Briefing Matinal Alita",
        description=f"*{maintenant}*",
        color=couleur_variation(cac40_data.get("performance_globale", 0)),
    )

    # Résumé CAC40
    perf = cac40_data.get("performance_globale", 0)
    cac_text = f"**Performance globale : {format_pourcentage(perf)}**\n\n"

    if cac40_data.get("top_gainers"):
        cac_text += "**🟢 Top Hausses :**\n"
        for g in cac40_data["top_gainers"][:5]:
            nom = g.get("nom", g["ticker"])
            cac_text += f"` {nom:>16} ` {format_pourcentage(g['variation_pct'])} ({g['prix_actuel']}€)\n"

    if cac40_data.get("top_losers"):
        cac_text += "\n**🔴 Top Baisses :**\n"
        for l in cac40_data["top_losers"][:5]:
            nom = l.get("nom", l["ticker"])
            cac_text += f"` {nom:>16} ` {format_pourcentage(l['variation_pct'])} ({l['prix_actuel']}€)\n"

    embed_cac.add_field(name="📈 CAC40", value=cac_text[:1024], inline=False)

    # Analyse LLM
    if analyse_cac40:
        embed_cac.add_field(
            name="🤖 Analyse IA",
            value=analyse_cac40[:1024],
            inline=False,
        )

    embeds.append(embed_cac)

    # --- Embed 2 : Portfolio ---
    embed_pf = discord.Embed(
        title="💼 Portfolio Personnel",
        color=couleur_variation(portfolio_data.get("gain_total", 0)),
    )

    if portfolio_data.get("actions"):
        # Détail par action (format visuel amélioré)
        portfolio_field = ""
        for a in portfolio_data["actions"]:
            if a["gain_pct"] > 0:
                icon = "🟢"
            elif a["gain_pct"] < 0:
                icon = "🔴"
            else:
                icon = "⚪"

            portfolio_field += f"{icon} **{a['nom']}** ({a['ticker']})\n"
            portfolio_field += f"├─ Achat: {a['prix_achat']:.2f}€ x {a['quantite']}\n"
            portfolio_field += f"├─ Actuel: {a['prix_actuel']:.2f}€\n"
            portfolio_field += f"└─ Perf: {format_prix(a['gain'])} ({format_pourcentage(a['gain_pct'])})\n\n"

        # Résumé global
        portfolio_field += f"💰 **Total Portefeuille**\n"
        portfolio_field += f"Investi: {format_prix(portfolio_data['total_investi'])}\n"
        portfolio_field += f"Valeur actuelle: {format_prix(portfolio_data['total_actuel'])}\n"
        portfolio_field += f"Performance: {format_prix(portfolio_data['gain_total'])} ({format_pourcentage(portfolio_data['gain_pct'])})"

        embed_pf.add_field(name="💼 Mon Portefeuille PEA", value=portfolio_field[:1024], inline=False)

        # Performance 24h (champ séparé)
        perf_jour = ""
        for a in portfolio_data["actions"]:
            variation_jour = a.get("variation_jour", 0)
            if variation_jour > 0:
                perf_jour += f"🟢 {a['nom']}: +{variation_jour:.2f}%\n"
            elif variation_jour < 0:
                perf_jour += f"🔴 {a['nom']}: {variation_jour:.2f}%\n"
            else:
                perf_jour += f"⚪ {a['nom']}: stable\n"

        if perf_jour:
            embed_pf.add_field(name="📊 Performance 24h", value=perf_jour[:1024], inline=False)
    else:
        embed_pf.add_field(name="Info", value="Portfolio vide. Utilisez `/portfolio add` pour commencer.", inline=False)

    embeds.append(embed_pf)

    # --- Embed 3 : Alertes ---
    if alertes:
        embed_alertes = discord.Embed(
            title="🚨 Alertes & Points d'Attention",
            description=alertes[:4096],
            color=0xF39C12,
        )
        embeds.append(embed_alertes)

    # --- Embed 4 : Météo + Moto ---
    embed_meteo = discord.Embed(
        title="🌦️ Météo & Score Moto",
        color=0x3498DB,
    )

    if meteo:
        from alita.modules.weather import get_weather_emoji
        emoji = get_weather_emoji(meteo.get("description", ""))

        meteo_text = (
            f"{emoji} **{meteo['description'].capitalize()}**\n"
            f"🌡️ {meteo['temperature']}°C (ressenti {meteo['ressenti']}°C)\n"
            f"💨 Vent : {meteo['vent_vitesse']} km/h\n"
            f"💧 Humidité : {meteo['humidite']}%\n"
        )
        if meteo.get("pluie_1h", 0) > 0:
            meteo_text += f"🌧️ Pluie : {meteo['pluie_1h']} mm/h\n"

        embed_meteo.add_field(
            name=f"📍 {meteo['ville']}",
            value=meteo_text,
            inline=True,
        )

    if moto_score:
        score_bar = "🟩" * moto_score["score"] + "⬜" * (10 - moto_score["score"])
        moto_text = (
            f"**{score_bar} {moto_score['score']}/10**\n\n"
            f"{moto_score['verdict']}\n\n"
        )
        moto_text += "\n".join(moto_score["details"])

        embed_meteo.add_field(
            name="🏍️ Score Moto",
            value=moto_text[:1024],
            inline=True,
        )

    embeds.append(embed_meteo)

    # --- Embed 5 : Actualités (si disponibles) ---
    if world_news or tech_news:
        embed_news = discord.Embed(
            title="📰 Actualités du jour",
            color=0x9B59B6,
        )

        if world_news:
            world_field = ""
            for article in world_news[:2]:
                world_field += f"📰 **{article['title']}**\n"
                world_field += f"_{article['source']}_\n"
                world_field += f"[Lire l'article]({article['url']})\n\n"
            embed_news.add_field(name="🌍 Actualités Mondiales", value=world_field[:1024], inline=False)

        if tech_news:
            tech_field = ""
            for article in tech_news[:2]:
                tech_field += f"🤖 **{article['title']}**\n"
                tech_field += f"_{article['source']}_\n"
                tech_field += f"[Lire l'article]({article['url']})\n\n"
            embed_news.add_field(name="🚀 Tech & IA", value=tech_field[:1024], inline=False)

        embeds.append(embed_news)

    # Footer sur le dernier embed
    embeds[-1].set_footer(text="Alita Bot v1.0 | ASMO-01 Homelab")

    return embeds


def build_portfolio_list_embed(portfolio_data: dict) -> discord.Embed:
    """Construit un embed pour la commande /portfolio list."""
    embed = discord.Embed(
        title="💼 Portfolio",
        color=couleur_variation(portfolio_data.get("gain_total", 0)),
    )

    if not portfolio_data.get("actions"):
        embed.description = "Portfolio vide."
        return embed

    for a in portfolio_data["actions"]:
        emoji = "🟢" if a["gain"] >= 0 else "🔴"
        embed.add_field(
            name=f"{emoji} {a['ticker']} - {a['nom']}",
            value=(
                f"**Qté :** {a['quantite']} | **Achat :** {a['prix_achat']}€ | **Actuel :** {a['prix_actuel']}€\n"
                f"**Jour :** {format_pourcentage(a['variation_jour'])} | "
                f"**Total :** {format_pourcentage(a['gain_pct'])} ({format_prix(a['gain'])})"
            ),
            inline=False,
        )

    embed.add_field(
        name="📊 Total",
        value=(
            f"Investi : {format_prix(portfolio_data['total_investi'])} | "
            f"Actuel : {format_prix(portfolio_data['total_actuel'])} | "
            f"**{format_pourcentage(portfolio_data['gain_pct'])}** ({format_prix(portfolio_data['gain_total'])})"
        ),
        inline=False,
    )

    return embed
