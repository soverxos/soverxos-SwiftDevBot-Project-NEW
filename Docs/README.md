# SwiftDevBot SDK Documentation

## Overview

The SwiftDevBot SDK provides a comprehensive framework for developing modular extensions (modules) for the SwiftDevBot platform. Modules can add new commands, handle events, provide web interfaces, and persist data.

## Core Components

### BaseModule

The `BaseModule` class is the foundation for all modules. It provides:

- **Metadata**: name, version, description, author, requirements
- **Lifecycle management**: `on_load()`, `on_unload()`, `on_start()`, `on_stop()`
- **Decorators**: `@on_command()`, `@on_event()`, `@web_tab()`
- **Built-in services**: logger, storage, eventbus client

### ModuleStorage

Persistent JSON-based storage for module data:

```python
# Set a value
await self.storage.set("key", "value")

# Get a value
value = self.storage.get("key", "default")

# Save to disk
await self.storage.save()

# Load from disk
await self.storage.load()
```

### EventBusClient

Simplified interface for EventBus communication:

```python
# Send notification
await self.eventbus.send_notification(user_id, "Hello!", "info")

# Publish event
await self.eventbus.publish("custom.event", {"data": "value"})

# Call RPC
response = await self.eventbus.call_rpc("service", "method", param="value")
```

## Creating a Module

### Basic Structure

```python
from Systems.sdk import BaseModule, get_event_client

class MyModule(BaseModule):
    name = "my_module"
    version = "1.0.0"
    description = "My awesome module"
    author = "Developer"
    requires = ["eventbus", "storage"]  # Optional permissions

    def __init__(self):
        super().__init__(__file__.replace('/module.py', ''))

    async def on_load(self):
        await super().on_load()
        self.eventbus = get_event_client(self.name)
        await self.storage.load()

        # Register handlers here
        @self.on_command("hello")
        async def handle_hello(self, message):
            await self.eventbus.send_notification(
                message.from_user.id,
                "Hello from my module!",
                "success"
            )

# Create module instance
module = MyModule()
```

### Command Handlers

Use the `@on_command` decorator to register Telegram commands:

```python
@self.on_command("greet")
async def handle_greet(self, message):
    """Greet a user"""
    user = message.from_user
    username = user.username or "User"

    await self.eventbus.send_notification(
        user.id,
        f"Hello, {username}! 👋",
        "welcome"
    )

    return f"Greeted {user.id}"
```

### Event Handlers

Use the `@on_event` decorator to handle system events:

```python
@self.on_event("user.joined")
async def handle_user_join(self, event_data):
    """Handle new user joining"""
    user_id = event_data.get('user_id')

    # Update statistics
    count = self.storage.get("user_count", 0) + 1
    await self.storage.set("user_count", count)
    await self.storage.save()

    self.logger.info(f"New user {user_id}, total: {count}")
```

### Web Interface

Use the `@web_tab` decorator to add web interface tabs:

```python
@self.web_tab("My Stats", "📊")
async def render_stats_tab(self):
    """Render statistics web tab"""
    user_count = self.storage.get("user_count", 0)

    html = f"""
    <div class="stats">
        <h2>📊 My Module Statistics</h2>
        <p>Total users greeted: <strong>{user_count}</strong></p>
        <p>Module version: <strong>{self.version}</strong></p>
    </div>

    <style>
    .stats {{
        padding: 20px;
        background: white;
        border-radius: 8px;
    }}
    </style>
    """

    return html
```

## Available Events

### System Events

- `user.joined` - New user joined
- `user.left` - User left
- `message.received` - New message received
- `command.executed` - Command was executed

### Bot Events

- `bot.started` - Bot started
- `bot.stopped` - Bot stopped
- `module.loaded` - Module was loaded
- `module.unloaded` - Module was unloaded

## Best Practices

### 1. Error Handling

Always wrap operations in try-catch blocks:

```python
@self.on_command("weather")
async def handle_weather(self, message):
    try:
        # Your code here
        city = message.text.split()[1]
        weather = await self.get_weather(city)

        await self.eventbus.send_notification(
            message.from_user.id,
            f"Weather in {city}: {weather}",
            "info"
        )
    except Exception as e:
        self.logger.error(f"Weather command failed: {e}")
        await self.eventbus.send_notification(
            message.from_user.id,
            "❌ Failed to get weather data",
            "error"
        )
```

### 2. Storage Management

Use storage for persistent data:

```python
async def on_load(self):
    await self.storage.load()
    # Initialize defaults
    if not self.storage.get("initialized"):
        await self.storage.set("user_count", 0)
        await self.storage.set("initialized", True)
        await self.storage.save()

async def on_unload(self):
    # Always save on unload
    await self.storage.save()
```

### 3. Logging

Use structured logging:

```python
self.logger.info("Module started", extra={"version": self.version})
self.logger.error("API call failed", extra={"endpoint": url, "error": str(e)})
self.logger.debug("Processing user", extra={"user_id": user_id})
```

### 4. Permissions

Check permissions when needed:

```python
if not self.has_permission("admin"):
    return "Admin permission required"

if not self._is_admin(user_id):
    await self.eventbus.send_notification(
        user_id, "Access denied", "error"
    )
    return
```

## Module Requirements

Specify required permissions in the `requires` list:

```python
requires = ["eventbus", "storage", "admin_permissions", "http"]
```

Available permissions:
- `eventbus` - Access to EventBus
- `storage` - Persistent storage
- `admin_permissions` - Admin operations
- `http` - HTTP requests
- `database` - Direct database access

## Deployment

1. Create module directory: `Modules/your_module/`
2. Create `module.py` with your module class
3. Optionally add static files, templates, etc.
4. The module will be automatically discovered and loaded

## Examples

Check the included example modules:
- `welcome` - Basic command and event handling
- `weather` - External API integration
- `spam_filter` - Advanced event processing
- `template_module` - Complete SDK demonstration

## Support

For questions and issues:
- Check existing modules for examples
- Review SDK source code for advanced features
- Use logging for debugging
- Check platform logs for errors
