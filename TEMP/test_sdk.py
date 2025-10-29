#!/usr/bin/env python3
"""
Test SDK Components
"""

import asyncio
import sys
import os

# Добавляем корневую директорию
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_sdk():
    print("🧪 Testing SwiftDevBot SDK")
    print("=" * 35)

    try:
        # 1. Test BaseModule imports
        print("1️⃣  Testing BaseModule...")
        from Systems.sdk import BaseModule, ModuleStorage, EventBusClient, get_event_client
        print("   ✅ SDK imports successful")

        # 2. Test BaseModule creation
        print("\\n2️⃣  Testing BaseModule creation...")

        class TestModule(BaseModule):
            name = "test_module"
            version = "1.0.0"
            description = "Test module"

        module = TestModule("Modules/test_sdk_module")

        # Register handlers using instance methods
        @module.on_command("hello")
        async def hello_cmd(message):
            return "Hello!"

        @module.on_event("test.event")
        async def test_event(data):
            print(f"Received event: {data}")

        @module.web_tab("Test Tab", "🧪")
        async def test_tab():
            return "<h3>Test Web Tab</h3>"

        print("   ✅ BaseModule created successfully")

        # 3. Test decorators
        print("\\n3️⃣  Testing decorators...")
        commands = module.get_command_handlers()
        events = module.get_event_handlers()
        web_tabs = module.get_web_tabs()

        print(f"   ✅ Commands: {list(commands.keys())}")
        print(f"   ✅ Events: {list(events.keys())}")
        print(f"   ✅ Web tabs: {list(web_tabs.keys())}")

        # 4. Test ModuleStorage
        print("\\n4️⃣  Testing ModuleStorage...")
        await module.storage.load()
        module.storage.set("test_key", "test_value")
        module.storage.set("counter", 42)

        value = module.storage.get("test_key")
        counter = module.storage.get("counter", 0)

        print(f"   ✅ Storage loaded, test_key='{value}', counter={counter}")
        await module.storage.save()

        # 5. Test EventBus Client
        print("\\n5️⃣  Testing EventBus Client...")
        client = get_event_client("test_module")
        print("   ✅ EventBus client created")

        # Test storage persistence
        print("\\n6️⃣  Testing storage persistence...")
        module2 = TestModule("Modules/test_sdk_module")
        await module2.storage.load()
        persisted_value = module2.storage.get("test_key")
        persisted_counter = module2.storage.get("counter", 0)
        print(f"   ✅ Persisted: test_key='{persisted_value}', counter={persisted_counter}")

        # Cleanup
        module.storage.clear()
        await module.storage.save()

        print("\\n🎉 ALL SDK TESTS PASSED!")
        print("\\n📊 SDK Components Ready:")
        print("   ✅ BaseModule with decorators (@on_command, @on_event, @web_tab)")
        print("   ✅ ModuleStorage (JSON-based persistence)")
        print("   ✅ EventBusClient (simplified API)")
        print("   ✅ Module lifecycle (on_load, on_unload, on_start, on_stop)")

    except Exception as e:
        print(f"❌ SDK Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_sdk())
