"""Modèles SQLAlchemy pour la base de données Alita."""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, DateTime, Text, JSON,
    Enum, ForeignKey, Index, create_engine,
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class Portfolio(Base):
    """Table des actions en portfolio."""
    __tablename__ = "portfolio"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(20), nullable=False, index=True)
    nom = Column(String(100), nullable=False)
    prix_achat = Column(Numeric(10, 2), nullable=False)
    quantite = Column(Integer, nullable=False)
    date_achat = Column(DateTime, nullable=False)
    actif = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    transactions = relationship("Transaction", back_populates="portfolio_rel")

    def __repr__(self):
        return f"<Portfolio {self.ticker} x{self.quantite}>"


class Transaction(Base):
    """Table historique des transactions."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    portfolio_id = Column(Integer, ForeignKey("portfolio.id", ondelete="SET NULL"))
    type_transaction = Column(
        Enum("ACHAT", "VENTE", "MODIFICATION", name="type_transaction_enum"),
        nullable=False,
    )
    ticker = Column(String(20), nullable=False)
    prix = Column(Numeric(10, 2))
    quantite = Column(Integer)
    date_transaction = Column(DateTime, nullable=False, index=True)
    note = Column(Text)

    portfolio_rel = relationship("Portfolio", back_populates="transactions")

    def __repr__(self):
        return f"<Transaction {self.type_transaction} {self.ticker}>"


class ConfigDB(Base):
    """Table de configuration clé/valeur."""
    __tablename__ = "config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cle = Column(String(50), unique=True, nullable=False)
    valeur = Column(Text, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Config {self.cle}={self.valeur}>"


class ApiCache(Base):
    """Cache des appels API pour limiter les requêtes."""
    __tablename__ = "api_cache"

    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(255), unique=True, nullable=False)
    data = Column(JSON, nullable=False)
    expires_at = Column(DateTime, nullable=False, index=True)


class BriefingLog(Base):
    """Logs des briefings envoyés."""
    __tablename__ = "briefings_log"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date_envoi = Column(DateTime, nullable=False, index=True)
    contenu = Column(Text)
    statut = Column(
        Enum("SUCCESS", "ERREUR", name="statut_enum"),
        nullable=False,
    )
    message_erreur = Column(Text)
