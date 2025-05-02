import asyncio
import logging
import logging.config
from aiogram import Bot, Dispatcher, types
import os
import sys
from dotenv import load_dotenv

from app.db.config import (
    get_session_maker,
)
from app.dependencies.logging_settings import logging_config
from app.middlewares.database import DataBaseSession, UserMiddleware
from app.handlers import user_router, admin_router

load_dotenv(dotenv_path="token.env")
BOT_TOKEN: str = os.getenv("SECRET_KEY") or ""
if not BOT_TOKEN:
    raise ValueError("Missing SECRET_KEY")


ALLOWED_UPDATES = ["message", "edited_message", "callback_query"]

logging.config.dictConfig(logging_config)
logger = logging.getLogger(__name__)

# Set SQLAlchemy engine logger to use the same formatter and level as the main project
sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
sqlalchemy_logger.setLevel(logging.INFO)
sqlalchemy_logger.handlers = [logging.StreamHandler(sys.stdout)]
sqlalchemy_logger.propagate = False

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(user_router)
dp.include_router(admin_router)


async def main() -> None:
    dp.update.middleware(DataBaseSession(session_maker=get_session_maker()))
    dp.update.middleware(UserMiddleware())
    await bot.delete_webhook(drop_pending_updates=True)
    # await bot.delete_my_commands(scope=types.BotCommandScopeAllPrivateChats())
    await bot.set_my_commands(
        commands=[
            types.BotCommand(command="help", description="Help"),
        ],
        scope=types.BotCommandScopeAllPrivateChats(),
    )
    await dp.start_polling(bot, allowed_updates=ALLOWED_UPDATES)


if __name__ == "__main__":
    logger.info("Starting bot...")
    asyncio.run(main())
