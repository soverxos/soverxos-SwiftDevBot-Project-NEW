# 🚀 SwiftDevBot — Roadmap до версии 1.0

**SwiftDevBot** — модульная микросервисная платформа для Telegram-ботов,  
разработанная на Python 3.12+ с использованием `aiogram`, `FastAPI`, `SQLAlchemy` и `Redis`.

---

## 🧩 Версии и этапы

| Этап | Версия | Статус | Цель |
|------|---------|--------|------|
| ⚙️ Stage 1 | v0.2 — Core Foundation | 🔄 В разработке | Создание базового ядра и микросервисов |
| 🧠 Stage 2 | v0.5 — Modular Runtime | 🕐 Планируется | Поддержка SDK, загрузка модулей, WebPanel |
| 🚀 Stage 3 | v1.0 — Production Release | 🕐 Планируется | Полностью рабочая SaaS-платформа |

---

## ⚙️ **Stage 1 — Core Foundation (v0.2)**

🧠 **Цель:** создать минимально работоспособную платформу с ядром, CLI и запуском сервисов.

### 🧱 Основные задачи:
- [x] Структура проекта (`Systems`, `Modules`, `Data`, `Backups`)
- [x] Сервисы: `bot_service`, `auth_service`, `user_service`, `rbac_service`, `module_host`, `admin_service`
- [x] `.env` конфигурация с SQLite + Memory
- [x] Run скрипты: `run_dev.sh`, `run_prod.sh`
- [x] Запуск всех сервисов через bash/systemd
- [x] WebPanel mock (порт 8000)
- [x] Dockerfile + docker-compose.yml
- [x] Сервисный мониторинг (`run_dev.sh status`)
- [x] Единое логирование `core/logging`
- [x] Менеджер конфигурации `core/config`
- [x] Универсальный EventBus (`memory`/`redis`)
- [x] Database engine (SQLAlchemy + Alembic)
- [x] Registry heartbeat (health-check микросервисов)
- [x] Security: базовая валидация лицензии

---

## 🧠 **Stage 2 — Modular Runtime (v0.5)**

🧩 **Цель:** реализовать модульность, SDK и подключаемые Web-интерфейсы.

### 💡 Задачи по слоям:

#### ⚙️ Core
- [x] Расширить EventBus: подписки, RPC-вызовы
- [ ] Добавить sandbox-исполнение модулей
- [x] Поддержка hot-reload без рестарта ядра
- [ ] Security — цифровая подпись модулей

#### 🧠 SDK
- [x] `BaseModule` — основной класс модулей
- [x] `@on_command`, `@web_tab` — декораторы SDK
- [x] Локальное хранилище модулей (`storage`)
- [x] Клиент EventBus (`sdk/client.py`)
- [x] Документация SDK для разработчиков

#### 🌐 WebPanel
- [x] FastAPI сервер
- [x] Подключение web-вкладок модулей
- [ ] Авторизация через Auth Service
- [x] Интерфейс `/profile`, `/settings`, `/modules`
- [x] Поддержка шаблонов и статических файлов

#### 🧰 CLI
- [x] Команды:
  - `sdb.py start/stop/status`
  - `sdb.py module list/reload`
  - `sdb.py user add`
  - `sdb.py backup create`
  - `sdb.py license verify`

#### 🧱 Примеры модулей
- [x] `welcome` — приветствие
- [x] `weather` — API OpenWeather
- [x] `spam_filter` — антиспам
- [x] `template_module` — пример SDK-взаимодействия
- [ ] `web_demo` — пример web-вкладки в профиле

---

## 🚀 **Stage 3 — Production Release (v1.0)**

🏁 **Цель:** платформа готова к коммерческому использованию и масштабированию.

### 🔒 Безопасность
- [ ] Лицензирование RSA (ограничения по пользователям и модулям)
- [ ] RBAC везде (API, WebPanel, CLI)
- [ ] HTTPS-only (через Nginx / Certbot)
- [ ] CSP и secure cookies в WebPanel

### 💾 Инфраструктура
- [ ] systemd unit-файлы для всех сервисов
- [ ] logrotate для Data/logs/
- [ ] deploy/backup.sh (Postgres + uploads)
- [ ] health-check aggregator (`/services/status`)
- [ ] Grafana + Prometheus интеграция
- [ ] Автообновления (git pull + reload)
- [ ] Pre-commit hooks (black, isort, mypy)

### 🌐 WebPanel
- [ ] UI темизация (тёмная/светлая темы)
- [ ] WebSockets (live monitoring)
- [ ] Панель администратора (SysModules/admin_panel)
- [ ] OAuth 2.0 (через Telegram или GitHub)
- [ ] Журнал аудита операций

### 📦 Модули и экосистема
- [ ] Marketplace загрузки модулей
- [ ] Подпись модулей (PGP)
- [ ] Автообновление модулей
- [ ] Интеграция с внешними API (например, GitHub Actions, DockerHub)

---

## 🧩 **Будущее (v1.1–v2.0)**

- [ ] GUI-установка модулей (через WebPanel)
- [ ] SaaS Multi-tenant режим (изолированные рабочие пространства)
- [ ] REST API для внешних интеграций
- [ ] Асинхронный кластерный EventBus (на NATS или Kafka)
- [ ] Поддержка внешних адаптеров (Discord, Slack)
- [ ] Интеграция с облачными хранилищами (S3, Google Drive)
- [ ] Поддержка SwiftDevBot Cloud (remote deploy и лицензии)

---

## 🧾 Приоритеты

| Приоритет | Направление | Обоснование |
|------------|--------------|--------------|
| 🔥 | Ядро и EventBus | Без них система не масштабируется |
| 🧩 | SDK | Основа модульности и совместимости |
| 🌐 | WebPanel | UI и API для пользователей |
| 🔒 | Security & RBAC | Безопасность и лицензирование |
| 🧰 | CLI & DevOps | Простота обслуживания и деплоя |

---

## 🧭 Финальная цель
> **SwiftDevBot v1.0** — это готовая к развёртыванию SaaS-платформа,  
> где можно запускать десятки микросервисов, создавать и подключать  
> любые Telegram-модули с web-интерфейсами, логикой и безопасностью уровня Botpress.

---

📅 **Плановые версии:**
- `v0.2` — Core Foundation (2025 Q4)
- `v0.5` — Modular Runtime (2026 Q1)
- `v1.0` — Production Ready (2026 Q2)
