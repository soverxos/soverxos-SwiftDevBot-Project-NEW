from Systems.sdk.base_module import BaseModule
class Welcome(BaseModule):
    async def on_load(self):
        self.logger.info('🧩 welcome module loaded')
