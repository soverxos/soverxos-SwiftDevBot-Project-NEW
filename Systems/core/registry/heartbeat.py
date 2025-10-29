"""
Service Heartbeat Monitor
------------------------
Мониторинг heartbeat'ов зарегистрированных сервисов
"""

import asyncio
import time

from Systems.core.logging.logger import logger


class HeartbeatMonitor:
    """Мониторинг heartbeat'ов сервисов"""

    def __init__(self, eventbus=None):
        self.eventbus = eventbus
        self.heartbeat_interval = 10  # секунд
        self._running = False

    async def start(self, service_name: str = "registry"):
        """Запуск мониторинга heartbeat'ов"""
        if self._running:
            return

        self._running = True
        self.service_name = service_name
        asyncio.create_task(self._heartbeat_loop())

    async def stop(self):
        """Остановка мониторинга"""
        self._running = False

    async def _heartbeat_loop(self):
        """Основной цикл отправки heartbeat'ов"""
        while self._running:
            try:
                # Отправка собственного heartbeat
                if self.eventbus:
                    await self.eventbus.publish("service:heartbeat", {
                        "service_name": self.service_name,
                        "timestamp": time.time()
                    })

                await asyncio.sleep(self.heartbeat_interval)

            except Exception as e:
                logger.error(f"❌ HeartbeatMonitor: heartbeat error: {e}")
                await asyncio.sleep(1)

