#!/usr/bin/env python3
"""
Test SDK Module - демонстрация возможностей SDK
"""

import asyncio
from Systems.sdk import BaseModule, get_event_client


class TestSDKModule(BaseModule):
    """Тестовый модуль для демонстрации SDK"""

    name = "test_sdk"
    version = "0.1.0"
    description = "Test module for SDK demonstration"
    author = "SwiftDevBot"
    requires = ["eventbus", "storage"]

    def __init__(self):
        super().__init__(__file__.replace('/module.py', ''))

    async def on_load(self):
        await super().on_load()
        self.logger.info("TestSDK module loaded!")

        # Инициализируем EventBus клиент
        self.eventbus = get_event_client(self.name)

        # Загружаем storage
        await self.storage.load()

        # Регистрируем обработчики
        self.logger.info(f"Registered {len(self.get_command_handlers())} commands")
        self.logger.info(f"Registered {len(self.get_event_handlers())} event types")
        self.logger.info(f"Registered {len(self.get_web_tabs())} web tabs")

    async def on_unload(self):
        await super().on_unload()
        # Сохраняем storage при выгрузке
        await self.storage.save()

    async def on_load(self):
        await super().on_load()

        # Регистрируем обработчики
        @self.on_command("test")
        async def handle_test_command(message):
            """Обработчик команды /test"""
            self.logger.info("Received /test command")

            # Сохраняем счетчик в storage
            counter = self.storage.get("command_counter", 0) + 1
            self.storage.set("command_counter", counter)

            # Отправляем ответ через EventBus
            await self.eventbus.send_notification(
                user_id=getattr(message.from_user, 'id', 0),
                message=f"Test command received! Counter: {counter}",
                type="success"
            )

            return f"Test executed {counter} times"

        @self.on_event("user.joined")
        async def handle_user_joined(event_data):
            """Обработчик события нового пользователя"""
            self.logger.info(f"New user joined: {event_data}")

            # Приветствуем нового пользователя
            user_id = event_data.get('user_id')
            if user_id:
                await self.eventbus.send_notification(
                    user_id=user_id,
                    message="Welcome to SwiftDevBot! Use /test to try the SDK.",
                    type="welcome"
                )

        @self.web_tab("Test SDK", "🧪")
        async def render_web_tab():
            """Web-вкладка для демонстрации SDK"""
            counter = self.storage.get("command_counter", 0)
            commands = list(self.get_command_handlers().keys())

            html = f"""
            <div class="sdk-demo">
                <h3>🧪 Test SDK Module</h3>
                <p>Version: {self.version}</p>
                <p>Commands executed: {counter}</p>
                <p>Available commands: {', '.join(commands)}</p>

                <div class="storage-demo">
                    <h4>📦 Storage Demo</h4>
                    <p>Stored keys: {list(self.storage.keys())}</p>
                </div>

                <div class="eventbus-demo">
                    <h4>📡 EventBus Demo</h4>
                    <p>Module can send notifications and handle events</p>
                </div>
            </div>

            <style>
            .sdk-demo {{
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
            }}
            .storage-demo, .eventbus-demo {{
                margin-top: 15px;
                padding: 10px;
                background: white;
                border-radius: 4px;
            }}
            </style>
            """

            return html


# Создаем экземпляр модуля
module = TestSDKModule()
