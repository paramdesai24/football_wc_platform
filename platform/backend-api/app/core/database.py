from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings
from pathlib import Path

# Lazy-loaded engine to avoid module-level blocking
_engine = None
_SessionLocal = None


def _get_engine():
    """Get or create the database engine (lazy loaded)."""
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.DATABASE_URL,
            connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
            echo=settings.DEBUG,
        )
    return _engine


def _get_session_local():
    """Get or create the SessionLocal factory (lazy loaded)."""
    global _SessionLocal
    if _SessionLocal is None:
        engine = _get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


class Base(DeclarativeBase):
    pass


def get_db():
    SessionLocal = _get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    if settings.DATABASE_URL.startswith("sqlite:///"):
        db_path = Path(settings.DATABASE_URL.replace("sqlite:///", "", 1))
        db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = _get_engine()
    Base.metadata.create_all(bind=engine)
