#!/usr/bin/env python3
"""
Welcome Module - приветствие новых пользователей
Демонстрирует базовые возможности SDK
"""

from Systems.sdk import BaseModule, get_event_client


class Welcome(BaseModule):
    """Модуль приветствия для новых пользователей SwiftDevBot"""

    name = "welcome"
    version = "1.0.0"
    description = "Welcome module for new users"
    author = "SwiftDevBot"
    requires = ["eventbus", "storage"]

    def __init__(self):
        super().__init__(__file__.replace('/module.py', ''))

    async def on_load(self):
        await super().on_load()

        # Инициализируем EventBus клиент
        self.eventbus = get_event_client(self.name)

        # Загружаем статистику
        await self.storage.load()

        # Регистрируем обработчики команд и событий
        @self.on_command("start")
        async def handle_start(message):
            """Обработчик команды /start"""
            user = message.from_user
            self.logger.info(f"User {user.id} ({user.username}) started the bot")

            # Сохраняем статистику
            starts = self.storage.get("total_starts", 0) + 1
            self.storage.set("total_starts", starts)
            await self.storage.save()

            # Отправляем приветствие
            await self.eventbus.send_notification(
                user_id=user.id,
                message="""🎉 Добро пожаловать в SwiftDevBot!

Это модульная платформа для Telegram ботов с открытым исходным кодом.

📋 Доступные команды:
/help - справка
/test - тест SDK

🌐 Web-интерфейс доступен по адресу: http://localhost:8000

Приятного использования! 🤖""",
                type="welcome"
            )

            return f"Welcome message sent to user {user.id}"

        @self.on_command("help")
        async def handle_help(message):
            """Обработчик команды /help"""
            help_text = """📚 Справка по SwiftDevBot

🤖 Основные команды:
/start - запуск бота и приветствие
/help - эта справка
/test - тест функциональности

🧩 Модули:
• Welcome - приветствие и справка
• Weather - погода (в разработке)
• Spam Filter - фильтр спама (в разработке)

🌐 Web-интерфейс: http://localhost:8000

💡 Для разработчиков: SDK позволяет создавать собственные модули
с командами, событиями и веб-интерфейсами."""

            await self.eventbus.send_notification(
                user_id=message.from_user.id,
                message=help_text,
                type="info"
            )

            return "Help sent"

        @self.on_command("stats")
        async def handle_stats(message):
            """Показать статистику использования"""
            if message.from_user.id != int(self.storage.get("admin_id", 0)):
                await self.eventbus.send_notification(
                    user_id=message.from_user.id,
                    message="❌ У вас нет прав для просмотра статистики",
                    type="error"
                )
                return "Access denied"

            total_starts = self.storage.get("total_starts", 0)
            total_users = self.storage.get("unique_users", 0)

            stats_text = f"""📊 Статистика Welcome модуля:

🚀 Всего запусков: {total_starts}
👥 Уникальных пользователей: {total_users}
📅 Версия модуля: {self.version}

🕐 Время работы: {self.storage.get('started_at', 'N/A')}"""

            await self.eventbus.send_notification(
                user_id=message.from_user.id,
                message=stats_text,
                type="info"
            )

            return f"Stats sent to admin {message.from_user.id}"

        @self.on_event("user.joined")
        async def handle_user_joined(event_data):
            """Обработчик события нового пользователя"""
            user_id = event_data.get('user_id')
            if user_id:
                self.logger.info(f"New user joined via event: {user_id}")

                # Обновляем счетчик уникальных пользователей
                unique_users = self.storage.get("unique_users", 0) + 1
                self.storage.set("unique_users", unique_users)
                await self.storage.save()

        @self.web_tab("Welcome", "🎉")
        async def render_welcome_tab():
            """Web-вкладка с информацией о модуле"""
            total_starts = self.storage.get("total_starts", 0)
            unique_users = self.storage.get("unique_users", 0)

            html = f"""
            <div class="welcome-tab">
                <h2>🎉 Welcome Module</h2>
                <p class="description">Приветствие новых пользователей и базовая справка</p>

                <div class="stats-grid">
                    <div class="stat-card">
                        <h3>🚀 Запусков бота</h3>
                        <div class="stat-number">{total_starts}</div>
                    </div>

                    <div class="stat-card">
                        <h3>👥 Уникальных пользователей</h3>
                        <div class="stat-number">{unique_users}</div>
                    </div>

                    <div class="stat-card">
                        <h3>📦 Версия модуля</h3>
                        <div class="stat-number">{self.version}</div>
                    </div>
                </div>

                <div class="features">
                    <h3>✨ Возможности</h3>
                    <ul>
                        <li>🎯 Обработка команд /start, /help, /stats</li>
                        <li>📡 Обработка событий user.joined</li>
                        <li>💾 Локальное хранилище данных</li>
                        <li>📊 Статистика использования</li>
                        <li>🌐 Web-интерфейс</li>
                    </ul>
                </div>

                <div class="commands">
                    <h3>💬 Доступные команды</h3>
                    <div class="command-list">
                        <code>/start</code> - приветствие и информация
                        <code>/help</code> - справка по боту
                        <code>/stats</code> - статистика (только админ)
                    </div>
                </div>
            </div>

            <style>
            .welcome-tab {{
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}

            .description {{
                font-size: 1.1em;
                color: #666;
                margin-bottom: 30px;
            }}

            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }}

            .stat-card {{
                background: white;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}

            .stat-card h3 {{
                margin: 0 0 10px 0;
                color: #666;
                font-size: 0.9em;
            }}

            .stat-number {{
                font-size: 2em;
                font-weight: bold;
                color: #007bff;
            }}

            .features, .commands {{
                background: white;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}

            .features ul {{
                list-style: none;
                padding: 0;
            }}

            .features li {{
                padding: 5px 0;
                border-bottom: 1px solid #eee;
            }}

            .features li:last-child {{
                border-bottom: none;
            }}

            .command-list {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 4px;
                font-family: monospace;
            }}

            .command-list code {{
                display: block;
                margin: 5px 0;
                color: #007bff;
            }}
            </style>
            """

            return html

    async def on_start(self):
        await super().on_start()

        # Сохраняем время запуска
        from datetime import datetime
        self.storage.set("started_at", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        await self.storage.save()

        self.logger.info("Welcome module started")


# Создаем экземпляр модуля
module = Welcome()
