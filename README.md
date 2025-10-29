# SwiftDevBot - Modular Telegram Bot Platform

Модульная платформа для создания Telegram ботов с микросервисной архитектурой.

## 📁 Структура проекта

- `Systems/` - Ядро платформы и сервисы
- `Modules/` - Пользовательские модули бота
- `Data/` - Базы данных, логи, настройки
- `Docs/` - Документация и руководства
- `TEMP/` - Временные файлы для тестирования
- `Backups/` - Резервные копии

## 🚀 Быстрый старт

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск всех сервисов
bash run_dev.sh start

# Проверка статуса
bash run_dev.sh status

# Остановка сервисов
bash run_dev.sh stop
```

## 📚 Документация

- `Docs/ROADMAP.md` - План развития проекта
- `Docs/REGISTRATION_SYSTEM.md` - Система регистрации пользователей
- `Docs/CLEANUP_GUIDE.md` - Руководство по очистке

## ⚙️ Настройки

Основные настройки в `.env`:
- `DB_ENGINE` - Тип базы данных (postgres/mysql/sqlite)
- `REQUIRE_REGISTRATION` - Обязательная регистрация пользователей
- `BOT_TOKEN` - Токен Telegram бота

## 🛠️ CLI команды

```bash
python3 sdb.py progress    # Прогресс разработки
python3 sdb.py status      # Статус сервисов
python3 sdb.py clean       # Очистка проекта
python3 sdb.py module create <name>  # Создать модуль
```

## 📞 Поддержка

WebPanel доступен по адресу: http://localhost:8000
