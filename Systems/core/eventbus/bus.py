"""
Universal EventBus for SwiftDevBot
----------------------------------
Продвинутая шина сообщений с поддержкой pub/sub, RPC и разных брокеров
"""

import asyncio
import json
import uuid
import time
from typing import Dict, Any, Callable, Optional, List, Union, Awaitable
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod

from Systems.core.logging.logger import get_logger
from Systems.core.config.settings import EVENTBUS_MODE, REDIS_URL, SDB_ENV

logger = get_logger("eventbus", "system", "eventbus")


@dataclass
class Message:
    """Универсальное сообщение EventBus"""
    id: str
    topic: str
    payload: Dict[str, Any]
    timestamp: float
    source: str = "unknown"
    correlation_id: Optional[str] = None
    reply_to: Optional[str] = None
    headers: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.headers is None:
            self.headers = {}

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        return cls(**data)

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls, json_str: str) -> 'Message':
        return cls.from_dict(json.loads(json_str))


@dataclass
class RPCRequest:
    """RPC запрос"""
    id: str
    method: str
    params: Dict[str, Any]
    timeout: float = 30.0
    correlation_id: Optional[str] = None

    def to_message(self, source: str) -> Message:
        return Message(
            id=self.id,
            topic=f"rpc.{self.method}",
            payload=self.params,
            timestamp=time.time(),
            source=source,
            correlation_id=self.correlation_id,
            headers={"rpc": True, "timeout": self.timeout}
        )


@dataclass
class RPCResponse:
    """RPC ответ"""
    id: str
    result: Optional[Any] = None
    error: Optional[str] = None
    correlation_id: str = ""

    def to_message(self, source: str) -> Message:
        return Message(
            id=self.id,
            topic="rpc.response",
            payload={"result": self.result, "error": self.error},
            timestamp=time.time(),
            source=source,
            correlation_id=self.correlation_id,
            headers={"rpc_response": True}
        )


class BrokerBackend(ABC):
    """Абстрактный бэкенд для брокера сообщений"""

    @abstractmethod
    async def connect(self) -> bool:
        """Подключиться к брокеру"""
        pass

    @abstractmethod
    async def disconnect(self):
        """Отключиться от брокера"""
        pass

    @abstractmethod
    async def publish(self, message: Message):
        """Опубликовать сообщение"""
        pass

    @abstractmethod
    async def subscribe(self, topic: str, handler: Callable[[Message], Awaitable[None]]):
        """Подписаться на топик"""
        pass

    @abstractmethod
    async def unsubscribe(self, topic: str):
        """Отписаться от топика"""
        pass


class MemoryBroker(BrokerBackend):
    """In-memory брокер для разработки"""

    def __init__(self, max_queue_size: int = 10000):
        self.queue = asyncio.Queue(maxsize=max_queue_size)
        self.subscriptions: Dict[str, List[Callable]] = {}
        self.running = False

    async def connect(self) -> bool:
        self.running = True
        asyncio.create_task(self._process_messages())
        logger.info("🧠 MemoryBroker: connected")
        return True

    async def disconnect(self):
        self.running = False
        logger.info("🧠 MemoryBroker: disconnected")

    async def publish(self, message: Message):
        await self.queue.put(message)

    async def subscribe(self, topic: str, handler: Callable[[Message], Awaitable[None]]):
        if topic not in self.subscriptions:
            self.subscriptions[topic] = []
        self.subscriptions[topic].append(handler)
        logger.debug(f"🧠 MemoryBroker: subscribed to {topic}")

    async def unsubscribe(self, topic: str):
        if topic in self.subscriptions:
            del self.subscriptions[topic]
            logger.debug(f"🧠 MemoryBroker: unsubscribed from {topic}")

    async def _process_messages(self):
        while self.running:
            try:
                message = await asyncio.wait_for(self.queue.get(), timeout=1.0)

                # Рассылаем подписчикам
                for topic, handlers in self.subscriptions.items():
                    if self._topic_matches(message.topic, topic):
                        for handler in handlers:
                            try:
                                await handler(message)
                            except Exception as e:
                                logger.error(f"🧠 MemoryBroker: handler error: {e}")

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"🧠 MemoryBroker: processing error: {e}")

    def _topic_matches(self, message_topic: str, subscription_topic: str) -> bool:
        """Проверка совпадения топика с поддержкой wildcards"""
        if subscription_topic == "*":
            return True
        if subscription_topic.endswith(".*"):
            return message_topic.startswith(subscription_topic[:-1])
        return message_topic == subscription_topic


class RedisBroker(BrokerBackend):
    """Redis брокер для продакшена"""

    def __init__(self, redis_url: str):
        self.redis_url = redis_url
        self.redis = None
        self.pubsub = None
        self.subscriptions: Dict[str, Callable] = {}

    async def connect(self) -> bool:
        try:
            import redis.asyncio as aioredis

            self.redis = aioredis.from_url(self.redis_url)
            await self.redis.ping()

            self.pubsub = self.redis.pubsub()
            logger.info(f"🔌 RedisBroker: connected to {self.redis_url}")
            return True

        except ImportError:
            logger.error("🔌 RedisBroker: redis library not installed")
            return False
        except Exception as e:
            logger.error(f"🔌 RedisBroker: connection failed: {e}")
            return False

    async def disconnect(self):
        if self.pubsub:
            await self.pubsub.unsubscribe()
        if self.redis:
            await self.redis.close()
        logger.info("🔌 RedisBroker: disconnected")

    async def publish(self, message: Message):
        if not self.redis:
            return

        try:
            await self.redis.publish(message.topic, message.to_json())
        except Exception as e:
            logger.error(f"🔌 RedisBroker: publish error: {e}")

    async def subscribe(self, topic: str, handler: Callable[[Message], Awaitable[None]]):
        if not self.pubsub:
            return

        self.subscriptions[topic] = handler

        try:
            await self.pubsub.subscribe(topic)
            asyncio.create_task(self._redis_listener())
            logger.debug(f"🔌 RedisBroker: subscribed to {topic}")
        except Exception as e:
            logger.error(f"🔌 RedisBroker: subscribe error: {e}")

    async def unsubscribe(self, topic: str):
        if topic in self.subscriptions:
            del self.subscriptions[topic]
        if self.pubsub:
            await self.pubsub.unsubscribe(topic)
        logger.debug(f"🔌 RedisBroker: unsubscribed from {topic}")

    async def _redis_listener(self):
        if not self.pubsub:
            return

        try:
            async for redis_message in self.pubsub.listen():
                if redis_message.get("type") == "message":
                    try:
                        message = Message.from_json(redis_message.get("data", "{}"))

                        # Рассылаем подписчикам
                        for topic, handler in self.subscriptions.items():
                            if self._topic_matches(message.topic, topic):
                                await handler(message)

                    except Exception as e:
                        logger.error(f"🔌 RedisBroker: message processing error: {e}")

        except Exception as e:
            logger.error(f"🔌 RedisBroker: listener error: {e}")

    def _topic_matches(self, message_topic: str, subscription_topic: str) -> bool:
        """Проверка совпадения топика с поддержкой wildcards"""
        # Redis pubsub не поддерживает wildcards, но мы можем эмулировать
        if subscription_topic == "*":
            return True
        if subscription_topic.endswith(".*"):
            return message_topic.startswith(subscription_topic[:-1])
        return message_topic == subscription_topic


class EventBus:
    """Универсальная шина сообщений SwiftDevBot"""

    def __init__(self, broker: Optional[BrokerBackend] = None):
        self.broker = broker
        self.rpc_handlers: Dict[str, Callable] = {}
        self.pending_requests: Dict[str, asyncio.Future] = {}
        self.middlewares: List[Callable[[Message], Awaitable[Message]]] = []
        self.connected = False

    async def initialize(self):
        """Инициализация EventBus"""
        if not self.broker:
            # Автоматический выбор брокера
            if EVENTBUS_MODE == "redis":
                self.broker = RedisBroker(REDIS_URL)
            else:
                from Systems.core.config.settings import EVENTBUS_MEMORY_MAX
                self.broker = MemoryBroker(EVENTBUS_MEMORY_MAX)

        self.connected = await self.broker.connect()

        if self.connected:
            # Подписываемся на RPC ответы
            await self.subscribe("rpc.response", self._handle_rpc_response)
            logger.info(f"🚀 EventBus initialized with {self.broker.__class__.__name__}")
        else:
            logger.error("❌ EventBus initialization failed")

    async def shutdown(self):
        """Завершение работы EventBus"""
        if self.broker:
            await self.broker.disconnect()
        self.connected = False

        # Отменяем все ожидающие RPC запросы
        for future in self.pending_requests.values():
            if not future.done():
                future.cancel()

        logger.info("🛑 EventBus shutdown")

    # === Pub/Sub API ===

    async def publish(self, topic: str, payload: Dict[str, Any], **kwargs):
        """Опубликовать сообщение"""
        if not self.connected:
            logger.warning("⚠️ EventBus: not connected, message dropped")
            return

        message = Message(
            id=str(uuid.uuid4()),
            topic=topic,
            payload=payload,
            timestamp=time.time(),
            **kwargs
        )

        # Применяем middleware
        for middleware in self.middlewares:
            message = await middleware(message)

        await self.broker.publish(message)
        logger.debug(f"📤 Published: {topic}")

    async def subscribe(self, topic: str, handler: Callable[[Message], Awaitable[None]]):
        """Подписаться на топик"""
        if not self.connected:
            logger.warning("⚠️ EventBus: not connected, subscription failed")
            return

        async def wrapped_handler(message: Message):
            try:
                await handler(message)
            except Exception as e:
                logger.error(f"❌ Handler error for topic {topic}: {e}")

        await self.broker.subscribe(topic, wrapped_handler)
        logger.debug(f"📥 Subscribed: {topic}")

    async def unsubscribe(self, topic: str):
        """Отписаться от топика"""
        if self.broker:
            await self.broker.unsubscribe(topic)

    # === RPC API ===

    async def register_rpc_handler(self, method: str, handler: Callable[[Dict[str, Any]], Awaitable[Any]]):
        """Зарегистрировать RPC обработчик"""
        self.rpc_handlers[method] = handler

        # Подписываемся на RPC вызовы для этого метода
        await self.subscribe(f"rpc.{method}", self._handle_rpc_call)
        logger.info(f"🔧 RPC handler registered: {method}")

    async def call_rpc(self, method: str, params: Dict[str, Any] = None, timeout: float = 30.0) -> Any:
        """Вызвать RPC метод"""
        if params is None:
            params = {}

        request = RPCRequest(
            id=str(uuid.uuid4()),
            method=method,
            params=params,
            timeout=timeout
        )

        # Создаем Future для ожидания ответа
        future = asyncio.Future()
        self.pending_requests[request.id] = future

        # Отправляем запрос
        message = request.to_message("client")
        await self.broker.publish(message)

        try:
            # Ждем ответа с таймаутом
            response_message = await asyncio.wait_for(future, timeout=timeout)

            if response_message.payload.get("error"):
                raise Exception(response_message.payload["error"])

            return response_message.payload.get("result")

        except asyncio.TimeoutError:
            raise Exception(f"RPC timeout: {method}")
        finally:
            # Очищаем pending request
            self.pending_requests.pop(request.id, None)

    async def _handle_rpc_call(self, message: Message):
        """Обработка входящего RPC вызова"""
        method = message.topic.replace("rpc.", "")

        if method not in self.rpc_handlers:
            # Отправляем ошибку
            error_response = RPCResponse(
                id=str(uuid.uuid4()),
                error=f"Method not found: {method}",
                correlation_id=message.correlation_id or message.id
            )
            await self.broker.publish(error_response.to_message("server"))
            return

        try:
            # Выполняем RPC метод
            handler = self.rpc_handlers[method]
            result = await handler(message.payload)

            # Отправляем успешный ответ
            success_response = RPCResponse(
                id=str(uuid.uuid4()),
                result=result,
                correlation_id=message.correlation_id or message.id
            )
            await self.broker.publish(success_response.to_message("server"))

        except Exception as e:
            # Отправляем ошибку
            error_response = RPCResponse(
                id=str(uuid.uuid4()),
                error=str(e),
                correlation_id=message.correlation_id or message.id
            )
            await self.broker.publish(error_response.to_message("server"))

    async def _handle_rpc_response(self, message: Message):
        """Обработка RPC ответа"""
        correlation_id = message.correlation_id
        if correlation_id in self.pending_requests:
            future = self.pending_requests[correlation_id]
            if not future.done():
                future.set_result(message)

    def add_middleware(self, middleware: Callable[[Message], Awaitable[Message]]):
        """Добавить middleware"""
        self.middlewares.append(middleware)

    # === Legacy API (для обратной совместимости) ===

    async def connect(self):
        """Устаревший метод для совместимости"""
        await self.initialize()

    async def disconnect(self):
        """Устаревший метод для совместимости"""
        await self.shutdown()


# Глобальный экземпляр EventBus
eventbus = EventBus()
