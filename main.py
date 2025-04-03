import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, types
import os
from dotenv import load_dotenv

from db.config import (
    get_session_maker,
)
from middlewares.database import DataBaseSession, UserMiddleware
from handlers.user_private import router as user_router


load_dotenv(dotenv_path="token.env")
BOT_TOKEN: str = os.getenv("SECRET_KEY") or ""
if not BOT_TOKEN:
    raise ValueError("Missing SECRET_KEY")


ALLOWED_UPDATES = ["message", "edited_message", "callback_query"]

logger = logging.getLogger(__name__)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
dp.include_router(user_router)


async def main() -> None:
    dp.update.middleware(DataBaseSession(session_pool=get_session_maker()))
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
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
