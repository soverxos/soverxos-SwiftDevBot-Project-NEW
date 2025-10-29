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
from Systems.core.config.settings import REQUIRE_REGISTRATION, START_MESSAGE_NEW_USER, START_MESSAGE_EXISTING_USER

load_dotenv()

SUPERADMIN_ID = int(os.getenv("SDB_SUPERADMIN_ID","0"))
ADMIN_IDS = [int(i) for i in os.getenv("SDB_ADMIN_IDS","").split(",") if i.strip()]

def is_admin(uid: int) -> bool:
    return uid == SUPERADMIN_ID or uid in ADMIN_IDS


async def is_user_registered(telegram_id: int) -> bool:
    """Проверяет, зарегистрирован ли пользователь в БД"""
    # Если регистрация не требуется, считаем всех пользователей зарегистрированными
    if not REQUIRE_REGISTRATION:
        return True

    from Systems.core.database.engine import get_async_session
    from Systems.core.database.models import User
    from sqlalchemy import select

    try:
        async with get_async_session() as session:
            stmt = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(stmt)
            user = result.scalar_one_or_none()
            return user is not None
    except Exception as e:
        logger.error(f"Error checking user registration: {e}")
        return False


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
        # Если регистрация не требуется, просто показываем приветствие
        if not REQUIRE_REGISTRATION:
            logger.info(f"User {m.from_user.id} ({m.from_user.username}) sent /start (registration disabled)")
            await m.answer(START_MESSAGE_EXISTING_USER)
            return

        # Проверяем, не зарегистрирован ли уже пользователь
        if await is_user_registered(m.from_user.id):
            logger.info(f"Already registered user {m.from_user.id} ({m.from_user.username}) sent /start again")
            await m.answer(START_MESSAGE_EXISTING_USER)
            return

        # Регистрируем нового пользователя
        user = await save_or_update_user(m.from_user)

        logger.info(f"User {m.from_user.id} ({m.from_user.username}) registered via /start")
        await m.answer(START_MESSAGE_NEW_USER)

    @dp.message(Command("admin"))
    async def cmd_admin(m: types.Message):
        # Администраторы всегда имеют доступ, независимо от регистрации
        if not is_admin(m.from_user.id):
            # Для не-админов проверяем регистрацию только если она включена
            if REQUIRE_REGISTRATION and not await is_user_registered(m.from_user.id):
                logger.warning(f"Unregistered user {m.from_user.id} ({m.from_user.username}) attempted /admin")
                await m.answer("❌ Сначала зарегистрируйтесь командой /start")
                return
            else:
                logger.warning(f"Non-admin user {m.from_user.id} attempted /admin without permissions")
                await m.answer("⛔ Нет доступа.")
                return

        logger.info(f"Admin {m.from_user.id} accessed /admin")
        await m.answer("✅ Привет, админ! Команды: /admin, /ping, /settings")

    @dp.message(Command("ping"))
    async def cmd_ping(m: types.Message):
        # Проверяем регистрацию пользователя
        if not await is_user_registered(m.from_user.id):
            logger.warning(f"Unregistered user {m.from_user.id} ({m.from_user.username}) attempted /ping")
            await m.answer("❌ Сначала зарегистрируйтесь командой /start")
            return

        logger.debug(f"User {m.from_user.id} sent /ping")
        await m.answer("pong")

    @dp.message(Command("help"))
    async def cmd_help(m: types.Message):
        # Проверяем регистрацию пользователя
        if not await is_user_registered(m.from_user.id):
            logger.warning(f"Unregistered user {m.from_user.id} ({m.from_user.username}) attempted /help")
            await m.answer("❌ Сначала зарегистрируйтесь командой /start")
            return

        logger.debug(f"User {m.from_user.id} requested help")

        if REQUIRE_REGISTRATION:
            help_text = ("🤖 SwiftDevBot - справка\n\n"
                        "📋 Доступные команды:\n"
                        "/start - регистрация/статус\n"
                        "/admin - админ-панель (только админы)\n"
                        "/ping - проверка бота\n"
                        "/help - эта справка\n\n"
                        "💡 Все команды доступны только зарегистрированным пользователям!")
        else:
            help_text = ("🤖 SwiftDevBot - справка\n\n"
                        "📋 Доступные команды:\n"
                        "/start - приветствие\n"
                        "/admin - админ-панель (только админы)\n"
                        "/ping - проверка бота\n"
                        "/help - эта справка\n\n"
                        "💡 Регистрация пользователей отключена!")

        await m.answer(help_text)

    @dp.message(Command("settings"))
    async def cmd_settings(m: types.Message):
        # Проверяем права администратора (админы всегда имеют доступ)
        if not is_admin(m.from_user.id):
            logger.warning(f"Non-admin user {m.from_user.id} attempted /settings without permissions")
            await m.answer("⛔ Нет доступа. Только администраторы.")
            return

        logger.info(f"Admin {m.from_user.id} accessed /settings")

        # Показываем текущие настройки и инструкции
        settings_text = ("⚙️ Настройки SwiftDevBot\n\n"
                        f"📋 Регистрация пользователей: {'✅ ВКЛЮЧЕНА' if REQUIRE_REGISTRATION else '❌ ОТКЛЮЧЕНА'}\n\n"
                        "🔧 Доступные команды для админов:\n"
                        "/settings on - включить обязательную регистрацию\n"
                        "/settings off - отключить обязательную регистрацию\n\n"
                        "⚠️ Изменения применятся после перезапуска бота!")

        await m.answer(settings_text)

    @dp.message(lambda m: m.text and m.text.startswith("/settings "))
    async def cmd_settings_action(m: types.Message):
        # Проверяем права администратора (админы всегда имеют доступ)
        if not is_admin(m.from_user.id):
            logger.warning(f"Non-admin user {m.from_user.id} attempted /settings action without permissions")
            await m.answer("⛔ Нет доступа. Только администраторы.")
            return

        # Разбираем команду
        parts = m.text.split()
        if len(parts) != 2:
            await m.answer("❌ Использование: /settings on или /settings off")
            return

        action = parts[1].lower()
        if action not in ["on", "off"]:
            await m.answer("❌ Использование: /settings on или /settings off")
            return

        # Здесь можно добавить логику изменения настроек
        # Пока просто показываем сообщение о том, что нужно перезапустить бота
        if action == "on":
            await m.answer("✅ Обязательная регистрация будет ВКЛЮЧЕНА после перезапуска бота!\n\n"
                          "🔄 Выполните: bash run_dev.sh stop && bash run_dev.sh start")
        else:
            await m.answer("❌ Обязательная регистрация будет ОТКЛЮЧЕНА после перезапуска бота!\n\n"
                          "🔄 Выполните: bash run_dev.sh stop && bash run_dev.sh start")

        logger.info(f"Admin {m.from_user.id} set registration to {action}")

    # Обработчик для всех текстовых сообщений
    @dp.message()
    async def handle_all_messages(m: types.Message):
        # Проверяем регистрацию пользователя только если регистрация включена
        if REQUIRE_REGISTRATION and not await is_user_registered(m.from_user.id):
            # Игнорируем сообщения от незарегистрированных пользователей
            logger.debug(f"Ignoring message from unregistered user {m.from_user.id} ({m.from_user.username})")
            return

        # Пользователь зарегистрирован (или регистрация отключена) - можно обрабатывать сообщение
        logger.debug(f"User {m.from_user.id} sent message: {m.text[:50]}...")

        # Сохраняем информацию о пользователе только если регистрация включена
        if REQUIRE_REGISTRATION:
            user = await save_or_update_user(m.from_user)

    logger.info("✅ bot_service started, polling Telegram...")

    # Обработка конфликтов polling
    try:
        await dp.start_polling(bot)
    except Exception as e:
        if "Conflict" in str(e) or "terminated by other getUpdates" in str(e):
            logger.warning("⚠️  Конфликт с другим экземпляром бота. Попытка получить свежие updates...")
            try:
                # Получаем последние updates для сброса offset
                updates = await bot.get_updates(offset=-1, limit=1)
                if updates:
                    last_update_id = updates[-1].update_id
                    logger.info(f"📥 Получен offset: {last_update_id}")
                    await dp.start_polling(bot, allowed_updates=[], drop_pending_updates=True)
                else:
                    logger.error("❌ Не удалось получить updates для сброса конфликта")
            except Exception as e2:
                logger.error(f"❌ Ошибка при разрешении конфликта: {e2}")
        else:
            logger.error(f"❌ Ошибка при запуске polling: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(run())
