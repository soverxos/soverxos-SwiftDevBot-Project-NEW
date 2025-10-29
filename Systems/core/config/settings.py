"""
SwiftDevBot Configuration Settings
----------------------------------
Централизованная конфигурация системы с валидацией и безопасным парсингом
"""

import os
from typing import List, Optional
from pathlib import Path

# Загружаем переменные окружения из .env файла
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv не установлен, работаем без него
    pass


# Валидация и безопасный парсинг
def _parse_int(value: str, default: int, min_val: Optional[int] = None, max_val: Optional[int] = None) -> int:
    """Безопасный парсинг целого числа с валидацией диапазона"""
    try:
        result = int(value)
        if min_val is not None and result < min_val:
            raise ValueError(f"Value {result} is less than minimum {min_val}")
        if max_val is not None and result > max_val:
            raise ValueError(f"Value {result} is greater than maximum {max_val}")
        return result
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid integer value '{value}': {e}")


def _parse_list_of_ints(value: str, default: List[int] = None) -> List[int]:
    """Безопасный парсинг списка целых чисел"""
    if default is None:
        default = []

    if not value.strip():
        return default

    try:
        return [int(x.strip()) for x in value.split(",") if x.strip()]
    except (ValueError, TypeError) as e:
        raise ValueError(f"Invalid integer list value '{value}': {e}")


def _validate_choice(value: str, choices: List[str], default: str) -> str:
    """Валидация выбора из списка"""
    if value not in choices:
        raise ValueError(f"Invalid choice '{value}'. Must be one of: {choices}")
    return value


# Основные настройки окружения
SDB_ENV = _validate_choice(
    os.getenv("SDB_ENV", "dev"),
    ["dev", "staging", "prod"],
    "dev"
)

# Настройки базы данных
DB_ENGINE = _validate_choice(
    os.getenv("DB_ENGINE", "sqlite"),
    ["sqlite", "postgres", "mysql"],
    "sqlite"
)

# Определяем исходные DSN для всех БД
POSTGRES_DSN = os.getenv("POSTGRES_DSN")
MYSQL_DSN = os.getenv("MYSQL_DSN")
SQLITE_PATH = os.getenv("SQLITE_PATH", "Data/database/sdb.sqlite3")

if DB_ENGINE == "sqlite":
    # Проверяем, что путь безопасный
    sqlite_path = Path(SQLITE_PATH)
    if sqlite_path.is_absolute() and not str(sqlite_path).startswith("/tmp/"):
        raise ValueError("SQLite path must be relative or in /tmp/ for security")
    DATABASE_URL = f"sqlite:///{SQLITE_PATH}"
elif DB_ENGINE == "postgres":
    DATABASE_URL = POSTGRES_DSN
    if not DATABASE_URL:
        raise ValueError("POSTGRES_DSN is required when DB_ENGINE=postgres")
elif DB_ENGINE == "mysql":
    DATABASE_URL = MYSQL_DSN
    if not DATABASE_URL:
        raise ValueError("MYSQL_DSN is required when DB_ENGINE=mysql")

# Создаем async версию URL для использования в async движке
if DB_ENGINE == "sqlite":
    ASYNC_DATABASE_URL = DATABASE_URL.replace("sqlite:///", "sqlite+aiosqlite:///")
elif DB_ENGINE == "postgres":
    # Убираем sync драйвер и добавляем async
    ASYNC_DATABASE_URL = DATABASE_URL.replace("+psycopg2", "").replace("postgresql://", "postgresql+asyncpg://")
elif DB_ENGINE == "mysql":
    # Убираем sync драйвер и добавляем async
    ASYNC_DATABASE_URL = DATABASE_URL.replace("+pymysql", "").replace("mysql://", "mysql+aiomysql://")
else:
    ASYNC_DATABASE_URL = DATABASE_URL

# Настройки EventBus
EVENTBUS_MODE = _validate_choice(
    os.getenv("EVENTBUS_MODE", "memory" if SDB_ENV == "dev" else "redis"),
    ["memory", "redis"],
    "memory" if SDB_ENV == "dev" else "redis"
)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
EVENTBUS_MEMORY_MAX = _parse_int(
    os.getenv("EVENTBUS_MEMORY_MAX", "1000"),
    1000, 10, 100000  # min 10, max 100k
)

# Настройки администраторов
SDB_SUPERADMIN_ID = _parse_int(
    os.getenv("SDB_SUPERADMIN_ID", "0"),
    0, 0, 999999999999  # Telegram ID limits
)

SDB_ADMIN_IDS = _parse_list_of_ints(
    os.getenv("SDB_ADMIN_IDS", ""),
    []
)

# Проверяем, что superadmin не дублируется в admin_ids
if SDB_SUPERADMIN_ID > 0 and SDB_SUPERADMIN_ID in SDB_ADMIN_IDS:
    raise ValueError("SDB_SUPERADMIN_ID should not be in SDB_ADMIN_IDS")

# Настройки логирования
LOG_LEVEL = _validate_choice(
    os.getenv("LOG_LEVEL", "INFO"),
    ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
    "INFO"
)

LOG_FORMAT = _validate_choice(
    os.getenv("LOG_FORMAT", "json" if SDB_ENV == "prod" else "text"),
    ["text", "json"],
    "json" if SDB_ENV == "prod" else "text"
)

# Дополнительные настройки безопасности
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-in-prod")
if SDB_ENV != "dev" and SECRET_KEY == "dev-secret-change-in-prod":
    raise ValueError("SECRET_KEY must be set in production")

# Настройки производительности
MAX_WORKERS = _parse_int(
    os.getenv("MAX_WORKERS", "4"),
    4, 1, 100
)

REQUEST_TIMEOUT = _parse_int(
    os.getenv("REQUEST_TIMEOUT", "30"),
    30, 5, 300
)

# Настройки Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN and SDB_ENV != "dev":
    raise ValueError("BOT_TOKEN is required in production")

# Webhook настройки (опционально)
WEBHOOK_URL = os.getenv("WEBHOOK_URL")
WEBHOOK_PATH = os.getenv("WEBHOOK_PATH", "/webhook")

# Настройки регистрации пользователей
REQUIRE_REGISTRATION = os.getenv("REQUIRE_REGISTRATION", "true").lower() == "true"
START_MESSAGE_NEW_USER = os.getenv("START_MESSAGE_NEW_USER",
    "🎉 Добро пожаловать в SwiftDevBot!\n\nВы успешно зарегистрированы.\n\nДоступные команды:\n/admin - админ-панель\n/ping - проверка бота\n/help - справка")
START_MESSAGE_EXISTING_USER = os.getenv("START_MESSAGE_EXISTING_USER",
    "✅ Вы уже зарегистрированы!\n\nДоступные команды:\n/admin - админ-панель\n/ping - проверка бота\n/help - справка")

# Экспорт всех настроек для использования
__all__ = [
    "SDB_ENV", "DB_ENGINE", "DATABASE_URL", "ASYNC_DATABASE_URL", "EVENTBUS_MODE", "REDIS_URL",
    "EVENTBUS_MEMORY_MAX", "SDB_SUPERADMIN_ID", "SDB_ADMIN_IDS",
    "LOG_LEVEL", "LOG_FORMAT", "SECRET_KEY", "MAX_WORKERS", "REQUEST_TIMEOUT",
    "BOT_TOKEN", "WEBHOOK_URL", "WEBHOOK_PATH", "POSTGRES_DSN", "MYSQL_DSN", "SQLITE_PATH",
    "REQUIRE_REGISTRATION", "START_MESSAGE_NEW_USER", "START_MESSAGE_EXISTING_USER"
]
