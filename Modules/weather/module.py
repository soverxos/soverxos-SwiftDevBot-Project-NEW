from Systems.sdk.base_module import BaseModule
class Weather(BaseModule):
    async def on_load(self):
        self.logger.info('🧩 weather module loaded')
