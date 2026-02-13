"""Calcul du score moto basé sur la météo avec analyse des prévisions 8h-19h."""

from datetime import datetime
from typing import Optional

from alita.utils.logger import logger


def _extraire_pire_conditions(hourly_forecast: list) -> dict:
    """Analyse les prévisions horaires entre 8h et 19h pour trouver les pires conditions.

    Retourne un dict avec les pires valeurs de la journée de travail.
    """
    pire = {
        "pluie_max": 0,
        "pop_max": 0,  # Probabilité de précipitation max (0-1)
        "vent_max": 0,
        "temp_min": 50,
        "temp_max": -50,
        "visibilite_min": 10000,
    }

    for h in hourly_forecast:
        # Filtrer sur la plage 8h-19h
        dt_txt = h.get("dt_txt", "")
        if dt_txt:
            try:
                heure = datetime.strptime(dt_txt, "%Y-%m-%d %H:%M:%S").hour
            except ValueError:
                continue
            if heure < 8 or heure > 19:
                continue

        pluie = h.get("pluie_3h", 0)
        pop = h.get("pop", 0)
        vent = h.get("vent_vitesse", 0)
        temp = h.get("temperature", 20)
        visi = h.get("visibilite", 10000)

        pire["pluie_max"] = max(pire["pluie_max"], pluie)
        pire["pop_max"] = max(pire["pop_max"], pop)
        pire["vent_max"] = max(pire["vent_max"], vent)
        pire["temp_min"] = min(pire["temp_min"], temp)
        pire["temp_max"] = max(pire["temp_max"], temp)
        pire["visibilite_min"] = min(pire["visibilite_min"], visi)

    return pire


def calculer_score_moto(meteo: dict, hourly_forecast: Optional[list] = None,
                        seuil_vent: float = 20, seuil_pluie: float = 50) -> dict:
    """Calcule le score moto de 0 à 10 basé sur les conditions météo.

    Analyse les prévisions 8h-19h si disponibles, sinon se base sur la météo actuelle.
    La pluie est RÉDHIBITOIRE (score automatique à 0).

    Args:
        meteo: Données météo actuelles (depuis weather.get_weather)
        hourly_forecast: Prévisions horaires (depuis weather.get_hourly_forecast)
        seuil_vent: Vitesse de vent max acceptable (km/h) - conservé pour compatibilité
        seuil_pluie: Probabilité de pluie max acceptable (%) - conservé pour compatibilité

    Retourne un dict avec : score, details (liste des pénalités), verdict
    """
    score = 10
    details = []

    if meteo is None:
        return {"score": 0, "details": ["❌ Données météo indisponibles"], "verdict": "🚫 NON - Conditions dangereuses"}

    # Déterminer les conditions à évaluer (prévisions 8h-19h ou météo actuelle)
    if hourly_forecast:
        pire = _extraire_pire_conditions(hourly_forecast)
        pluie = pire["pluie_max"]
        pop = pire["pop_max"] * 100  # Convertir en pourcentage
        vent = pire["vent_max"]
        temp_min = pire["temp_min"]
        temp_max = pire["temp_max"]
        visibilite = pire["visibilite_min"]
        source = "prévisions 8h-19h"
    else:
        pluie = meteo.get("pluie_1h", 0)
        pop = 0
        vent = meteo.get("vent_vitesse", 0)
        temp_min = meteo.get("temperature", 20)
        temp_max = temp_min
        visibilite = 10000
        source = "météo actuelle"

    logger.debug("Score moto basé sur %s", source)

    # === PLUIE = RÉDHIBITOIRE ===
    if pluie > 0.5 or pop > 40:
        raisons = []
        if pluie > 0.5:
            raisons.append(f"{pluie:.1f} mm")
        if pop > 40:
            raisons.append(f"{pop:.0f}% probabilité")

        return {
            "score": 0,
            "details": [f"☔ PLUIE prévue ({', '.join(raisons)}) - Condition rédhibitoire"],
            "verdict": "🚫 NON - Conditions dangereuses",
        }

    # === PÉNALITÉS (si pas de pluie) ===

    # Vent
    if vent > 40:
        score -= 4
        details.append(f"💨 Vent très fort ({vent:.0f} km/h) : -4")
    elif vent > 25:
        score -= 2
        details.append(f"💨 Vent fort ({vent:.0f} km/h) : -2")

    # Température basse (risque verglas)
    if temp_min < 3:
        score -= 3
        details.append(f"🥶 Risque verglas ({temp_min:.0f}°C) : -3")
    elif temp_min < 8:
        score -= 1
        details.append(f"🥶 Froid ({temp_min:.0f}°C) : -1")

    # Température haute
    if temp_max > 35:
        score -= 1
        details.append(f"🥵 Forte chaleur ({temp_max:.0f}°C) : -1")

    # Brouillard
    if visibilite < 1000:
        score -= 2
        details.append(f"🌫️ Brouillard (visibilité {visibilite}m) : -2")

    # Clamp entre 0 et 10
    score = max(0, min(10, score))

    # Verdict selon le score
    if score == 0:
        verdict = "🚫 NON - Conditions dangereuses"
    elif score <= 3:
        verdict = "⚠️ DÉCONSEILLÉ - Risques élevés"
    elif score <= 6:
        verdict = "🤔 MITIGÉ - À toi de voir"
    elif score <= 8:
        verdict = "✅ OK - Conditions correctes"
    else:
        verdict = "🌟 PARFAIT - Fonce !"

    if not details:
        details.append("✅ Aucune pénalité, conditions parfaites !")

    logger.debug("Score moto calculé : %d/10 (%s)", score, source)

    return {
        "score": score,
        "details": details,
        "verdict": verdict,
    }
