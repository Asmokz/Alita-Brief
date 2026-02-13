"""Client Yahoo Finance via yfinance."""

import time
from typing import Optional
import yfinance as yf

from alita.utils.logger import logger

# Liste complète des tickers CAC40
CAC40_TICKERS = [
    "AIR.PA", "AI.PA", "ALO.PA", "MT.PA", "CS.PA",
    "BNP.PA", "EN.PA", "CAP.PA", "CA.PA", "ACA.PA",
    "BN.PA", "DSY.PA", "ENGI.PA", "EL.PA", "ERF.PA",
    "RMS.PA", "KER.PA", "LR.PA", "OR.PA", "MC.PA",
    "ML.PA", "ORA.PA", "RI.PA", "PUB.PA", "RNO.PA",
    "SAF.PA", "SGO.PA", "SAN.PA", "SU.PA", "GLE.PA",
    "STLAP.PA", "STMPA.PA", "TEP.PA", "HO.PA", "TTE.PA",
    "URW.PA", "VIE.PA", "DG.PA", "VIV.PA", "WLN.PA",
]

# Mapping ticker → nom complet pour affichage lisible
CAC40_NAMES = {
    "AIR.PA": "Airbus",
    "AI.PA": "Air Liquide",
    "ALO.PA": "Alstom",
    "MT.PA": "ArcelorMittal",
    "CS.PA": "AXA",
    "BNP.PA": "BNP Paribas",
    "EN.PA": "Bouygues",
    "CAP.PA": "Capgemini",
    "CA.PA": "Carrefour",
    "ACA.PA": "Crédit Agricole",
    "BN.PA": "Danone",
    "DSY.PA": "Dassault Systèmes",
    "ENGI.PA": "Engie",
    "EL.PA": "EssilorLuxottica",
    "ERF.PA": "Eurofins Scientific",
    "RMS.PA": "Hermès",
    "KER.PA": "Kering",
    "LR.PA": "Legrand",
    "OR.PA": "L'Oréal",
    "MC.PA": "LVMH",
    "ML.PA": "Michelin",
    "ORA.PA": "Orange",
    "RI.PA": "Pernod Ricard",
    "PUB.PA": "Publicis",
    "RNO.PA": "Renault",
    "SAF.PA": "Safran",
    "SGO.PA": "Saint-Gobain",
    "SAN.PA": "Sanofi",
    "SU.PA": "Schneider Electric",
    "GLE.PA": "Société Générale",
    "STLAP.PA": "Stellantis",
    "STMPA.PA": "STMicroelectronics",
    "TEP.PA": "Teleperformance",
    "HO.PA": "Thales",
    "TTE.PA": "TotalEnergies",
    "URW.PA": "Unibail-Rodamco-Westfield",
    "VIE.PA": "Veolia",
    "DG.PA": "Vinci",
    "VIV.PA": "Vivendi",
    "WLN.PA": "Worldline",
    # Tickers de la spec originale (alias)
    "FP.PA": "TotalEnergies",
    "STLAM.PA": "Stellantis",
}


def get_ticker_name(ticker: str) -> str:
    """Retourne le nom complet d'une action depuis son ticker."""
    return CAC40_NAMES.get(ticker, ticker)


def get_ticker_price(ticker: str) -> Optional[dict]:
    """Récupère le prix actuel et la variation d'un ticker.

    Retourne un dict avec : prix_actuel, variation, variation_pct, ouverture, volume
    """
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period="2d")

        if hist.empty:
            logger.warning("Pas de données pour %s", ticker)
            return None

        prix_actuel = float(hist["Close"].iloc[-1])

        # Variation par rapport à la veille si disponible, sinon par rapport à l'ouverture
        if len(hist) >= 2:
            prix_veille = float(hist["Close"].iloc[-2])
        else:
            prix_veille = float(hist["Open"].iloc[-1])

        variation = prix_actuel - prix_veille
        variation_pct = (variation / prix_veille) * 100 if prix_veille != 0 else 0

        return {
            "ticker": ticker,
            "nom": get_ticker_name(ticker),
            "prix_actuel": round(prix_actuel, 2),
            "variation": round(variation, 2),
            "variation_pct": round(variation_pct, 2),
            "ouverture": round(float(hist["Open"].iloc[-1]), 2),
            "volume": int(hist["Volume"].iloc[-1]),
        }
    except Exception as e:
        logger.error("Erreur Yahoo Finance pour %s : %s", ticker, e)
        return None


def get_ticker_history(ticker: str, period: str = "5d") -> Optional[list]:
    """Récupère l'historique des prix d'un ticker."""
    try:
        t = yf.Ticker(ticker)
        hist = t.history(period=period)

        if hist.empty:
            return None

        results = []
        for date, row in hist.iterrows():
            results.append({
                "date": date.strftime("%Y-%m-%d"),
                "ouverture": round(float(row["Open"]), 2),
                "cloture": round(float(row["Close"]), 2),
                "haut": round(float(row["High"]), 2),
                "bas": round(float(row["Low"]), 2),
                "volume": int(row["Volume"]),
            })
        return results
    except Exception as e:
        logger.error("Erreur historique pour %s : %s", ticker, e)
        return None


def get_cac40_movers() -> dict:
    """Récupère les top hausses et baisses du CAC40.

    Retourne un dict avec : top_gainers, top_losers, performance_globale
    """
    results = []

    for ticker in CAC40_TICKERS:
        data = get_ticker_price(ticker)
        if data:
            results.append(data)
        time.sleep(0.5)  # Rate limiting : ~2 req/sec

    if not results:
        logger.error("Aucune donnée CAC40 récupérée")
        return {"top_gainers": [], "top_losers": [], "performance_globale": 0}

    # Tri par variation %
    results.sort(key=lambda x: x["variation_pct"], reverse=True)

    # Performance globale (moyenne des variations)
    perf_globale = sum(r["variation_pct"] for r in results) / len(results)

    return {
        "top_gainers": results[:5],
        "top_losers": results[-5:][::-1],  # Inversé pour avoir le pire en premier
        "performance_globale": round(perf_globale, 2),
        "tous": results,
    }


def get_ticker_info(ticker: str) -> Optional[dict]:
    """Récupère les infos détaillées d'un ticker (nom, secteur, etc.)."""
    try:
        t = yf.Ticker(ticker)
        info = t.info
        return {
            "nom": info.get("shortName", ticker),
            "secteur": info.get("sector", "N/A"),
            "industrie": info.get("industry", "N/A"),
            "devise": info.get("currency", "EUR"),
        }
    except Exception as e:
        logger.error("Erreur info ticker %s : %s", ticker, e)
        return None
