class BaseModule:
    name: str = "Module"
    version: str = "0.0.1"
    description: str = ""

    def __init__(self):
        self.logger = self._get_logger()

    def _get_logger(self):
        class L:
            def info(self, *a, **k): print(*a)
            def warning(self, *a, **k): print(*a)
            def error(self, *a, **k): print(*a)
        return L()

    async def on_load(self): ...
    async def on_unload(self): ...
