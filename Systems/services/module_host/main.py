"""
Module Host Service
Manages loading, unloading, and execution of SwiftDevBot modules
"""

import asyncio
import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import inspect

from fastapi import FastAPI, HTTPException
import uvicorn

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Systems.core.logging.logger import get_logger, init_logging
from Systems.core.eventbus.bus import eventbus
from Systems.core.registry import registry
from Systems.core.registry.models import ServiceInfo
from Systems.sdk import BaseModule


class ModuleHost:
    """Module Host - manages module lifecycle"""

    def __init__(self):
        self.logger = get_logger("module_host", "service", "module_host")
        self.modules: Dict[str, BaseModule] = {}
        self.modules_path = Path("Modules")
        self.loaded_modules: Dict[str, Any] = {}

    async def initialize(self):
        """Initialize module host"""
        self.logger.info("Initializing Module Host...")

        # Ensure modules directory exists
        self.modules_path.mkdir(exist_ok=True)

        # Discover and load modules
        await self.discover_modules()
        await self.load_all_modules()

        self.logger.info(f"Module Host initialized with {len(self.modules)} modules")

    async def discover_modules(self):
        """Discover available modules"""
        self.logger.info("Discovering modules...")

        for module_dir in self.modules_path.iterdir():
            if module_dir.is_dir() and not module_dir.name.startswith('.'):
                module_py = module_dir / "module.py"
                if module_py.exists():
                    self.logger.debug(f"Found module: {module_dir.name}")
                    # Module will be loaded when needed

    async def load_module(self, module_name: str) -> bool:
        """Load a specific module"""
        try:
            module_path = self.modules_path / module_name / "module.py"

            if not module_path.exists():
                self.logger.error(f"Module {module_name} not found")
                return False

            self.logger.info(f"Loading module: {module_name}")

            # Import module dynamically
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            if spec is None or spec.loader is None:
                self.logger.error(f"Could not load spec for {module_name}")
                return False

            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # Find BaseModule instance
            module_instance = None
            for name, obj in inspect.getmembers(module):
                if isinstance(obj, BaseModule):
                    module_instance = obj
                    break

            if module_instance is None:
                self.logger.error(f"No BaseModule instance found in {module_name}")
                return False

            # Initialize module
            await module_instance.on_load()

            # Store module
            self.modules[module_name] = module_instance
            self.loaded_modules[module_name] = module

            # Register with registry
            service_info = ServiceInfo(
                name=f'module.{module_name}',
                host='module_host',
                port=8104,  # Module host port
                service_type='module',
                version=module_instance.version,
                metadata={
                    'description': module_instance.description,
                    'author': module_instance.author,
                    'commands': list(module_instance.get_command_handlers().keys()),
                    'web_tabs': list(module_instance.get_web_tabs().keys())
                }
            )
            await registry.register_service(service_info)

            self.logger.info(f"Module {module_name} loaded successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to load module {module_name}: {e}")
            return False

    async def unload_module(self, module_name: str) -> bool:
        """Unload a specific module"""
        try:
            if module_name not in self.modules:
                self.logger.warning(f"Module {module_name} not loaded")
                return False

            self.logger.info(f"Unloading module: {module_name}")

            # Call unload hook
            await self.modules[module_name].on_unload()

            # Unregister from registry
            await registry.unregister_service(f'module.{module_name}')

            # Remove from memory
            del self.modules[module_name]
            if module_name in self.loaded_modules:
                del sys.modules[module_name]
                del self.loaded_modules[module_name]

            self.logger.info(f"Module {module_name} unloaded successfully")
            return True

        except Exception as e:
            self.logger.error(f"Failed to unload module {module_name}: {e}")
            return False

    async def load_all_modules(self):
        """Load all discovered modules"""
        for module_dir in self.modules_path.iterdir():
            if module_dir.is_dir() and not module_dir.name.startswith('.'):
                await self.load_module(module_dir.name)

    async def reload_module(self, module_name: str) -> bool:
        """Reload a module (unload and load again)"""
        self.logger.info(f"Reloading module: {module_name}")

        # Unload first
        unloaded = await self.unload_module(module_name)
        if not unloaded:
            return False

        # Small delay to ensure cleanup
        await asyncio.sleep(0.1)

        # Load again
        return await self.load_module(module_name)

    def get_loaded_modules(self) -> Dict[str, Dict[str, Any]]:
        """Get information about loaded modules"""
        result = {}
        for name, module in self.modules.items():
            result[name] = {
                'name': module.name,
                'version': module.version,
                'description': module.description,
                'author': module.author,
                'commands': list(module.get_command_handlers().keys()),
                'events': list(module.get_event_handlers().keys()),
                'web_tabs': list(module.get_web_tabs().keys()),
                'loaded': module.loaded,
                'running': module.running
            }
        return result

    async def execute_command(self, module_name: str, command: str, *args, **kwargs) -> Any:
        """Execute command on a module"""
        if module_name not in self.modules:
            raise ValueError(f"Module {module_name} not loaded")

        module = self.modules[module_name]
        handlers = module.get_command_handlers()

        if command not in handlers:
            raise ValueError(f"Command {command} not found in module {module_name}")

        return await handlers[command](*args, **kwargs)

    async def shutdown(self):
        """Shutdown module host and unload all modules"""
        self.logger.info("Shutting down Module Host...")

        # Unload all modules
        for module_name in list(self.modules.keys()):
            await self.unload_module(module_name)

        self.logger.info("Module Host shutdown complete")


# Global module host instance
module_host = ModuleHost()

# FastAPI app
app = FastAPI(title="module_host", description="SwiftDevBot Module Host Service")

@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    await init_logging()
    await eventbus.initialize()
    await registry.initialize(eventbus)
    await module_host.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await module_host.shutdown()
    await registry.stop_monitoring()

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "modules_loaded": len(module_host.modules),
        "service": "module_host"
    }

@app.get("/modules")
async def list_modules():
    """List all loaded modules"""
    return {
        "modules": module_host.get_loaded_modules(),
        "total": len(module_host.modules)
    }

@app.get("/modules/{module_name}")
async def get_module_info(module_name: str):
    """Get information about a specific module"""
    if module_name not in module_host.modules:
        raise HTTPException(status_code=404, detail="Module not found")

    return module_host.get_loaded_modules()[module_name]

@app.post("/modules/{module_name}/load")
async def load_module_endpoint(module_name: str):
    """Load a module"""
    success = await module_host.load_module(module_name)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to load module")

    return {"status": "loaded", "module": module_name}

@app.post("/modules/{module_name}/unload")
async def unload_module_endpoint(module_name: str):
    """Unload a module"""
    success = await module_host.unload_module(module_name)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to unload module")

    return {"status": "unloaded", "module": module_name}

@app.post("/modules/{module_name}/reload")
async def reload_module_endpoint(module_name: str):
    """Reload a module"""
    success = await module_host.reload_module(module_name)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to reload module")

    return {"status": "reloaded", "module": module_name}

@app.get("/modules/{module_name}/health")
async def module_health(module_name: str):
    """Module health check"""
    if module_name not in module_host.modules:
        raise HTTPException(status_code=404, detail="Module not found")

    module = module_host.modules[module_name]
    return {
        "module": module_name,
        "status": "ok" if module.loaded else "error",
        "version": module.version,
        "commands": len(module.get_command_handlers()),
        "events": len(module.get_event_handlers()),
        "web_tabs": len(module.get_web_tabs())
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8104)
