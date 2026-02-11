"""Connexion et gestion de la base de données."""

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from alita.config import Config
from alita.utils.logger import logger

# Engine global (initialisé au premier appel)
_engine = None
_SessionLocal = None


def get_engine():
    """Crée ou retourne l'engine SQLAlchemy."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            Config.get_db_url(),
            pool_size=5,
            max_overflow=10,
            pool_recycle=3600,
            echo=False,
        )
        logger.info("Connexion DB établie : %s:%s/%s", Config.DB_HOST, Config.DB_PORT, Config.DB_NAME)
    return _engine


def get_session_factory():
    """Retourne la factory de sessions."""
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal


@contextmanager
def get_session():
    """Context manager pour obtenir une session DB avec commit/rollback auto."""
    factory = get_session_factory()
    session: Session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def test_connection() -> bool:
    """Teste la connexion à la base de données."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            from sqlalchemy import text
            conn.execute(text("SELECT 1"))
        logger.info("Connexion DB OK")
        return True
    except Exception as e:
        logger.error("Erreur connexion DB : %s", e)
        return False
