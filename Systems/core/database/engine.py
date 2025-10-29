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
import warnings
from typing import AsyncGenerator

from Systems.core.config.settings import DATABASE_URL, ASYNC_DATABASE_URL, DB_ENGINE

# Подавляем исключения aiomysql о закрытии event loop
import sys
_original_stderr = sys.stderr

# Monkey patch для aiomysql Connection.__del__ чтобы не показывать исключения
def _patch_aiomysql():
    try:
        import aiomysql
        original_del = aiomysql.Connection.__del__

        def patched_del(self):
            try:
                return original_del(self)
            except RuntimeError as e:
                if "Event loop is closed" in str(e):
                    # Игнорируем это исключение
                    pass
                else:
                    raise

        aiomysql.Connection.__del__ = patched_del
        if not hasattr(sys, '_aiomysql_patched'):
            sys._aiomysql_patched = True
            print("✅ Aiomysql cleanup патч применен", file=_original_stderr)
    except ImportError:
        pass

_patch_aiomysql()


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
async_database_url = ASYNC_DATABASE_URL

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

