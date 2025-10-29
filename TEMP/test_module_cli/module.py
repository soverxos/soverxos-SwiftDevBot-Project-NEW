from Systems.sdk.base_module import BaseModule

class Module(BaseModule):
    async def on_load(self):
        print('✅ Модуль загружен: %s' % self.__class__.__name__)
