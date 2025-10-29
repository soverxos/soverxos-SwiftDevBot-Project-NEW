import os

SDB_ENV = os.getenv("SDB_ENV", "dev")

DB_ENGINE = os.getenv("DB_ENGINE", "sqlite")
if DB_ENGINE == "sqlite":
    SQLITE_PATH = os.getenv("SQLITE_PATH", "Data/database/sdb.sqlite3")
    DATABASE_URL = f"sqlite:///{SQLITE_PATH}"
elif DB_ENGINE == "postgres":
    DATABASE_URL = os.getenv("POSTGRES_DSN")
elif DB_ENGINE == "mysql":
    DATABASE_URL = os.getenv("MYSQL_DSN")
else:
    raise ValueError(f"Unsupported DB_ENGINE: {DB_ENGINE}")

EVENTBUS_MODE = os.getenv("EVENTBUS_MODE", "redis")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
EVENTBUS_MEMORY_MAX = int(os.getenv("EVENTBUS_MEMORY_MAX", "1000"))

SDB_SUPERADMIN_ID = int(os.getenv("SDB_SUPERADMIN_ID", "0"))
SDB_ADMIN_IDS = [int(x) for x in os.getenv("SDB_ADMIN_IDS", "").split(",") if x.strip()]

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = os.getenv("LOG_FORMAT", "text")
