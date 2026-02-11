"""Logique métier du portfolio."""

from datetime import datetime
from typing import Optional
from decimal import Decimal

from alita.database.db import get_session
from alita.database.models import Portfolio, Transaction
from alita.modules import yahoo_finance
from alita.utils.logger import logger
from alita.utils.helpers import now_paris


def ajouter_action(ticker: str, nom: str, prix_achat: float, quantite: int) -> dict:
    """Ajoute une action au portfolio.

    Retourne un dict avec : ok, message, portfolio_id
    """
    try:
        with get_session() as session:
            # Vérifier si le ticker existe déjà en actif
            existant = session.query(Portfolio).filter_by(
                ticker=ticker.upper(), actif=True
            ).first()

            if existant:
                return {
                    "ok": False,
                    "message": f"{ticker.upper()} est déjà dans le portfolio (x{existant.quantite})",
                }

            # Créer l'entrée portfolio
            nouvelle = Portfolio(
                ticker=ticker.upper(),
                nom=nom,
                prix_achat=Decimal(str(prix_achat)),
                quantite=quantite,
                date_achat=now_paris(),
                actif=True,
            )
            session.add(nouvelle)
            session.flush()  # Pour obtenir l'ID

            # Enregistrer la transaction
            transaction = Transaction(
                portfolio_id=nouvelle.id,
                type_transaction="ACHAT",
                ticker=ticker.upper(),
                prix=Decimal(str(prix_achat)),
                quantite=quantite,
                date_transaction=now_paris(),
                note=f"Achat initial de {nom}",
            )
            session.add(transaction)

            logger.info("Action ajoutée : %s x%d @ %.2f€", ticker.upper(), quantite, prix_achat)
            return {
                "ok": True,
                "message": f"✅ {nom} ({ticker.upper()}) ajouté : {quantite} actions à {prix_achat}€",
                "portfolio_id": nouvelle.id,
            }

    except Exception as e:
        logger.error("Erreur ajout portfolio : %s", e)
        return {"ok": False, "message": f"❌ Erreur : {e}"}


def retirer_action(ticker: str) -> dict:
    """Archive une action (soft delete)."""
    try:
        with get_session() as session:
            action = session.query(Portfolio).filter_by(
                ticker=ticker.upper(), actif=True
            ).first()

            if not action:
                return {"ok": False, "message": f"❌ {ticker.upper()} non trouvé dans le portfolio actif"}

            action.actif = False

            # Enregistrer la transaction
            transaction = Transaction(
                portfolio_id=action.id,
                type_transaction="VENTE",
                ticker=ticker.upper(),
                prix=action.prix_achat,
                quantite=action.quantite,
                date_transaction=now_paris(),
                note=f"Retrait de {action.nom}",
            )
            session.add(transaction)

            logger.info("Action retirée : %s", ticker.upper())
            return {"ok": True, "message": f"✅ {action.nom} ({ticker.upper()}) retiré du portfolio"}

    except Exception as e:
        logger.error("Erreur retrait portfolio : %s", e)
        return {"ok": False, "message": f"❌ Erreur : {e}"}


def lister_portfolio() -> dict:
    """Liste le portfolio actif avec performances en temps réel.

    Retourne un dict avec : actions (liste), total_investi, total_actuel, gain_total, gain_pct
    """
    try:
        with get_session() as session:
            actions = session.query(Portfolio).filter_by(actif=True).all()

            if not actions:
                return {
                    "ok": True,
                    "actions": [],
                    "total_investi": 0,
                    "total_actuel": 0,
                    "gain_total": 0,
                    "gain_pct": 0,
                    "message": "Portfolio vide",
                }

            resultats = []
            total_investi = 0
            total_actuel = 0

            for action in actions:
                prix_data = yahoo_finance.get_ticker_price(action.ticker)
                prix_actuel = prix_data["prix_actuel"] if prix_data else float(action.prix_achat)
                variation_jour = prix_data["variation_pct"] if prix_data else 0

                investi = float(action.prix_achat) * action.quantite
                actuel = prix_actuel * action.quantite
                gain = actuel - investi
                gain_pct = (gain / investi) * 100 if investi != 0 else 0

                total_investi += investi
                total_actuel += actuel

                resultats.append({
                    "ticker": action.ticker,
                    "nom": action.nom,
                    "quantite": action.quantite,
                    "prix_achat": float(action.prix_achat),
                    "prix_actuel": prix_actuel,
                    "variation_jour": round(variation_jour, 2),
                    "gain": round(gain, 2),
                    "gain_pct": round(gain_pct, 2),
                    "investi": round(investi, 2),
                    "valeur_actuelle": round(actuel, 2),
                    "date_achat": action.date_achat.strftime("%d/%m/%Y"),
                })

            gain_total = total_actuel - total_investi
            gain_total_pct = (gain_total / total_investi) * 100 if total_investi != 0 else 0

            return {
                "ok": True,
                "actions": resultats,
                "total_investi": round(total_investi, 2),
                "total_actuel": round(total_actuel, 2),
                "gain_total": round(gain_total, 2),
                "gain_pct": round(gain_total_pct, 2),
            }

    except Exception as e:
        logger.error("Erreur liste portfolio : %s", e)
        return {"ok": False, "actions": [], "message": f"❌ Erreur : {e}"}


def historique_transactions(ticker: str) -> list:
    """Récupère l'historique des transactions pour un ticker."""
    try:
        with get_session() as session:
            transactions = (
                session.query(Transaction)
                .filter_by(ticker=ticker.upper())
                .order_by(Transaction.date_transaction.desc())
                .limit(20)
                .all()
            )

            return [
                {
                    "type": t.type_transaction,
                    "prix": float(t.prix) if t.prix else None,
                    "quantite": t.quantite,
                    "date": t.date_transaction.strftime("%d/%m/%Y %H:%M"),
                    "note": t.note or "",
                }
                for t in transactions
            ]

    except Exception as e:
        logger.error("Erreur historique %s : %s", ticker, e)
        return []


def get_portfolio_pour_briefing() -> dict:
    """Récupère les données portfolio formatées pour le briefing.

    Retourne les données enrichies avec les top performers du jour.
    """
    portfolio = lister_portfolio()

    if not portfolio.get("actions"):
        return portfolio

    # Trier par variation du jour pour trouver les top performers
    actions_triees = sorted(
        portfolio["actions"],
        key=lambda x: x["variation_jour"],
        reverse=True,
    )

    portfolio["top_performers"] = actions_triees[:3]
    portfolio["worst_performers"] = actions_triees[-3:][::-1]

    return portfolio
