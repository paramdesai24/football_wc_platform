from __future__ import annotations

from logging.config import fileConfig
import asyncio
import os
import ssl
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from dotenv import load_dotenv

from app.core.config import settings
from app.core.database import postgres_engine
from app.models.auction_models import AuctionBase

config = context.config
load_dotenv(Path(__file__).resolve().parents[1] / ".env", override=False)
supabase_url = os.getenv("SUPABASE_POSTGRES_URL", "").strip()


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


sqlalchemy_url = _to_asyncpg_url(supabase_url) if supabase_url else settings.DATABASE_URL
config.set_main_option("sqlalchemy.url", sqlalchemy_url.replace("%", "%%"))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = AuctionBase.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    def do_run_migrations(connection):
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()

    async def run_async_migrations() -> None:
        connectable: AsyncEngine
        if postgres_engine is not None:
            connectable = postgres_engine
        else:
            connectable = create_async_engine(
                config.get_main_option("sqlalchemy.url"),
                connect_args={"ssl": _create_ssl_context()},
                poolclass=pool.NullPool,
            )

        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

        if postgres_engine is None:
            await connectable.dispose()

    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
