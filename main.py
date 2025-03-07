import asyncio
from sqlalchemy import select
from sqlalchemy.orm import Session
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, FSInputFile
from typing import Callable, Awaitable
import os
from dotenv import load_dotenv

from config import get_engine, get_session
from models import User
from menu_markups import get_user_actions_markup, get_admin_actions_markup

load_dotenv(dotenv_path="token.env")
BOT_TOKEN: str = os.getenv("SECRET_KEY") or ""
if not BOT_TOKEN:
    raise ValueError("Missing SECRET_KEY")

admins: tuple[str, ...] = ("aoi_dev", "mimfort")


async def main(session: Session) -> None:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    router = dp.include_router(Router())

    # Specify the correct types for callback handler functions.
    def register_callback(
        action: str, handler: Callable[[CallbackQuery], Awaitable[None]]
    ) -> None:
        async def wrapper(query: CallbackQuery) -> None:
            print(f"Handling action: {action}")
            await handler(query)

        router.callback_query.register(wrapper, F.data == action)

    def is_user_registered(message: Message) -> bool:
        stmt = select(User).where(User.chat_id == message.chat.id)
        result = session.execute(stmt).scalars().all()
        return bool(result)

    @router.message(Command("help"))
    async def send_basic_actions(message: Message) -> None:
        await message.answer(
            "Choose an action:",
            reply_markup=get_user_actions_markup(message.chat.username or "", admins),
        )

    @router.message(Command("admin"))
    async def send_admin_actions(message: Message) -> None:
        if message.chat.username in admins:
            await message.answer(
                text="админские действия", reply_markup=get_admin_actions_markup()
            )
        else:
            await message.answer("У вас нет права доступа.")

    @router.message(Command("register"))
    async def send_register(message: Message) -> None:
        if not is_user_registered(message):
            session.add(
                User(
                    chat_id=message.chat.id,
                    username=message.chat.username,
                    first_name=message.chat.first_name,
                )
            )
            session.commit()
            await message.answer(f"Охайо, {message.chat.username}!🖖")
        else:
            await message.answer("Вы уже прошли регистрацию!")

    @router.message(Command("settingup"))
    async def send_setting_up_vpn_connection(message: Message) -> None:
        await message.answer("Скачать nekoray, nekobox: https://matsuridayo.github.io/")
        await message.answer_photo(photo=FSInputFile(path="img.png"), caption="")

    from aiogram.exceptions import TelegramBadRequest

    @router.errors()
    async def handle_errors(exception: Exception) -> None:
        if isinstance(exception, TelegramBadRequest):
            print("Bad request: %s" % exception)
        else:
            print("Unhandled exception:", exception)

    register_callback("register", lambda q: send_register(q.message))
    register_callback("settingup", lambda q: send_setting_up_vpn_connection(q.message))
    register_callback("adminmarkup", lambda q: send_admin_actions(q.message))

    await dp.start_polling(bot)


if __name__ == "__main__":
    engine = get_engine()
    SessionLocal = get_session(engine)
    session = SessionLocal()
    asyncio.run(main(session))
