"""Tests unitaires pour le module portfolio."""

import unittest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from datetime import datetime

from alita.modules.portfolio import ajouter_action, retirer_action, lister_portfolio


class TestPortfolio(unittest.TestCase):
    """Tests du module portfolio."""

    @patch("alita.modules.portfolio.get_session")
    def test_ajouter_action_succes(self, mock_session):
        """Test ajout d'une action avec succès."""
        session = MagicMock()
        session.query.return_value.filter_by.return_value.first.return_value = None
        mock_session.return_value.__enter__ = lambda s: session
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        result = ajouter_action("AIR.PA", "Airbus", 145.20, 10)

        self.assertTrue(result["ok"])
        self.assertIn("AIR.PA", result["message"])

    @patch("alita.modules.portfolio.get_session")
    def test_ajouter_action_doublon(self, mock_session):
        """Test ajout d'une action déjà existante."""
        existant = MagicMock()
        existant.quantite = 10
        session = MagicMock()
        session.query.return_value.filter_by.return_value.first.return_value = existant
        mock_session.return_value.__enter__ = lambda s: session
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        result = ajouter_action("AIR.PA", "Airbus", 145.20, 10)

        self.assertFalse(result["ok"])
        self.assertIn("déjà", result["message"])

    @patch("alita.modules.portfolio.get_session")
    def test_retirer_action_inexistante(self, mock_session):
        """Test retrait d'une action non présente."""
        session = MagicMock()
        session.query.return_value.filter_by.return_value.first.return_value = None
        mock_session.return_value.__enter__ = lambda s: session
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        result = retirer_action("FAKE.PA")

        self.assertFalse(result["ok"])
        self.assertIn("non trouvé", result["message"])

    @patch("alita.modules.portfolio.get_session")
    def test_retirer_action_succes(self, mock_session):
        """Test retrait d'une action existante."""
        action = MagicMock()
        action.id = 1
        action.nom = "Airbus"
        action.ticker = "AIR.PA"
        action.prix_achat = Decimal("145.20")
        action.quantite = 10
        session = MagicMock()
        session.query.return_value.filter_by.return_value.first.return_value = action
        mock_session.return_value.__enter__ = lambda s: session
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        result = retirer_action("AIR.PA")

        self.assertTrue(result["ok"])
        self.assertFalse(action.actif)


class TestMotoScore(unittest.TestCase):
    """Tests du calcul de score moto."""

    def test_conditions_parfaites(self):
        from alita.modules.moto_score import calculer_score_moto

        meteo = {
            "temperature": 22,
            "vent_vitesse": 10,
            "pluie_1h": 0,
            "nuages": 20,
        }
        result = calculer_score_moto(meteo)
        self.assertEqual(result["score"], 10)

    def test_pluie(self):
        from alita.modules.moto_score import calculer_score_moto

        meteo = {
            "temperature": 20,
            "vent_vitesse": 10,
            "pluie_1h": 2,
            "nuages": 80,
        }
        result = calculer_score_moto(meteo)
        self.assertLessEqual(result["score"], 6)

    def test_meteo_none(self):
        from alita.modules.moto_score import calculer_score_moto

        result = calculer_score_moto(None)
        self.assertEqual(result["score"], 0)

    def test_froid_extreme(self):
        from alita.modules.moto_score import calculer_score_moto

        meteo = {
            "temperature": -5,
            "vent_vitesse": 30,
            "pluie_1h": 3,
            "nuages": 100,
        }
        result = calculer_score_moto(meteo)
        self.assertEqual(result["score"], 0)


if __name__ == "__main__":
    unittest.main()
