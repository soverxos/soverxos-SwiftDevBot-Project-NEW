from Systems.sdk.base_module import BaseModule

class TemplateModule(BaseModule):
    name = "Template"
    version = "1.0.0"
    description = "Template user module"

    async def on_load(self):
        self.logger.info("🧩 TemplateModule loaded")
