from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Tuple

from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_user_actions_markup(
    username: str, admins: Tuple[str, ...]
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text=str("регистрация"), callback_data="register"),
        InlineKeyboardButton(
            text=str("установка подключения"), callback_data="settingup"
        ),
    )
    if username in admins:
        builder.add(
            InlineKeyboardButton(text=str("(Ви админ!)"), callback_data="adminmarkup")
        )

    return builder.as_markup()


def get_admin_actions_markup() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text=str("список подключений"), callback_data="conlist"),
        InlineKeyboardButton(text=str("добавить подключение"), callback_data="addcon"),
    )
    return builder.as_markup()
