"""Calcul du score moto basé sur la météo."""

from alita.utils.logger import logger


def calculer_score_moto(meteo: dict, seuil_vent: float = 20, seuil_pluie: float = 50) -> dict:
    """Calcule le score moto de 0 à 10 basé sur les conditions météo.

    Args:
        meteo: Données météo (depuis weather.get_weather)
        seuil_vent: Vitesse de vent max acceptable (km/h)
        seuil_pluie: Probabilité de pluie max acceptable (%)

    Retourne un dict avec : score, details (liste des pénalités), verdict
    """
    score = 10
    details = []

    if meteo is None:
        return {"score": 0, "details": ["❌ Données météo indisponibles"], "verdict": "Inconnu"}

    temperature = meteo.get("temperature", 20)
    vent = meteo.get("vent_vitesse", 0)
    pluie = meteo.get("pluie_1h", 0)
    nuages = meteo.get("nuages", 0)

    # Pluie
    if pluie > 0:
        score -= 4
        details.append(f"🌧️ Pluie détectée ({pluie} mm/h) : -4")
    elif nuages > seuil_pluie:
        score -= 2
        details.append(f"☁️ Couverture nuageuse élevée ({nuages}%) : -2")

    # Vent
    if vent > seuil_vent * 1.5:
        score -= 3
        details.append(f"💨 Vent très fort ({vent:.0f} km/h) : -3")
    elif vent > seuil_vent:
        score -= 2
        details.append(f"💨 Vent fort ({vent:.0f} km/h) : -2")

    # Température basse
    if temperature < 0:
        score -= 3
        details.append(f"🥶 Gel ({temperature}°C) : -3")
    elif temperature < 5:
        score -= 2
        details.append(f"🥶 Froid ({temperature}°C) : -2")

    # Température haute
    if temperature > 40:
        score -= 2
        details.append(f"🥵 Chaleur extrême ({temperature}°C) : -2")
    elif temperature > 35:
        score -= 1
        details.append(f"🥵 Forte chaleur ({temperature}°C) : -1")

    # Clamp entre 0 et 10
    score = max(0, min(10, score))

    # Verdict textuel
    if score >= 8:
        verdict = "🏍️ Conditions idéales, en selle !"
    elif score >= 6:
        verdict = "🏍️ Conditions correctes, prudence."
    elif score >= 4:
        verdict = "⚠️ Conditions médiocres, réfléchis-y."
    else:
        verdict = "❌ Mauvaises conditions, reste au chaud."

    if not details:
        details.append("✅ Aucune pénalité, conditions parfaites !")

    logger.debug("Score moto calculé : %d/10", score)

    return {
        "score": score,
        "details": details,
        "verdict": verdict,
    }
