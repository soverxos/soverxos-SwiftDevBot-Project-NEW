Ты работаешь в проекте SwiftDevBot — это микросервисная SaaS-платформа для Telegram-ботов, написанная на Python 3.12+.

⚙️ Архитектура проекта:
- ядро платформы находится в Systems/
- системные модули (всегда активны): Systems/SysModules/
- пользовательские модули — в Modules/ (каждый модуль имеет папку web/, backend/, module.json)
- сервисы запускаются из Systems/services/
- WebPanel — на FastAPI (порт 8000)
- бот — на Aiogram 3.22
- конфигурация — через .env (SQLite или PostgreSQL, Redis или Memory)

📦 Инфраструктура:
- есть run_dev.sh (для локальной разработки)
- есть run_prod.sh и deploy/ (для продакшена)
- поддержка systemd, Nginx, logrotate, backup
- по умолчанию используется SQLite + EventBus(memory)

👑 Основные цели разработки:
1. Расширять ядро SwiftDevBot новыми системными модулями (Auth, RBAC, WebPanel, License и т.д.)
2. Создавать пользовательские модули в папке Modules/ с web-интерфейсом и Telegram-командами.
3. Добавлять команды в sdb.py (CLI-утилиту управления платформой).
4. Оптимизировать и масштабировать систему, не ломая совместимость структуры.
5. Сохранять строгую архитектуру — **никаких изменений в утверждённой структуре проекта.**

🧩 Формат пользовательского модуля:
Modules/<ModuleName>/
 ├── backend/              # обработчики и API
 ├── web/                  # UI-часть, шаблоны, js/css
 ├── __init__.py
 ├── module.json           # метаданные (id, версия, автор, webpath, команды)
 └── readme.md

📜 Важные пути из .env:
DATA_DIR=Data
MODULES_DIR=Modules
SYSMODULES_DIR=Systems/SysModules
BACKUPS_DIR=Backups

🎯 При разработке:
- Все сервисы должны быть асинхронными.
- Для HTTP используем FastAPI.
- Для Telegram — Aiogram 3.22 с Dispatcher.
- Конфигурацию читаем через python-dotenv.
- Для БД — SQLAlchemy ORM.
- Для брокеров — Redis или in-memory EventBus.

💬 От тебя я хочу:
- генерировать новый код, совместимый с этой архитектурой;
- помогать создавать новые SysModules или UserModules;
- писать чистый, поддерживаемый код (PEP8, async, type hints);
- интегрировать модули в WebPanel (FastAPI endpoints + шаблоны);
- при необходимости добавлять миграции Alembic для PostgreSQL;
- НЕ изменять структуру проекта — она финальная и утверждённая!

Полная структура SwiftDevBot (v1.0 — Microservice Modular Platform)

swiftdevbot/
│
├── Systems/                                  # 📦 Системная часть (ядро)
│   │
│   ├── core/                                 # 🧠 Общая логика фреймворка
│   │   ├── registry/                         # Реестр сервисов и heartbeat
│   │   ├── eventbus/                         # Шина сообщений (Redis/NATS)
│   │   ├── security/                         # Проверка подписей, лицензии
│   │   ├── database/                         # SQLAlchemy / ORM
│   │   ├── config/                           # Работа с .env и конфигами
│   │   ├── logging/                          # Единое логирование
│   │   └── utils/                            # Вспомогательные функции
│   │
│   ├── services/                             # ⚙️ Микросервисы (каждый автономен)
│   │   ├── bot_service/                      # Telegram listener
│   │   │   ├── main.py
│   │   │   ├── adapters/                     # aiogram ↔ EventBus
│   │   │   └── handlers/
│   │   │
│   │   ├── auth_service/                     # JWT, refresh, сессии
│   │   │   ├── main.py
│   │   │   ├── routes/
│   │   │   └── models/
│   │   │
│   │   ├── user_service/                     # Пользователи
│   │   │   ├── main.py
│   │   │   └── repository/
│   │   │
│   │   ├── rbac_service/                     # Права и роли
│   │   │   ├── main.py
│   │   │   ├── policies/
│   │   │   └── engine.py
│   │   │
│   │   ├── module_host/                      # Запуск и sandbox модулей
│   │   │   ├── main.py
│   │   │   ├── loader.py
│   │   │   └── sandbox/
│   │   │
│   │   └── admin_service/                    # REST API и диагностика
│   │       ├── main.py
│   │       └── routes/
│   │
│   ├── SysModules/                           # 🔒 Системные модули (встроенные)
│   │   ├── admin_panel/                      # Панель администратора
│   │   │   ├── backend/                      # FastAPI
│   │   │   └── frontend/                     # React/Vue билд
│   │   │
│   │   ├── webpanel/                         # Веб-панель пользователей
│   │   │   ├── backend/
│   │   │   │   ├── main.py                   # Основной FastAPI-сервер панели
│   │   │   │   ├── routes/                   # /profile, /settings, /modules
│   │   │   │   └── extension_loader.py       # Подключает web части модулей
│   │   │   └── frontend/                     # Скомпилированный UI
│   │   │
│   │   └── monitoring/                       # Мониторинг, метрики
│   │       └── module.py
│   │
│   ├── sdk/                                  # 🧩 SDK для модулей
│   │   ├── __init__.py
│   │   ├── base_module.py                    # BaseModule (основа для всех модулей)
│   │   ├── event_handler.py                  # Декораторы событий
│   │   ├── web_extension.py                  # Декораторы веб-вкладок
│   │   ├── client.py                         # EventBus клиент
│   │   ├── storage.py                        # Хранилище данных модуля
│   │   └── schemas.py                        # Pydantic-схемы
│   │
│   ├── cli/                                  # CLI интерфейс
│   │   ├── __init__.py
│   │   └── commands.py
│   │
│   └── scripts/                              # Вспомогательные скрипты
│       ├── backup.py
│       └── migrate.py
│
├── Modules/                                  # 🧱 Пользовательские модули
│   ├── welcome/
│   │   └── module.py
│   ├── weather/
│   │   └── module.py
│   ├── spam_filter/
│   │   └── module.py
│   └── template_module/                      # Шаблон для разработчиков
│       ├── module.py
│       ├── manifest.toml
│       ├── web/
│       │   ├── templates/
│       │   │   └── profile_tab.html
│       │   ├── static/
│       │   │   ├── style.css
│       │   │   └── script.js
│       │   └── routes.py
│       ├── handlers/
│       │   └── commands.py
│       ├── services/
│       │   └── service.py
│       ├── schemas/
│       │   └── schema.py
│       └── keyboards/
│           └── buttons.py
│
├── Data/                                     # 📊 Данные
│   ├── database/
│   ├── logs/
│   ├── uploads/
│   └── pids/
│
├── Backups/                                  # 💾 Резервные копии
│
├── docker-compose.yml                        # 🐳 Поднимает всё (Redis, PostgreSQL, сервисы)
├── .env.example                              # Пример конфигурации
├── requirements.txt
├── pyproject.toml
└── sdb.py                                    # CLI entry point


Modules/
└── weather/
	├── module.py                     # Основной класс модуля
	├── manifest.toml                 # Манифест (описание, зависимости)
	│
	├── web/                          # 🌐 Веб-интерфейс модуля (если есть)
	│   ├── templates/                # HTML шаблоны
	│   │   └── profile_tab.html
	│   ├── static/                   # JS, CSS, изображения
	│   │   ├── weather.js
	│   │   └── weather.css
	│   └── routes.py                 # FastAPI маршруты
	│
	├── handlers/                     # Telegram обработчики
	│   ├── commands.py
	│   ├── callbacks.py
	│   └── messages.py
	│
	├── services/                     # Внутренняя логика
	│   └── weather_service.py
	│
	├── schemas/                      # Pydantic модели
	│   └── weather_schema.py
	│
	├── states/                       # FSM состояния (aiogram)
	│   └── weather_state.py
	│
	├── keyboards/                    # Telegram клавиатуры
	│   └── weather_keyboards.py
	│
	└── __init__.py
	


