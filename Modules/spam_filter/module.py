from Systems.sdk.base_module import BaseModule
class Spamfilter(BaseModule):
    async def on_load(self):
        self.logger.info('🧩 spam_filter module loaded')
