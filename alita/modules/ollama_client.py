"""Client pour l'API Ollama (LLM local)."""

from typing import Optional
import requests

from alita.config import Config
from alita.utils.logger import logger


def generate(prompt: str, temperature: float = 0.3) -> Optional[str]:
    """Envoie un prompt à Ollama et retourne la réponse.

    Args:
        prompt: Le prompt à envoyer
        temperature: Température de génération (0.0 = déterministe, 1.0 = créatif)

    Retourne la réponse texte ou None en cas d'erreur.
    """
    url = f"{Config.OLLAMA_HOST}/api/generate"

    payload = {
        "model": Config.OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": temperature,
            "num_predict": 500,
        },
    }

    try:
        response = requests.post(url, json=payload, timeout=Config.OLLAMA_TIMEOUT)
        response.raise_for_status()

        data = response.json()
        result = data.get("response", "").strip()

        if not result:
            logger.warning("Ollama a retourné une réponse vide")
            return None

        logger.info("Réponse Ollama reçue (%d caractères)", len(result))
        return result

    except requests.exceptions.Timeout:
        logger.error("Timeout Ollama après %ds", Config.OLLAMA_TIMEOUT)
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Impossible de se connecter à Ollama (%s)", Config.OLLAMA_HOST)
        return None
    except requests.exceptions.RequestException as e:
        logger.error("Erreur Ollama : %s", e)
        return None


def test_ollama() -> dict:
    """Teste la connexion à Ollama.

    Retourne un dict avec : ok (bool), message, modele
    """
    try:
        # Vérifier que le serveur répond
        url = f"{Config.OLLAMA_HOST}/api/tags"
        response = requests.get(url, timeout=5)
        response.raise_for_status()

        data = response.json()
        modeles = [m["name"] for m in data.get("models", [])]

        if Config.OLLAMA_MODEL not in modeles:
            # Vérifier aussi avec le tag complet (ex: mistral:7b vs mistral:7b-instruct)
            model_base = Config.OLLAMA_MODEL.split(":")[0]
            modeles_base = [m.split(":")[0] for m in modeles]
            if model_base not in modeles_base:
                return {
                    "ok": False,
                    "message": f"Modèle {Config.OLLAMA_MODEL} non trouvé. Disponibles : {', '.join(modeles)}",
                    "modele": Config.OLLAMA_MODEL,
                }

        # Test de génération rapide
        test_result = generate("Dis 'OK' en un mot.")
        if test_result:
            return {
                "ok": True,
                "message": f"Ollama OK - Modèle {Config.OLLAMA_MODEL} fonctionnel",
                "modele": Config.OLLAMA_MODEL,
            }
        else:
            return {
                "ok": False,
                "message": "Ollama connecté mais génération échouée",
                "modele": Config.OLLAMA_MODEL,
            }

    except requests.exceptions.RequestException as e:
        return {
            "ok": False,
            "message": f"Connexion Ollama échouée : {e}",
            "modele": Config.OLLAMA_MODEL,
        }


def analyse_cac40(cac40_perf: float, top_gainers: list, top_losers: list) -> Optional[str]:
    """Génère une analyse CAC40 via LLM.

    Args:
        cac40_perf: Performance globale en %
        top_gainers: Liste des 5 meilleures performances
        top_losers: Liste des 5 pires performances

    Retourne l'analyse texte ou None.
    """
    gainers_str = "\n".join(
        f"  - {g['ticker']} : {g['variation_pct']:+.2f}% ({g['prix_actuel']}€)"
        for g in top_gainers
    )
    losers_str = "\n".join(
        f"  - {l['ticker']} : {l['variation_pct']:+.2f}% ({l['prix_actuel']}€)"
        for l in top_losers
    )

    prompt = f"""Tu es un analyste financier concis qui s'adresse à un investisseur particulier.

Données CAC40 hier :
- Performance globale : {cac40_perf:+.2f}%
- Top 5 hausses :
{gainers_str}
- Top 5 baisses :
{losers_str}

Mission :
1. Résume en 2-3 phrases le contexte macro
2. Identifie 2 opportunités d'achat parmi les baisses (explique pourquoi)
3. Signale 1 action à éviter (piège à valeur)

Format : bullet points, factuel, actionnable. Réponds en français."""

    return generate(prompt, temperature=0.3)


def analyse_portfolio_alertes(portfolio_data: str, historical_prices: str) -> Optional[str]:
    """Génère des alertes sur le portfolio via LLM.

    Args:
        portfolio_data: Tableau du portfolio actuel
        historical_prices: Historique 5 jours des prix

    Retourne les alertes texte ou None.
    """
    prompt = f"""Analyse ce portfolio d'un investisseur particulier :

{portfolio_data}

Historique 5 derniers jours :
{historical_prices}

Détecte :
- Mouvements anormaux (variation > ±2% par rapport à la moyenne 5 jours)
- Signaux d'alerte importants

Format : "⚠️ [Action] : [Raison courte]"
Maximum 3 alertes, uniquement si critiques.
Si rien d'anormal, écris "✅ Aucune alerte critique."
Réponds en français."""

    return generate(prompt, temperature=0.2)
