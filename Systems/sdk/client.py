"""
EventBus Client for SwiftDevBot Modules
Provides simplified interface for modules to interact with EventBus
"""

import asyncio
from typing import Any, Callable, Dict, Optional
from Systems.core.eventbus.bus import eventbus
from Systems.core.logging.logger import get_logger


class EventBusClient:
    """Simplified EventBus client for modules"""

    def __init__(self, module_name: str):
        self.module_name = module_name
        self.logger = get_logger(f"module.{module_name}.eventbus", "module", module_name)
        self._subscriptions: Dict[str, Callable] = {}

    async def publish(self, topic: str, payload: Any = None, **kwargs):
        """Publish message to topic"""
        try:
            message = {
                'source': self.module_name,
                'payload': payload,
                **kwargs
            }
            await eventbus.publish(topic, message)
            self.logger.debug(f"Published to {topic}: {message}")
        except Exception as e:
            self.logger.error(f"Failed to publish to {topic}: {e}")

    async def subscribe(self, topic: str, callback: Callable):
        """Subscribe to topic"""
        try:
            # Wrap callback to add module context
            async def wrapped_callback(message):
                try:
                    await callback(message)
                except Exception as e:
                    self.logger.error(f"Error in callback for {topic}: {e}")

            await eventbus.subscribe(topic, wrapped_callback)
            self._subscriptions[topic] = callback
            self.logger.debug(f"Subscribed to {topic}")
        except Exception as e:
            self.logger.error(f"Failed to subscribe to {topic}: {e}")

    async def unsubscribe(self, topic: str):
        """Unsubscribe from topic"""
        try:
            if topic in self._subscriptions:
                # Note: EventBus doesn't have unsubscribe by callback yet
                # This is a placeholder for future implementation
                del self._subscriptions[topic]
                self.logger.debug(f"Unsubscribed from {topic}")
        except Exception as e:
            self.logger.error(f"Failed to unsubscribe from {topic}: {e}")

    async def call_rpc(self, service: str, method: str, **params) -> Any:
        """Call RPC method on service"""
        try:
            rpc_request = {
                'service': service,
                'method': method,
                'params': params,
                'source': self.module_name
            }

            response = await eventbus.call_rpc(service, method, rpc_request)
            self.logger.debug(f"RPC call to {service}.{method}: {response}")
            return response
        except Exception as e:
            self.logger.error(f"RPC call failed {service}.{method}: {e}")
            raise

    # High-level convenience methods
    async def send_notification(self, user_id: int, message: str, type: str = "info"):
        """Send notification to user"""
        await self.publish("user.notification", {
            'user_id': user_id,
            'message': message,
            'type': type
        })

    async def log_user_action(self, user_id: int, action: str, **details):
        """Log user action"""
        await self.publish("user.action", {
            'user_id': user_id,
            'action': action,
            'timestamp': asyncio.get_event_loop().time(),
            **details
        })

    async def request_user_data(self, user_id: int) -> Optional[Dict]:
        """Request user data via RPC"""
        try:
            response = await self.call_rpc("user_service", "get_user", user_id=user_id)
            return response.get('user') if response else None
        except Exception as e:
            self.logger.error(f"Failed to get user data for {user_id}: {e}")
            return None

    async def update_user_settings(self, user_id: int, settings: Dict):
        """Update user settings via RPC"""
        try:
            response = await self.call_rpc("user_service", "update_settings",
                                         user_id=user_id, settings=settings)
            return response.get('success', False)
        except Exception as e:
            self.logger.error(f"Failed to update settings for {user_id}: {e}")
            return False


# Global client instance for modules
event_client = None

def get_event_client(module_name: str) -> EventBusClient:
    """Get or create EventBus client for module"""
    global event_client
    if event_client is None:
        event_client = EventBusClient(module_name)
    return event_client
