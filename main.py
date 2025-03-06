import asyncio
import logging
from aiogram import Bot, Dispatcher, F, Router
from aiogram.filters import Command
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
)

# Configure logging
logging.basicConfig(level=logging.INFO)

BOT_TOKEN = "7539715541:AAE5LmZDb0ikVd3Xtia_st9miAD5OagBck8"


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    router = dp.include_router(Router())

    # Create a numeric keyboard
    def get_keyboard():
        buttons = [
            [
                InlineKeyboardButton(text=str("1"), callback_data=str("нажал")),
                InlineKeyboardButton(text=str("2"), callback_data=str("нажал")),
                InlineKeyboardButton(text=str("3"), callback_data=str("нажал")),
                InlineKeyboardButton(text=str("4"), callback_data=str("нажал")),
            ]
        ]
        return InlineKeyboardMarkup(inline_keyboard=buttons)

    @router.message(Command("buttons"))
    async def send_buttons(message: Message):
        await message.answer("Choose a number:", reply_markup=get_keyboard())

    @router.callback_query()
    async def button_pressed(callback: CallbackQuery):
        await callback.answer(f"You pressed {callback.data}")
        await callback.message.answer(f"Selected: {callback.data}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
