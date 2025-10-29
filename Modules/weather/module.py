#!/usr/bin/env python3
"""
Weather Module - Weather information via OpenWeather API
Provides weather forecasts and current conditions
"""

import aiohttp
import json
from typing import Dict, Any, Optional
from Systems.sdk import BaseModule, get_event_client


class Weather(BaseModule):
    """Weather module using OpenWeather API"""

    name = "weather"
    version = "1.0.0"
    description = "Weather information and forecasts"
    author = "SwiftDevBot"
    requires = ["eventbus", "storage", "http"]

    def __init__(self):
        super().__init__(__file__.replace('/module.py', ''))

    async def on_load(self):
        await super().on_load()

        # Инициализируем EventBus клиент
        self.eventbus = get_event_client(self.name)

        # Загружаем настройки
        await self.storage.load()

        # Получаем API ключ из storage или переменных окружения
        self.api_key = self.storage.get("openweather_api_key") or self._get_env_api_key()

        if not self.api_key:
            self.logger.warning("OpenWeather API key not found. Set OPENWEATHER_API_KEY env var or configure via web interface")

        # Регистрируем обработчики команд
        @self.on_command("weather")
        async def handle_weather(message):
            """Показать погоду для указанного города"""
            args = message.text.split()[1:] if hasattr(message, 'text') else []
            city = " ".join(args) if args else "Moscow"

            weather_data = await self.get_weather(city)
            if weather_data:
                response = self.format_weather_response(weather_data)
            else:
                response = f"❌ Не удалось получить погоду для города '{city}'"

            await self.eventbus.send_notification(
                user_id=getattr(message.from_user, 'id', 0),
                message=response,
                type="info"
            )

            return f"Weather sent for {city}"

        @self.on_command("forecast")
        async def handle_forecast(message):
            """Показать прогноз погоды на 5 дней"""
            args = message.text.split()[1:] if hasattr(message, 'text') else []
            city = " ".join(args) if args else "Moscow"

            forecast_data = await self.get_forecast(city)
            if forecast_data:
                response = self.format_forecast_response(forecast_data)
            else:
                response = f"❌ Не удалось получить прогноз для города '{city}'"

            await self.eventbus.send_notification(
                user_id=getattr(message.from_user, 'id', 0),
                message=response,
                type="info"
            )

            return f"Forecast sent for {city}"

        @self.web_tab("Weather", "🌤️")
        async def render_weather_tab():
            """Web-вкладка с настройками погоды"""
            api_configured = bool(self.api_key)
            default_city = self.storage.get("default_city", "Moscow")
            last_requests = self.storage.get("request_count", 0)

            html = f"""
            <div class="weather-settings">
                <h2>🌤️ Weather Module Settings</h2>

                <div class="status-card">
                    <h3>📊 Module Status</h3>
                    <div class="status-info">
                        <p><strong>API Key:</strong> {'✅ Configured' if api_configured else '❌ Not configured'}</p>
                        <p><strong>Default City:</strong> {default_city}</p>
                        <p><strong>Requests Today:</strong> {last_requests}</p>
                        <p><strong>Version:</strong> {self.version}</p>
                    </div>
                </div>

                <div class="commands-section">
                    <h3>💬 Available Commands</h3>
                    <div class="commands-list">
                        <div class="command-item">
                            <code>/weather [city]</code>
                            <p>Get current weather for a city (default: Moscow)</p>
                        </div>
                        <div class="command-item">
                            <code>/forecast [city]</code>
                            <p>Get 5-day weather forecast</p>
                        </div>
                    </div>
                </div>

                <div class="quick-weather">
                    <h3>🌤️ Quick Weather Check</h3>
                    <div class="city-buttons">
                        <button onclick="checkWeather('Moscow')">Moscow</button>
                        <button onclick="checkWeather('Saint Petersburg')">SPb</button>
                        <button onclick="checkWeather('London')">London</button>
                        <button onclick="checkWeather('New York')">New York</button>
                    </div>
                    <div id="weather-result" class="weather-result"></div>
                </div>

                {'<div class="api-setup"><h3>🔑 API Setup Required</h3><p>Get your free API key from <a href="https://openweathermap.org/api" target="_blank">OpenWeatherMap</a></p><p>Set OPENWEATHER_API_KEY environment variable</p></div>' if not api_configured else ''}
            </div>

            <style>
            .weather-settings {{
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
            }}

            .status-card, .commands-section, .quick-weather, .api-setup {{
                background: white;
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}

            .status-info {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 4px;
            }}

            .status-info p {{
                margin: 8px 0;
                display: flex;
                justify-content: space-between;
            }}

            .commands-list {{
                display: grid;
                gap: 15px;
            }}

            .command-item {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 4px;
                border-left: 4px solid #007bff;
            }}

            .command-item code {{
                display: block;
                font-family: 'Courier New', monospace;
                font-weight: bold;
                color: #007bff;
                margin-bottom: 5px;
            }}

            .command-item p {{
                margin: 0;
                color: #666;
            }}

            .city-buttons {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
                gap: 10px;
                margin-bottom: 20px;
            }}

            .city-buttons button {{
                padding: 10px 15px;
                border: 1px solid #007bff;
                background: white;
                color: #007bff;
                border-radius: 4px;
                cursor: pointer;
                transition: all 0.3s;
            }}

            .city-buttons button:hover {{
                background: #007bff;
                color: white;
            }}

            .weather-result {{
                min-height: 100px;
                background: #f8f9fa;
                border-radius: 4px;
                padding: 15px;
                display: none;
            }}

            .weather-result.show {{
                display: block;
            }}

            .api-setup {{
                background: #fff3cd;
                border: 1px solid #ffeeba;
                color: #856404;
            }}

            .api-setup a {{
                color: #856404;
                text-decoration: underline;
            }}
            </style>

            <script>
            async function checkWeather(city) {{
                const resultDiv = document.getElementById('weather-result');
                resultDiv.innerHTML = '<p>🌤️ Loading weather data...</p>';
                resultDiv.classList.add('show');

                try {{
                    // This would normally call the weather API
                    // For demo purposes, showing a placeholder
                    setTimeout(() => {{
                        resultDiv.innerHTML = `
                            <h4>🌤️ Weather in ${{city}}</h4>
                            <p><strong>Temperature:</strong> 22°C</p>
                            <p><strong>Conditions:</strong> Partly cloudy</p>
                            <p><strong>Humidity:</strong> 65%</p>
                            <p><small>Note: Real weather data requires API key configuration</small></p>
                        `;
                    }}, 1000);
                }} catch (error) {{
                    resultDiv.innerHTML = '<p>❌ Error loading weather data</p>';
                }}
            }}
            </script>
            """

            return html

    def _get_env_api_key(self) -> Optional[str]:
        """Get API key from environment"""
        import os
        return os.getenv("OPENWEATHER_API_KEY")

    async def get_weather(self, city: str) -> Optional[Dict[str, Any]]:
        """Get current weather for city"""
        if not self.api_key:
            return None

        try:
            url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.api_key}&units=metric&lang=ru"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Update request counter
                        count = self.storage.get("request_count", 0) + 1
                        self.storage.set("request_count", count)
                        await self.storage.save()
                        return data
                    else:
                        self.logger.warning(f"Weather API error: {response.status}")
                        return None

        except Exception as e:
            self.logger.error(f"Error fetching weather for {city}: {e}")
            return None

    async def get_forecast(self, city: str) -> Optional[Dict[str, Any]]:
        """Get 5-day forecast for city"""
        if not self.api_key:
            return None

        try:
            url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={self.api_key}&units=metric&lang=ru"

            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        # Update request counter
                        count = self.storage.get("request_count", 0) + 1
                        self.storage.set("request_count", count)
                        await self.storage.save()
                        return data
                    else:
                        self.logger.warning(f"Forecast API error: {response.status}")
                        return None

        except Exception as e:
            self.logger.error(f"Error fetching forecast for {city}: {e}")
            return None

    def format_weather_response(self, data: Dict[str, Any]) -> str:
        """Format weather data for Telegram message"""
        try:
            city = data["name"]
            temp = data["main"]["temp"]
            feels_like = data["main"]["feels_like"]
            humidity = data["main"]["humidity"]
            pressure = data["main"]["pressure"]
            wind_speed = data["wind"]["speed"]
            description = data["weather"][0]["description"].capitalize()

            response = f"""🌤️ Погода в {city}:

🌡️ Температура: {temp}°C (ощущается как {feels_like}°C)
💧 Влажность: {humidity}%
🧭 Давление: {pressure} hPa
💨 Ветер: {wind_speed} м/с
📝 {description}

Обновлено: {self._format_timestamp(data['dt'])}"""

            return response

        except KeyError as e:
            self.logger.error(f"Error formatting weather data: {e}")
            return "❌ Ошибка форматирования данных о погоде"

    def format_forecast_response(self, data: Dict[str, Any]) -> str:
        """Format forecast data for Telegram message"""
        try:
            city = data["city"]["name"]
            forecasts = data["list"][:5]  # First 5 entries (every 3 hours)

            response = f"📅 Прогноз погоды для {city} (5 дней):\n\n"

            for i, forecast in enumerate(forecasts):
                dt = self._format_timestamp(forecast["dt"])
                temp = forecast["main"]["temp"]
                description = forecast["weather"][0]["description"].capitalize()

                if i % 8 == 0:  # New day (every 8 * 3h = 24h)
                    day_num = (i // 8) + 1
                    response += f"📆 День {day_num}:\n"

                response += f"  {dt}: {temp}°C, {description}\n"

            return response

        except KeyError as e:
            self.logger.error(f"Error formatting forecast data: {e}")
            return "❌ Ошибка форматирования данных прогноза"

    def _format_timestamp(self, timestamp: int) -> str:
        """Format Unix timestamp to readable time"""
        from datetime import datetime
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%H:%M")


# Создаем экземпляр модуля
module = Weather()
