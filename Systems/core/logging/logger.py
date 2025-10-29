"""
SwiftDevBot Logging System
--------------------------
Продвинутая система логирования для микросервисной платформы
"""

import os
import sys
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler

from Systems.core.config.settings import LOG_LEVEL, LOG_FORMAT, SDB_ENV


class JSONFormatter(logging.Formatter):
    """JSON formatter для структурированного логирования"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": getattr(record, 'service', 'unknown'),
            "module": getattr(record, 'module', 'unknown'),
            "request_id": getattr(record, 'request_id', None),
            "user_id": getattr(record, 'user_id', None),
        }

        # Добавляем extra поля
        if hasattr(record, 'extra_data') and record.extra_data:
            log_entry.update(record.extra_data)

        # Добавляем exception info
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


class TextFormatter(logging.Formatter):
    """Текстовый formatter для разработки"""

    def __init__(self):
        super().__init__(
            fmt="%(asctime)s %(levelname)8s %(name)-20s %(service)-15s %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

    def format(self, record: logging.LogRecord) -> str:
        # Добавляем service и module если не указаны
        if not hasattr(record, 'service'):
            record.service = getattr(record, 'service', 'unknown')
        if not hasattr(record, 'module'):
            record.module = getattr(record, 'module', 'unknown')

        return super().format(record)


class AsyncLogHandler(logging.Handler):
    """Асинхронный обработчик логов"""

    def __init__(self, queue: asyncio.Queue):
        super().__init__()
        self.queue = queue

    def emit(self, record: logging.LogRecord) -> None:
        # Отправляем в очередь для асинхронной обработки
        try:
            self.queue.put_nowait(record)
        except asyncio.QueueFull:
            # Если очередь полная, логируем синхронно
            print(f"AsyncLogHandler: queue full, dropping log: {record.getMessage()}", file=sys.stderr)


class SwiftDevBotLogger:
    """Основной класс логгера SwiftDevBot"""

    def __init__(self):
        self.loggers: Dict[str, logging.Logger] = {}
        self.log_queue = asyncio.Queue(maxsize=1000)
        self.running = False
        self._setup_complete = False

    def setup_logging(self):
        """Настройка системы логирования"""
        if self._setup_complete:
            return

        # Создаем директорию для логов
        log_dir = Path("Data/logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        # Определяем уровень логирования
        level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)

        # Создаем корневой логгер
        root_logger = logging.getLogger("swiftdevbot")
        root_logger.setLevel(level)

        # Очищаем существующие хендлеры
        root_logger.handlers.clear()

        # Выбираем formatter
        if LOG_FORMAT == "json" or SDB_ENV == "prod":
            formatter = JSONFormatter()
        else:
            formatter = TextFormatter()

        # Консольный хендлер (для всех сред)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

        # Файловый хендлер с ротацией (для prod)
        if SDB_ENV == "prod":
            file_handler = TimedRotatingFileHandler(
                filename=log_dir / "swiftdevbot.log",
                when="midnight",
                interval=1,
                backupCount=30
            )
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(JSONFormatter())
            root_logger.addHandler(file_handler)

            # Отдельный файл для ошибок
            error_handler = TimedRotatingFileHandler(
                filename=log_dir / "swiftdevbot.error.log",
                when="midnight",
                interval=1,
                backupCount=30
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(JSONFormatter())
            root_logger.addHandler(error_handler)

        # Асинхронный хендлер для высокой производительности
        async_handler = AsyncLogHandler(self.log_queue)
        async_handler.setLevel(level)
        async_handler.setFormatter(formatter)
        root_logger.addHandler(async_handler)

        self._setup_complete = True

    async def start_async_processing(self):
        """Запуск асинхронной обработки логов"""
        if not self.running:
            asyncio.create_task(self._process_log_queue())

    def get_logger(self, name: str, service: str = "unknown", module: str = "unknown") -> logging.Logger:
        """Получить логгер для конкретного компонента"""
        logger_name = f"swiftdevbot.{name}"
        if logger_name not in self.loggers:
            logger = logging.getLogger(logger_name)

            # Добавляем кастомные атрибуты
            logger.service = service
            logger.module = module

            self.loggers[logger_name] = logger

        return self.loggers[logger_name]

    async def _process_log_queue(self):
        """Асинхронная обработка очереди логов"""
        self.running = True
        while self.running:
            try:
                # Ждем следующую запись с таймаутом
                record = await asyncio.wait_for(self.log_queue.get(), timeout=1.0)

                # Здесь можно добавить дополнительную обработку:
                # - Отправка в внешние системы (Elasticsearch, Loki, etc.)
                # - Агрегация метрик
                # - Фильтрация чувствительных данных

                # Пока просто пропускаем дальше
                pass

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Log processing error: {e}", file=sys.stderr)

    async def shutdown(self):
        """Корректное завершение работы логгера"""
        self.running = False
        # Очищаем очередь
        while not self.log_queue.empty():
            try:
                self.log_queue.get_nowait()
            except asyncio.QueueEmpty:
                break

    def log_with_context(self, logger: logging.Logger, level: int, message: str,
                        request_id: Optional[str] = None, user_id: Optional[str] = None,
                        extra_data: Optional[Dict[str, Any]] = None, **kwargs):
        """Логирование с дополнительным контекстом"""
        extra = {
            'request_id': request_id,
            'user_id': user_id,
            'extra_data': extra_data or {},
            **kwargs
        }

        logger.log(level, message, extra=extra)


# Глобальный экземпляр логгера
logger_system = SwiftDevBotLogger()

# Основной логгер для обратной совместимости (с базовой настройкой)
logger_system.setup_logging()
logger = logger_system.get_logger("core", "system", "logging")


# Функции для удобного использования
def get_logger(name: str, service: str = "unknown", module: str = "unknown") -> logging.Logger:
    """Получить логгер для компонента"""
    return logger_system.get_logger(name, service, module)


def log_with_context(logger: logging.Logger, level: int, message: str, **context):
    """Логировать с контекстом"""
    logger_system.log_with_context(logger, level, message, **context)


# Инициализация при импорте
async def init_logging():
    """Асинхронная инициализация системы логирования"""
    await logger_system.start_async_processing()


async def shutdown_logging():
    """Завершение работы системы логирования"""
    await logger_system.shutdown()
