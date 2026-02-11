"""Fonctions utilitaires."""

from datetime import datetime
import pytz

from alita.config import Config


def now_paris() -> datetime:
    """Retourne l'heure actuelle en timezone Paris."""
    tz = pytz.timezone(Config.TIMEZONE)
    return datetime.now(tz)


def format_prix(prix: float) -> str:
    """Formate un prix en euros."""
    return f"{prix:,.2f} €".replace(",", " ").replace(".", ",")


def format_pourcentage(valeur: float) -> str:
    """Formate un pourcentage avec signe et couleur emoji."""
    signe = "+" if valeur >= 0 else ""
    return f"{signe}{valeur:.2f}%"


def couleur_variation(valeur: float) -> int:
    """Retourne un code couleur Discord selon la variation."""
    if valeur > 0:
        return 0x2ECC71  # Vert
    elif valeur < 0:
        return 0xE74C3C  # Rouge
    return 0x3498DB  # Bleu


def tronquer(texte: str, max_len: int = 1024) -> str:
    """Tronque un texte pour respecter les limites Discord embed."""
    if len(texte) <= max_len:
        return texte
    return texte[: max_len - 3] + "..."
