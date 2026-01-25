from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine  # pyright: ignore[reportMissingImports]
from sqlalchemy.orm import declarative_base  # pyright: ignore[reportMissingImports]
from sqlalchemy.pool import NullPool  # pyright: ignore[reportMissingImports]

from .config import settings


def ensure_async_database_url(database_url: str) -> str:
    """将 PostgreSQL 同步驱动 URL 规范化为 asyncpg URL，避免 AsyncEngine 初始化失败。"""
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url
    if database_url.startswith("postgresql+psycopg2://"):
        return "postgresql+asyncpg://" + database_url.removeprefix("postgresql+psycopg2://")
    if database_url.startswith("postgresql+psycopg://"):
        return "postgresql+asyncpg://" + database_url.removeprefix("postgresql+psycopg://")
    if database_url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + database_url.removeprefix("postgresql://")
    return database_url


if settings.app_env == "test":
    engine = create_async_engine(
        ensure_async_database_url(settings.database_url),
        echo=False,
        future=True,
        poolclass=NullPool,
    )
else:
    engine = create_async_engine(ensure_async_database_url(settings.database_url), echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()


async def get_session() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

