import asyncio
from sqlalchemy import select
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,

    FSInputFile
)

from dotenv import load_dotenv
import os

from config import get_engine, get_session
from models import User
from sqlalchemy.exc import (
    SQLAlchemyError, NoResultFound
)
load_dotenv(dotenv_path='token.env')
BOT_TOKEN = os.getenv("SECRET_KEY")

engine = get_engine()
Session = get_session(engine)
session = Session()


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    router = dp.include_router(Router())

    admins = ["aoi_dev", "mimfort"]
    def get_keyboard(username, admins):
        buttons = [
            [
                InlineKeyboardButton(text=str("регистрация"), callback_data=str("cmd:start")),
                InlineKeyboardButton(text=str("помощь"), callback_data=str("cmd:help")),
                InlineKeyboardButton(text=str("Ви админ!"), callback_data=str("cmd:admin")) if username in admins else InlineKeyboardButton(text=str("Ви не админ"), callback_data=str("cmd:not_admin"))
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @router.message(Command("buttons"))
    async def send_buttons(message: Message):
        await message.answer(
            "Choose an action:",
            reply_markup=get_keyboard(message.chat.username, admins)
        )

    # @router.message(Command("info"))
    # async def send_info(message: Message):
    #     print(dir(message))
    #     print(message.__dict__)
    #     print(message.__repr__())

    @router.message(Command("start"))
    async def init_dialog(message: Message):
        from typing import NamedTuple

        stmt = select(User).where(
            User.chat_id == message.chat.id and
            User.username == message.chat.username
        )

        result = session.execute(stmt).scalars().all()
        if not len(result):
            session.add(User(chat_id=message.chat.id, username=message.chat.username, first_name=message.chat.first_name))
            session.commit()
            await message.answer(
                f"Охайо!🖖 {message.chat.username}"
            ) 
        else: 
            await message.answer(
                f"Вы уже прошли регистрацию!"
            ) 
    @router.message(Command("help"))
    async def send_help(message: Message):
        await message.answer(
            "Скачать nekoray, nekobox: https://matsuridayo.github.io/"
        )

        await message.answer_photo(
            photo=FSInputFile(path='img.png'),
            caption="добавить "
        )

    @router.callback_query(F.data.startswith("cmd:"))
    async def button_pressed(callback: CallbackQuery):
        command = callback.data.split(":")[1]

        if command == "help":
            await send_help(callback.message)¤

        await callback.message.answer(f"Triggered /{command}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

