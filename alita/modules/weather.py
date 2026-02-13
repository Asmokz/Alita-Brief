"""Client API OpenWeatherMap."""

from typing import Optional
import requests

from alita.config import Config
from alita.utils.logger import logger

OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
OPENWEATHER_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


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


def get_hourly_forecast(ville: str = "Marseille", hours: int = 12) -> Optional[list]:
    """Récupère les prévisions horaires via l'API Forecast 5j/3h.

    Utilise l'endpoint /forecast (gratuit) qui retourne des prévisions par tranche de 3h.
    Filtre pour ne garder que les `hours` premières heures.

    Returns: Liste des prévisions avec temperature, vent, pluie, visibilite, description
    """
    try:
        params = {
            "q": f"{ville},FR",
            "appid": Config.OPENWEATHER_API_KEY,
            "units": "metric",
            "lang": "fr",
            "cnt": max(1, hours // 3 + 1),  # Nombre de tranches de 3h
        }

        response = requests.get(OPENWEATHER_FORECAST_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        forecasts = []
        for item in data.get("list", []):
            weather_main = item["weather"][0] if item.get("weather") else {}
            main = item.get("main", {})
            wind = item.get("wind", {})
            rain = item.get("rain", {})

            forecasts.append({
                "dt": item["dt"],
                "dt_txt": item.get("dt_txt", ""),
                "temperature": round(main.get("temp", 0), 1),
                "description": weather_main.get("description", "N/A"),
                "vent_vitesse": round(wind.get("speed", 0) * 3.6, 1),  # m/s → km/h
                "vent_rafales": round(wind.get("gust", 0) * 3.6, 1),
                "pluie_3h": rain.get("3h", 0),
                "pop": item.get("pop", 0),  # Probabilité de précipitation (0-1)
                "visibilite": item.get("visibility", 10000),
                "nuages": item.get("clouds", {}).get("all", 0),
            })

        return forecasts

    except requests.exceptions.RequestException as e:
        logger.error("Erreur API prévisions horaires : %s", e)
        return None
    except (KeyError, IndexError) as e:
        logger.error("Erreur parsing prévisions : %s", e)
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
