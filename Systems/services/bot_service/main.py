import os, asyncio, sys
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from dotenv import load_dotenv

# Добавляем корневую директорию в путь для импорта Systems
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
from Systems.core.logging.logger import logger
from Systems.core.database.engine import get_async_session
from Systems.core.database.models import User

load_dotenv()

SUPERADMIN_ID = int(os.getenv("SDB_SUPERADMIN_ID","0"))
ADMIN_IDS = [int(i) for i in os.getenv("SDB_ADMIN_IDS","").split(",") if i.strip()]

def is_admin(uid: int) -> bool:
    return uid == SUPERADMIN_ID or uid in ADMIN_IDS


async def save_or_update_user(telegram_user: types.User) -> User:
    """Сохранить или обновить информацию о пользователе в БД"""
    from datetime import datetime

    async with get_async_session() as session:
        # Ищем существующего пользователя по telegram_id
        from sqlalchemy import select
        stmt = select(User).where(User.telegram_id == telegram_user.id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        current_time = datetime.now()

        if user:
            # Обновляем существующего пользователя
            user.username = telegram_user.username
            user.first_name = telegram_user.first_name
            user.last_name = telegram_user.last_name
            user.language_code = telegram_user.language_code
            user.last_activity = current_time
            user.is_superadmin = (telegram_user.id == SUPERADMIN_ID)
            user.is_admin = is_admin(telegram_user.id)
            logger.debug(f"Updated user {telegram_user.id} in database")
        else:
            # Создаем нового пользователя
            user = User(
                telegram_id=telegram_user.id,
                username=telegram_user.username,
                first_name=telegram_user.first_name,
                last_name=telegram_user.last_name,
                language_code=telegram_user.language_code,
                last_activity=current_time,
                is_superadmin=(telegram_user.id == SUPERADMIN_ID),
                is_admin=is_admin(telegram_user.id)
            )
            session.add(user)
            logger.info(f"Created new user {telegram_user.id} ({telegram_user.username}) in database")

        await session.commit()
        await session.refresh(user)
        return user

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
        # Сохраняем информацию о пользователе
        user = await save_or_update_user(m.from_user)

        logger.info(f"User {m.from_user.id} ({m.from_user.username}) sent /start")
        await m.answer("Привет! Я — SwiftDevBot 🧠 (skeleton)")

    @dp.message(Command("admin"))
    async def cmd_admin(m: types.Message):
        # Сохраняем информацию о пользователе
        user = await save_or_update_user(m.from_user)

        if not is_admin(m.from_user.id):
            logger.warning(f"User {m.from_user.id} attempted /admin without permissions")
            await m.answer("⛔ Нет доступа.")
            return
        logger.info(f"Admin {m.from_user.id} accessed /admin")
        await m.answer("✅ Привет, админ! Команды: /admin, /ping")

    @dp.message(Command("ping"))
    async def cmd_ping(m: types.Message):
        # Сохраняем информацию о пользователе
        user = await save_or_update_user(m.from_user)

        logger.debug(f"User {m.from_user.id} sent /ping")
        await m.answer("pong")

    # Обработчик для всех текстовых сообщений (сохраняем пользователей)
    @dp.message()
    async def handle_all_messages(m: types.Message):
        # Сохраняем информацию о пользователе для всех взаимодействий
        user = await save_or_update_user(m.from_user)

    logger.info("✅ bot_service started, polling Telegram...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(run())
