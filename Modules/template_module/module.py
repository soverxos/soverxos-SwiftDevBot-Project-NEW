#!/usr/bin/env python3
"""
Template Module - Complete SDK Example
Demonstrates all SDK features for module development
"""

import asyncio
from datetime import datetime
from typing import Dict, Any
from Systems.sdk import BaseModule, get_event_client


class TemplateModule(BaseModule):
    """Complete example of SDK usage"""

    name = "template_module"
    version = "1.0.0"
    description = "Complete SDK demonstration module"
    author = "SwiftDevBot"
    requires = ["eventbus", "storage"]

    def __init__(self):
        super().__init__(__file__.replace('/module.py', ''))

    async def on_load(self):
        await super().on_load()

        # Инициализируем EventBus клиент
        self.eventbus = get_event_client(self.name)

        # Загружаем настройки
        await self.storage.load()

        # Инициализируем счетчики
        self.command_usage = self.storage.get("command_usage", {})
        self.event_count = self.storage.get("event_count", 0)

        # Регистрируем обработчики команд
        @self.on_command("template")
        async def handle_template(message):
            """Демонстрационная команда"""
            user = getattr(message, 'from_user', None)
            if not user:
                return "No user info"

            # Обновляем статистику
            cmd = "template"
            if cmd not in self.command_usage:
                self.command_usage[cmd] = 0
            self.command_usage[cmd] += 1
            await self.storage.set("command_usage", self.command_usage)
            await self.storage.save()

            response = f"""🎭 Template Module Demo

👤 User: {user.id} ({getattr(user, 'username', 'N/A')})
📊 Command used {self.command_usage[cmd]} times
🕐 Time: {datetime.now().strftime('%H:%M:%S')}

Available commands:
/template - This demo
/echo <text> - Echo your message
/counter - Show usage counter
/sdk_info - SDK information"""

            await self.eventbus.send_notification(
                user_id=user.id,
                message=response,
                type="info"
            )

            return f"Template command executed by {user.id}"

        @self.on_command("echo")
        async def handle_echo(message):
            """Повторяет сообщение пользователя"""
            args = getattr(message, 'text', '').split()[1:]
            if not args:
                response = "❌ Please provide text to echo. Usage: /echo <your message>"
            else:
                text = " ".join(args)
                response = f"🔊 Echo: {text}"

            await self.eventbus.send_notification(
                user_id=getattr(message.from_user, 'id', 0),
                message=response,
                type="success" if args else "error"
            )

            return f"Echo processed: {' '.join(args) if args else 'no args'}"

        @self.on_command("counter")
        async def handle_counter(message):
            """Показывает счетчики использования"""
            user_id = getattr(message.from_user, 'id', 0)

            total_commands = sum(self.command_usage.values())
            most_used = max(self.command_usage.items(), key=lambda x: x[1]) if self.command_usage else ("None", 0)

            response = f"""📊 Template Module Statistics:

🎯 Total commands executed: {total_commands}
🏆 Most used command: {most_used[0]} ({most_used[1]} times)
📈 Command usage breakdown:
"""

            for cmd, count in sorted(self.command_usage.items(), key=lambda x: x[1], reverse=True):
                response += f"  /{cmd}: {count} times\n"

            response += f"\n📡 Events processed: {self.event_count}"

            await self.eventbus.send_notification(
                user_id=user_id,
                message=response,
                type="info"
            )

            return f"Stats sent to {user_id}"

        @self.on_command("sdk_info")
        async def handle_sdk_info(message):
            """Показывает информацию о SDK"""
            user_id = getattr(message.from_user, 'id', 0)

            response = """🧠 SwiftDevBot SDK Information

📦 SDK Components:
• BaseModule - Base class for all modules
• ModuleStorage - Persistent JSON storage
• EventBusClient - Event system communication
• Decorators: @on_command, @on_event, @web_tab

🎯 Module Features:
• Command handling
• Event processing
• Web interface integration
• Persistent storage
• Logging system
• Permission management

📚 SDK Methods:
• self.logger - Structured logging
• self.storage - Persistent key-value storage
• self.eventbus - Event system communication
• self.on_command() - Register command handler
• self.on_event() - Register event handler
• self.web_tab() - Register web interface

🔗 Resources:
• Documentation: Available in SDK source
• Examples: Check other modules
• Support: Built-in logging and error handling"""

            await self.eventbus.send_notification(
                user_id=user_id,
                message=response,
                type="info"
            )

            return "SDK info sent"

        # Регистрируем обработчики событий
        @self.on_event("user.joined")
        async def handle_user_join(event_data):
            """Обработчик нового пользователя"""
            user_id = event_data.get('user_id')
            if user_id:
                self.event_count += 1
                await self.storage.set("event_count", self.event_count)
                await self.storage.save()

                self.logger.info(f"Template module: New user {user_id} joined (event #{self.event_count})")

        @self.on_event("message.received")
        async def handle_message(event_data):
            """Обработчик сообщений (демонстрация)"""
            message = event_data.get("message", {})
            text = message.get("text", "").lower()

            # Счетчик упоминаний слова "template"
            if "template" in text and len(text.split()) > 1:  # Не считать команду /template
                mentions = self.storage.get("template_mentions", 0) + 1
                await self.storage.set("template_mentions", mentions)
                await self.storage.save()

        # Регистрируем web-вкладку
        @self.web_tab("Template Module", "🎭")
        async def render_template_tab():
            """Web-вкладка с демонстрацией SDK"""
            total_commands = sum(self.command_usage.values())
            template_mentions = self.storage.get("template_mentions", 0)

            html = f"""
            <div class="template-demo">
                <h2>🎭 Template Module - SDK Demo</h2>
                <p class="description">Complete demonstration of SwiftDevBot SDK capabilities</p>

                <div class="features-grid">
                    <div class="feature-card">
                        <h3>🎯 Commands</h3>
                        <ul>
                            <li>Command registration with @on_command</li>
                            <li>Automatic argument parsing</li>
                            <li>Response formatting</li>
                            <li>Usage statistics</li>
                        </ul>
                    </div>

                    <div class="feature-card">
                        <h3>📡 Events</h3>
                        <ul>
                            <li>Event handling with @on_event</li>
                            <li>Real-time message processing</li>
                            <li>User activity tracking</li>
                            <li>Automated responses</li>
                        </ul>
                    </div>

                    <div class="feature-card">
                        <h3>💾 Storage</h3>
                        <ul>
                            <li>Persistent JSON storage</li>
                            <li>Automatic save/load</li>
                            <li>Key-value operations</li>
                            <li>Data persistence</li>
                        </ul>
                    </div>

                    <div class="feature-card">
                        <h3>🌐 Web Interface</h3>
                        <ul>
                            <li>Dynamic HTML generation</li>
                            <li>CSS styling integration</li>
                            <li>Real-time statistics</li>
                            <li>Interactive elements</li>
                        </ul>
                    </div>
                </div>

                <div class="stats-section">
                    <h3>📊 Module Statistics</h3>
                    <div class="stats-container">
                        <div class="stat-item">
                            <span class="stat-label">Total Commands:</span>
                            <span class="stat-value">{total_commands}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Events Processed:</span>
                            <span class="stat-value">{self.event_count}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Template Mentions:</span>
                            <span class="stat-value">{template_mentions}</span>
                        </div>
                        <div class="stat-item">
                            <span class="stat-label">Module Version:</span>
                            <span class="stat-value">{self.version}</span>
                        </div>
                    </div>
                </div>

                <div class="commands-demo">
                    <h3>💬 Try Commands</h3>
                    <div class="command-examples">
                        <div class="command-item">
                            <code>/template</code>
                            <p>Main demo command with statistics</p>
                        </div>
                        <div class="command-item">
                            <code>/echo Hello SDK!</code>
                            <p>Echo your message back</p>
                        </div>
                        <div class="command-item">
                            <code>/counter</code>
                            <p>View usage statistics</p>
                        </div>
                        <div class="command-item">
                            <code>/sdk_info</code>
                            <p>Learn about SDK features</p>
                        </div>
                    </div>
                </div>

                <div class="code-example">
                    <h3>💻 SDK Usage Example</h3>
                    <pre><code>from Systems.sdk import BaseModule

class MyModule(BaseModule):
    name = "my_module"
    version = "1.0.0"

    @BaseModule.on_command("hello")
    async def handle_hello(self, message):
        return "Hello from SDK!"

    @BaseModule.on_event("user.joined")
    async def handle_join(self, event):
        user_id = event.get('user_id')
        # Process new user

    @BaseModule.web_tab("My Tab", "🚀")
    async def render_tab(self):
        return "<h3>My Web Interface</h3>"</code></pre>
                </div>
            </div>

            <style>
            .template-demo {{
                max-width: 1000px;
                margin: 0 auto;
                padding: 20px;
            }}

            .description {{
                font-size: 1.1em;
                color: #666;
                text-align: center;
                margin-bottom: 40px;
            }}

            .features-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 40px;
            }}

            .feature-card {{
                background: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                border: 1px solid #e9ecef;
            }}

            .feature-card h3 {{
                margin: 0 0 15px 0;
                color: #007bff;
            }}

            .feature-card ul {{
                list-style: none;
                padding: 0;
                margin: 0;
            }}

            .feature-card li {{
                padding: 5px 0;
                border-bottom: 1px solid #f0f0f0;
                color: #666;
            }}

            .feature-card li:last-child {{
                border-bottom: none;
            }}

            .stats-section {{
                background: white;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 30px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}

            .stats-container {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 15px;
                margin-top: 15px;
            }}

            .stat-item {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 4px;
            }}

            .stat-label {{
                font-weight: bold;
                color: #495057;
            }}

            .stat-value {{
                font-size: 1.2em;
                color: #007bff;
                font-weight: bold;
            }}

            .commands-demo {{
                background: white;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 30px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}

            .command-examples {{
                display: grid;
                gap: 15px;
                margin-top: 15px;
            }}

            .command-item {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 4px;
                border-left: 4px solid #28a745;
            }}

            .command-item code {{
                display: block;
                font-family: 'Courier New', monospace;
                font-weight: bold;
                color: #28a745;
                margin-bottom: 5px;
            }}

            .command-item p {{
                margin: 0;
                color: #666;
            }}

            .code-example {{
                background: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}

            .code-example pre {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 4px;
                overflow-x: auto;
                margin-top: 15px;
            }}

            .code-example code {{
                font-family: 'Courier New', monospace;
                font-size: 0.9em;
                color: #495057;
            }}
            </style>
            """

            return html

    async def on_start(self):
        await super().on_start()

        # Сохраняем время запуска
        start_time = datetime.now().isoformat()
        await self.storage.set("last_started", start_time)
        await self.storage.save()

        self.logger.info(f"Template module started at {start_time}")

    async def on_unload(self):
        await super().on_unload()

        # Финальное сохранение статистики
        await self.storage.save()
        self.logger.info("Template module unloaded")


# Создаем экземпляр модуля
module = TemplateModule()
