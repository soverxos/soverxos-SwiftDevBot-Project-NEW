"""
Database Engine Configuration
------------------------------
SQLAlchemy engine и session management для SwiftDevBot
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from contextlib import asynccontextmanager
import os
from typing import AsyncGenerator

from Systems.core.config.settings import DATABASE_URL, DB_ENGINE


class Base(DeclarativeBase):
    """Базовый класс для всех ORM моделей"""
    pass


# Синхронный engine (для миграций Alembic)
sync_engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True,
)

# Асинхронный engine (для production использования)
if DB_ENGINE == "sqlite":
    # SQLite требует специального URL для async
    async_database_url = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
else:
    # PostgreSQL/MySQL
    async_database_url = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
    async_database_url = async_database_url.replace("mysql://", "mysql+aiomysql://")

async_engine = create_async_engine(
    async_database_url,
    echo=os.getenv("SQL_ECHO", "false").lower() == "true",
    pool_pre_ping=True,
)

# Session makers
SyncSessionLocal = sessionmaker(bind=sync_engine, autocommit=False, autoflush=False)
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


def get_sync_session():
    """Получить синхронную сессию (для скриптов/миграций)"""
    session = SyncSessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@asynccontextmanager
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Получить асинхронную сессию (для сервисов)"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database():
    """Инициализировать базу данных (создать таблицы)"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_database():
    """Удалить все таблицы (ОСТОРОЖНО!)"""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

