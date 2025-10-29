"""
Service Registry Core
--------------------
Основная логика реестра микросервисов
"""

import asyncio
from typing import Dict, Any, Optional, List

from Systems.core.logging.logger import logger
from Systems.core.eventbus.bus import EventBus
from Systems.core.database.engine import get_async_session
from Systems.core.database.models import Setting

from .models import ServiceInfo
from .health import HealthChecker
from .heartbeat import HeartbeatMonitor


class ServiceRegistry:
    """Реестр микросервисов с heartbeat мониторингом"""

    def __init__(self):
        self.services: Dict[str, ServiceInfo] = {}
        self.eventbus: Optional[EventBus] = None
        self.health_checker: Optional[HealthChecker] = None
        self.heartbeat_monitor: Optional[HeartbeatMonitor] = None
        self._running = False

    async def initialize(self, eventbus: EventBus):
        """Инициализация реестра"""
        self.eventbus = eventbus
        self.health_checker = HealthChecker(self.services, eventbus)
        self.heartbeat_monitor = HeartbeatMonitor(eventbus)

        logger.info("🔧 ServiceRegistry: initializing...")

        # Подписка на события heartbeat
        await self.eventbus.subscribe("service:heartbeat", self._handle_heartbeat)
        await self.eventbus.subscribe("service:register", self._handle_register)
        await self.eventbus.subscribe("service:unregister", self._handle_unregister)

        # Загрузка сохранённых сервисов из БД
        await self._load_services_from_db()

        logger.info(f"✅ ServiceRegistry: initialized with {len(self.services)} services")

    async def start_monitoring(self):
        """Запуск мониторинга сервисов"""
        if self._running:
            return

        self._running = True
        logger.info("🔄 ServiceRegistry: starting monitoring...")

        # Запуск компонентов мониторинга
        await self.health_checker.start()
        await self.heartbeat_monitor.start("registry")

    async def stop_monitoring(self):
        """Остановка мониторинга"""
        self._running = False

        if self.health_checker:
            await self.health_checker.stop()
        if self.heartbeat_monitor:
            await self.heartbeat_monitor.stop()

        logger.info("🛑 ServiceRegistry: monitoring stopped")

    async def register_service(self, service_info: ServiceInfo):
        """Регистрация нового сервиса"""
        self.services[service_info.name] = service_info
        service_info.update_heartbeat()

        logger.info(f"📝 ServiceRegistry: registered service {service_info.name} "
                   f"({service_info.host}:{service_info.port})")

        # Сохранение в БД
        await self._save_service_to_db(service_info)

        # Отправка события
        if self.eventbus:
            await self.eventbus.publish("registry:service_registered", service_info.to_dict())

    async def unregister_service(self, service_name: str):
        """Отмена регистрации сервиса"""
        if service_name in self.services:
            service_info = self.services.pop(service_name)
            logger.info(f"📝 ServiceRegistry: unregistered service {service_name}")

            # Удаление из БД
            await self._delete_service_from_db(service_name)

            # Отправка события
            if self.eventbus:
                await self.eventbus.publish("registry:service_unregistered", service_info.to_dict())

    def get_service(self, name: str) -> Optional[ServiceInfo]:
        """Получить информацию о сервисе"""
        return self.services.get(name)

    def get_services_by_type(self, service_type: str) -> List[ServiceInfo]:
        """Получить все сервисы определённого типа"""
        return [s for s in self.services.values() if s.service_type == service_type]

    def get_all_services(self) -> Dict[str, ServiceInfo]:
        """Получить все зарегистрированные сервисы"""
        return self.services.copy()

    def get_health_status(self) -> Dict[str, Any]:
        """Получить общий статус здоровья системы"""
        total = len(self.services)
        healthy = sum(1 for s in self.services.values() if s.is_healthy)

        return {
            "total_services": total,
            "healthy_services": healthy,
            "unhealthy_services": total - healthy,
            "health_percentage": round((healthy / total * 100), 1) if total > 0 else 0,
            "services": {name: {"status": s.status, "uptime": s.uptime}
                        for name, s in self.services.items()}
        }

    async def _handle_heartbeat(self, topic: str, payload: Dict[str, Any]):
        """Обработка heartbeat сообщения"""
        service_name = payload.get("service_name")
        if service_name and service_name in self.services:
            self.services[service_name].update_heartbeat()
            logger.debug(f"💓 ServiceRegistry: heartbeat from {service_name}")

    async def _handle_register(self, topic: str, payload: Dict[str, Any]):
        """Обработка регистрации сервиса"""
        service_info = ServiceInfo(**payload)
        await self.register_service(service_info)

    async def _handle_unregister(self, topic: str, payload: Dict[str, Any]):
        """Обработка отмены регистрации"""
        service_name = payload.get("service_name")
        if service_name:
            await self.unregister_service(service_name)

    async def _load_services_from_db(self):
        """Загрузка сервисов из базы данных"""
        try:
            async with get_async_session() as session:
                # Здесь можно добавить логику загрузки из БД
                # Пока что загружаем статически известные сервисы
                known_services = [
                    ServiceInfo("webpanel", "localhost", 8000, "web", "1.0.0"),
                    ServiceInfo("auth_service", "localhost", 8101, "api", "1.0.0"),
                    ServiceInfo("user_service", "localhost", 8102, "api", "1.0.0"),
                    ServiceInfo("rbac_service", "localhost", 8103, "api", "1.0.0"),
                    ServiceInfo("module_host", "localhost", 8104, "system", "1.0.0"),
                    ServiceInfo("admin_service", "localhost", 8105, "api", "1.0.0"),
                    ServiceInfo("bot_service", "localhost", 0, "bot", "1.0.0"),
                ]

                for service in known_services:
                    self.services[service.name] = service

        except Exception as e:
            logger.error(f"❌ ServiceRegistry: failed to load services from DB: {e}")

    async def _save_service_to_db(self, service_info: ServiceInfo):
        """Сохранение сервиса в базу данных"""
        try:
            async with get_async_session() as session:
                # Здесь можно добавить логику сохранения в БД
                pass
        except Exception as e:
            logger.error(f"❌ ServiceRegistry: failed to save service to DB: {e}")

    async def _delete_service_from_db(self, service_name: str):
        """Удаление сервиса из базы данных"""
        try:
            async with get_async_session() as session:
                # Здесь можно добавить логику удаления из БД
                pass
        except Exception as e:
            logger.error(f"❌ ServiceRegistry: failed to delete service from DB: {e}")

