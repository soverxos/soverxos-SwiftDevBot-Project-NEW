"""
Service Registry Package
-----------------------
Система регистрации и мониторинга здоровья микросервисов SwiftDevBot
"""

from .models import ServiceInfo
from .registry import ServiceRegistry
from .health import HealthChecker
from .heartbeat import HeartbeatMonitor

# Глобальный экземпляр реестра
registry = ServiceRegistry()

__all__ = [
    "ServiceInfo",
    "ServiceRegistry",
    "HealthChecker",
    "HeartbeatMonitor",
    "registry"
]
