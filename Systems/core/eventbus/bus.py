import asyncio, os
from Systems.core.logging.logger import logger

try:
    import redis.asyncio as aioredis
except Exception:
    aioredis = None

class EventBus:
    def __init__(self, mode: str | None = None, redis_url: str | None = None, memory_max: int = 1000):
        self.mode = mode or os.getenv("EVENTBUS_MODE", "redis")
        self.redis_url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.memory_queue = asyncio.Queue(maxsize=memory_max)
        self.redis = None

    async def connect(self):
        if self.mode == "memory":
            logger.info("🧠 EventBus: memory mode enabled")
            return
        if aioredis is None:
            logger.warning("⚠️ Redis client not installed. Falling back to memory mode.")
            self.mode = "memory"
            return
        try:
            self.redis = aioredis.from_url(self.redis_url)
            await self.redis.ping()
            logger.info(f"🔌 EventBus: connected to Redis {self.redis_url}")
        except Exception as e:
            logger.warning(f"⚠️ Redis unavailable ({e}). Falling back to memory mode.")
            self.mode = "memory"

    async def publish(self, topic: str, payload: dict):
        if self.mode == "memory":
            await self.memory_queue.put((topic, payload))
        else:
            await self.redis.publish(topic, str(payload))

    async def subscribe(self, topic: str, handler):
        if self.mode == "memory":
            asyncio.create_task(self._memory_listener(handler))
        else:
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(topic)
            asyncio.create_task(self._redis_listener(pubsub, handler))

    async def _memory_listener(self, handler):
        while True:
            topic, payload = await self.memory_queue.get()
            await handler(topic, payload)

    async def _redis_listener(self, pubsub, handler):
        async for message in pubsub.listen():
            if message.get("type") == "message":
                await handler(message.get("channel"), message.get("data"))
