# Alembic Database Migrations

## SwiftDevBot Database Migrations

This directory contains database migration scripts for SwiftDevBot.

## Usage

### Generate a new migration

```bash
cd /path/to/swiftdevbot
alembic revision --autogenerate -m "Add new table"
```

### Run migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade to specific revision
alembic upgrade <revision_id>

# Downgrade
alembic downgrade -1
```

### Check current status

```bash
alembic current
alembic history
```

## Configuration

- **Database URL**: Configured via `.env` file (DATABASE_URL)
- **Models**: Located in `Systems/core/database/models.py`
- **Engine**: Uses async SQLAlchemy engine

## Supported Databases

- SQLite (default for development)
- PostgreSQL (production recommended)
- MySQL/MariaDB (alternative)

## Migration Files

Migration files are stored in the `versions/` directory and are automatically generated based on changes to the SQLAlchemy models.

