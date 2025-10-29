"""
Service Health Monitoring
------------------------
Логика мониторинга здоровья сервисов
"""

import asyncio
import time
from typing import Dict, List

from Systems.core.logging.logger import logger


class HealthChecker:
    """Мониторинг здоровья зарегистрированных сервисов"""

    def __init__(self, services: Dict[str, 'ServiceInfo'], eventbus=None):
        self.services = services
        self.eventbus = eventbus
        self.health_check_interval = 5  # секунд
        self._running = False

    async def start(self):
        """Запуск проверки здоровья"""
        if self._running:
            return

        self._running = True
        asyncio.create_task(self._health_check_loop())

    async def stop(self):
        """Остановка проверки здоровья"""
        self._running = False

    async def _health_check_loop(self):
        """Основной цикл проверки здоровья"""
        while self._running:
            try:
                unhealthy_services = []

                for name, service in self.services.items():
                    was_healthy = service.is_healthy
                    is_healthy = service.is_healthy  # Перепроверка

                    if was_healthy and not is_healthy:
                        service.status = "unhealthy"
                        unhealthy_services.append(name)
                        logger.warning(f"⚠️ HealthChecker: service {name} became unhealthy")

                    elif not was_healthy and is_healthy:
                        service.status = "healthy"
                        logger.info(f"✅ HealthChecker: service {name} recovered")

                # Отправка отчёта о здоровье
                if unhealthy_services and self.eventbus:
                    await self.eventbus.publish("registry:health_alert", {
                        "unhealthy_services": unhealthy_services,
                        "timestamp": time.time()
                    })

                await asyncio.sleep(self.health_check_interval)

            except Exception as e:
                logger.error(f"❌ HealthChecker: health check error: {e}")
                await asyncio.sleep(1)

