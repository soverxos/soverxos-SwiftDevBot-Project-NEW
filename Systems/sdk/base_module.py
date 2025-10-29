"""
Base Module Class for SwiftDevBot Modules
Provides core functionality and decorators for module development
"""

import asyncio
import inspect
import os
from typing import Dict, List, Callable, Any, Optional
from pathlib import Path

from Systems.core.logging.logger import get_logger


class BaseModule:
    """Base class for all SwiftDevBot modules"""

    # Module metadata
    name: str = "Module"
    version: str = "0.0.1"
    description: str = ""
    author: str = ""
    requires: List[str] = []  # Required permissions/services

    # Module directory
    module_dir: Optional[Path] = None

    def __init__(self, module_path: Optional[str] = None):
        """Initialize module with path"""
        self.module_dir = Path(module_path) if module_path else None

        # Get proper logger
        self.logger = get_logger(f"module.{self.name}", "module", f"{self.name}")

        # Storage for registered handlers
        self._command_handlers: Dict[str, Callable] = {}
        self._event_handlers: Dict[str, List[Callable]] = {}
        self._web_tabs: Dict[str, Dict[str, Any]] = {}

        # Initialize storage
        self.storage = ModuleStorage(self)

        # Module state
        self.loaded = False
        self.running = False

    async def on_load(self):
        """Called when module is loaded"""
        self.logger.info(f"Module {self.name} v{self.version} loaded")
        self.loaded = True

    async def on_unload(self):
        """Called when module is unloaded"""
        self.logger.info(f"Module {self.name} unloaded")
        self.loaded = False

    async def on_start(self):
        """Called when module starts"""
        self.logger.info(f"Module {self.name} started")
        self.running = True

    async def on_stop(self):
        """Called when module stops"""
        self.logger.info(f"Module {self.name} stopped")
        self.running = False

    # Decorator methods
    def on_command(self, command: str):
        """Decorator to register command handler"""
        def decorator(func):
            self._command_handlers[command] = func
            self.logger.debug(f"Registered command handler: {command} -> {func.__name__}")
            return func
        return decorator

    def on_event(self, event: str):
        """Decorator to register event handler"""
        def decorator(func):
            if event not in self._event_handlers:
                self._event_handlers[event] = []
            self._event_handlers[event].append(func)
            self.logger.debug(f"Registered event handler: {event} -> {func.__name__}")
            return func
        return decorator

    def web_tab(self, title: str, icon: str = "🧩"):
        """Decorator to register web tab"""
        def decorator(func):
            self._web_tabs[title] = {
                'handler': func,
                'icon': icon,
                'title': title
            }
            self.logger.debug(f"Registered web tab: {title}")
            return func
        return decorator

    # Handler getters for module host
    def get_command_handlers(self) -> Dict[str, Callable]:
        """Get all registered command handlers"""
        return self._command_handlers

    def get_event_handlers(self) -> Dict[str, List[Callable]]:
        """Get all registered event handlers"""
        return self._event_handlers

    def get_web_tabs(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered web tabs"""
        return self._web_tabs

    # Utility methods
    def get_resource_path(self, relative_path: str) -> Path:
        """Get absolute path to module resource"""
        if self.module_dir:
            return self.module_dir / relative_path
        return Path(relative_path)

    def has_permission(self, permission: str) -> bool:
        """Check if module has specific permission"""
        return permission in self.requires


class ModuleStorage:
    """Local storage for modules using JSON files"""

    def __init__(self, module: BaseModule):
        self.module = module
        self._data: Dict[str, Any] = {}
        self._loaded = False

    def _get_storage_path(self) -> Path:
        """Get storage file path"""
        storage_dir = Path("Data/module_storage")
        storage_dir.mkdir(exist_ok=True)
        return storage_dir / f"{self.module.name}.json"

    async def load(self):
        """Load storage data from file"""
        import json
        storage_path = self._get_storage_path()

        if storage_path.exists():
            try:
                with open(storage_path, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
                self._loaded = True
                self.module.logger.debug(f"Storage loaded from {storage_path}")
            except Exception as e:
                self.module.logger.warning(f"Failed to load storage: {e}")
                self._data = {}
        else:
            self._data = {}

    async def save(self):
        """Save storage data to file"""
        import json
        storage_path = self._get_storage_path()

        try:
            with open(storage_path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            self.module.logger.debug(f"Storage saved to {storage_path}")
        except Exception as e:
            self.module.logger.error(f"Failed to save storage: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get value from storage"""
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        """Set value in storage"""
        self._data[key] = value

    def delete(self, key: str):
        """Delete value from storage"""
        if key in self._data:
            del self._data[key]

    def keys(self):
        """Get all storage keys"""
        return self._data.keys()

    def clear(self):
        """Clear all storage data"""
        self._data.clear()
