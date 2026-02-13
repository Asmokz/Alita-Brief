"""Gestion de la configuration via variables d'environnement."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration centralisée de l'application."""

    # Discord
    DISCORD_BOT_TOKEN: str = os.getenv("DISCORD_BOT_TOKEN", "")
    DISCORD_WEBHOOK_URL: str = os.getenv("DISCORD_WEBHOOK_URL", "")

    # Base de données
    DB_HOST: str = os.getenv("DB_HOST", "alita-db")
    DB_PORT: int = int(os.getenv("DB_PORT", "3306"))
    DB_USER: str = os.getenv("DB_USER", "root")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    DB_NAME: str = os.getenv("DB_NAME", "alita_db")

    @classmethod
    def get_db_url(cls) -> str:
        """Retourne l'URL de connexion SQLAlchemy."""
        return (
            f"mysql+pymysql://{cls.DB_USER}:{cls.DB_PASSWORD}"
            f"@{cls.DB_HOST}:{cls.DB_PORT}/{cls.DB_NAME}"
            f"?charset=utf8mb4"
        )

    # APIs
    OPENWEATHER_API_KEY: str = os.getenv("OPENWEATHER_API_KEY", "")
    NEWSAPI_KEY: str = os.getenv("NEWSAPI_KEY", "")

    # Ollama
    OLLAMA_HOST: str = os.getenv("OLLAMA_HOST", "http://host.docker.internal:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "mistral:7b")
    OLLAMA_TIMEOUT: int = int(os.getenv("OLLAMA_TIMEOUT", "60"))

    # Config générale
    TIMEZONE: str = os.getenv("TIMEZONE", "Europe/Paris")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
