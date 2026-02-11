"""Client API OpenWeatherMap."""

from typing import Optional
import requests

from alita.config import Config
from alita.utils.logger import logger

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


def get_weather(ville: str = "Marseille") -> Optional[dict]:
    """Récupère la météo actuelle pour une ville.

    Retourne : temperature, description, vent_vitesse, pluie, humidite, icone
    """
    try:
        params = {
            "q": f"{ville},FR",
            "appid": Config.OPENWEATHER_API_KEY,
            "units": "metric",
            "lang": "fr",
        }

        response = requests.get(OPENWEATHER_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Extraction des données
        weather_main = data["weather"][0] if data.get("weather") else {}
        main = data.get("main", {})
        wind = data.get("wind", {})
        rain = data.get("rain", {})

        return {
            "ville": ville,
            "temperature": round(main.get("temp", 0), 1),
            "ressenti": round(main.get("feels_like", 0), 1),
            "description": weather_main.get("description", "N/A"),
            "icone": weather_main.get("icon", ""),
            "humidite": main.get("humidity", 0),
            "vent_vitesse": round(wind.get("speed", 0) * 3.6, 1),  # m/s → km/h
            "vent_rafales": round(wind.get("gust", 0) * 3.6, 1),
            "pluie_1h": rain.get("1h", 0),
            "nuages": data.get("clouds", {}).get("all", 0),
        }
    except requests.exceptions.RequestException as e:
        logger.error("Erreur API météo : %s", e)
        return None
    except (KeyError, IndexError) as e:
        logger.error("Erreur parsing météo : %s", e)
        return None


def get_weather_emoji(description: str) -> str:
    """Retourne un emoji correspondant à la condition météo."""
    desc = description.lower()
    if "soleil" in desc or "clair" in desc or "dégagé" in desc:
        return "☀️"
    elif "nuage" in desc or "couvert" in desc:
        return "☁️"
    elif "pluie" in desc or "averse" in desc:
        return "🌧️"
    elif "orage" in desc:
        return "⛈️"
    elif "neige" in desc:
        return "❄️"
    elif "brouillard" in desc or "brume" in desc:
        return "🌫️"
    return "🌤️"
