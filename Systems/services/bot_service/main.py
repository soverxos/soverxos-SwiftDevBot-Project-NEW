import os, asyncio, sys
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# Добавляем корневую директорию в путь для импорта Systems
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from Systems.core.logging.logger import logger

load_dotenv()

SUPERADMIN_ID = int(os.getenv("SDB_SUPERADMIN_ID","0"))
ADMIN_IDS = [int(i) for i in os.getenv("SDB_ADMIN_IDS","").split(",") if i.strip()]

def is_admin(uid: int) -> bool:
    return uid == SUPERADMIN_ID or uid in ADMIN_IDS

async def run():
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("❌ BOT_TOKEN not set in environment (.env)")
        return
    
    logger.info("🚀 Initializing bot_service...")
    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    @dp.message(Command("start"))
    async def cmd_start(m: types.Message):
        logger.info(f"User {m.from_user.id} sent /start")
        await m.answer("Привет! Я — SwiftDevBot 🧠 (skeleton)")

    @dp.message(Command("admin"))
    async def cmd_admin(m: types.Message):
        if not is_admin(m.from_user.id):
            logger.warning(f"User {m.from_user.id} attempted /admin without permissions")
            await m.answer("⛔ Нет доступа.")
            return
        logger.info(f"Admin {m.from_user.id} accessed /admin")
        await m.answer("✅ Привет, админ! Команды: /admin, /ping")

    @dp.message(Command("ping"))
    async def cmd_ping(m: types.Message):
        logger.debug(f"User {m.from_user.id} sent /ping")
        await m.answer("pong")

    logger.info("✅ bot_service started, polling Telegram...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(run())
