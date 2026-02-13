"""Module de récupération d'actualités via NewsAPI.org."""

import logging
import requests
from typing import List, Dict
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class NewsAPI:
    """Client pour NewsAPI.org (free tier : 100 requêtes/jour)."""

    BASE_URL = "https://newsapi.org/v2"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_top_headlines(self, category: str = "general", country: str = "fr", max_results: int = 3) -> List[Dict]:
        """Récupère les headlines importantes.

        Categories : general, technology, business, science

        Returns: Liste d'articles avec title, description, url, source
        """
        try:
            url = f"{self.BASE_URL}/top-headlines"
            params = {
                "apiKey": self.api_key,
                "country": country,
                "category": category,
                "pageSize": max_results,
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            articles = data.get("articles", [])

            return [
                {
                    "title": article["title"],
                    "description": article.get("description", ""),
                    "url": article["url"],
                    "source": article["source"]["name"],
                    "published_at": article["publishedAt"],
                }
                for article in articles
                if article.get("title") and article.get("url")
            ]

        except requests.exceptions.RequestException as e:
            logger.error("Erreur NewsAPI : %s", e)
            return []

    def get_tech_ai_news(self, max_results: int = 2) -> List[Dict]:
        """Récupère les news tech/IA spécifiquement.

        Recherche sur mots-clés : AI, artificial intelligence, machine learning
        """
        try:
            url = f"{self.BASE_URL}/everything"

            yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

            params = {
                "apiKey": self.api_key,
                "q": 'AI OR "artificial intelligence" OR "machine learning"',
                "language": "en",
                "sortBy": "popularity",
                "from": yesterday,
                "pageSize": max_results,
            }

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            articles = data.get("articles", [])

            return [
                {
                    "title": article["title"],
                    "description": article.get("description", ""),
                    "url": article["url"],
                    "source": article["source"]["name"],
                }
                for article in articles
                if article.get("title") and article.get("url")
            ]

        except requests.exceptions.RequestException as e:
            logger.error("Erreur NewsAPI tech : %s", e)
            return []
