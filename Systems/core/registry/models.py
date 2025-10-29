"""
Service Registry Models
----------------------
Структуры данных для системы регистрации сервисов
"""

import time
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict


@dataclass
class ServiceInfo:
    """Информация о зарегистрированном сервисе"""
    name: str
    host: str
    port: int
    service_type: str  # web, bot, api, system
    version: str = "1.0.0"
    status: str = "unknown"  # unknown, healthy, unhealthy, offline
    last_heartbeat: Optional[float] = None
    uptime: float = 0.0
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def is_healthy(self) -> bool:
        """Проверка здоровья сервиса"""
        if self.last_heartbeat is None:
            return False
        return time.time() - self.last_heartbeat < 30  # 30 секунд таймаут

    def update_heartbeat(self):
        """Обновить время последнего heartbeat"""
        now = time.time()
        if self.last_heartbeat:
            self.uptime += now - self.last_heartbeat
        self.last_heartbeat = now
        self.status = "healthy" if self.is_healthy else "unhealthy"

