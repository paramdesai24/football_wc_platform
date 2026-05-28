import os
import ssl
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from dotenv import load_dotenv

from app.core.config import settings

load_dotenv(Path(__file__).resolve().parents[2] / ".env", override=False)


def _to_asyncpg_url(url: str) -> str:
    if not url:
        return url

    parts = urlsplit(url)
    scheme = parts.scheme
    if scheme == "postgresql+psycopg2":
        scheme = "postgresql+asyncpg"
    elif scheme == "postgresql":
        scheme = "postgresql+asyncpg"

    query = urlencode([(key, value) for key, value in parse_qsl(parts.query) if key.lower() != "sslmode"])
    return urlunsplit((scheme, parts.netloc, parts.path, query, parts.fragment))


def _create_ssl_context() -> ssl.SSLContext:
    context = ssl.create_default_context()
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    return context

# Lazy-loaded engine to avoid module-level blocking
_engine = None
_SessionLocal = None

# New Supabase PostgreSQL engine for the auction/FPL system
SUPABASE_URL = os.getenv("SUPABASE_POSTGRES_URL", "")
postgres_engine = None
PostgresSessionLocal = None

if SUPABASE_URL:
    postgres_engine = create_async_engine(
        _to_asyncpg_url(SUPABASE_URL),
        connect_args={"ssl": _create_ssl_context()},
        pool_size=10,
        max_overflow=20,
        echo=False,
    )
    PostgresSessionLocal = sessionmaker(
        postgres_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


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


async def get_postgres_db():
    if PostgresSessionLocal is None:
        raise RuntimeError("SUPABASE_POSTGRES_URL is not configured")

    async with PostgresSessionLocal() as session:
        yield session
