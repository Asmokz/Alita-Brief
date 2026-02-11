"""Tests pour le module Yahoo Finance."""

import unittest
from unittest.mock import patch, MagicMock
import pandas as pd
from datetime import datetime

from alita.modules.yahoo_finance import get_ticker_price, get_ticker_history, CAC40_TICKERS


class TestYahooFinance(unittest.TestCase):
    """Tests du module Yahoo Finance."""

    @patch("alita.modules.yahoo_finance.yf.Ticker")
    def test_get_ticker_price_succes(self, mock_ticker_class):
        """Test récupération prix avec données valides."""
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker

        # Simuler des données historiques sur 2 jours
        dates = pd.date_range("2024-01-01", periods=2, freq="D")
        mock_ticker.history.return_value = pd.DataFrame({
            "Open": [140.0, 142.0],
            "Close": [142.0, 145.0],
            "High": [143.0, 146.0],
            "Low": [139.0, 141.0],
            "Volume": [1000000, 1200000],
        }, index=dates)

        result = get_ticker_price("AIR.PA")

        self.assertIsNotNone(result)
        self.assertEqual(result["ticker"], "AIR.PA")
        self.assertEqual(result["prix_actuel"], 145.0)
        self.assertAlmostEqual(result["variation"], 3.0)
        self.assertGreater(result["variation_pct"], 0)

    @patch("alita.modules.yahoo_finance.yf.Ticker")
    def test_get_ticker_price_vide(self, mock_ticker_class):
        """Test avec un ticker qui ne retourne pas de données."""
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker
        mock_ticker.history.return_value = pd.DataFrame()

        result = get_ticker_price("FAKE.XX")

        self.assertIsNone(result)

    @patch("alita.modules.yahoo_finance.yf.Ticker")
    def test_get_ticker_history(self, mock_ticker_class):
        """Test récupération historique."""
        mock_ticker = MagicMock()
        mock_ticker_class.return_value = mock_ticker

        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        mock_ticker.history.return_value = pd.DataFrame({
            "Open": [140, 141, 142, 143, 144],
            "Close": [141, 142, 143, 144, 145],
            "High": [142, 143, 144, 145, 146],
            "Low": [139, 140, 141, 142, 143],
            "Volume": [1e6, 1.1e6, 1.2e6, 1.3e6, 1.4e6],
        }, index=dates)

        result = get_ticker_history("AIR.PA", "5d")

        self.assertIsNotNone(result)
        self.assertEqual(len(result), 5)
        self.assertIn("date", result[0])
        self.assertIn("cloture", result[0])

    def test_cac40_tickers_non_vide(self):
        """Vérifie que la liste CAC40 est définie."""
        self.assertGreater(len(CAC40_TICKERS), 30)
        self.assertTrue(all(t.endswith(".PA") for t in CAC40_TICKERS))


class TestWeather(unittest.TestCase):
    """Tests du module météo."""

    @patch("alita.modules.weather.requests.get")
    def test_get_weather_succes(self, mock_get):
        """Test récupération météo avec réponse valide."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "weather": [{"description": "ciel dégagé", "icon": "01d"}],
            "main": {"temp": 22.5, "feels_like": 21.0, "humidity": 45},
            "wind": {"speed": 3.5, "gust": 5.0},
            "rain": {},
            "clouds": {"all": 10},
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        from alita.modules.weather import get_weather
        result = get_weather("Marseille")

        self.assertIsNotNone(result)
        self.assertEqual(result["ville"], "Marseille")
        self.assertEqual(result["temperature"], 22.5)
        self.assertIn("dégagé", result["description"])


if __name__ == "__main__":
    unittest.main()
