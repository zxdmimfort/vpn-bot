
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardButton


def get_user_actions_markup(username, admins):
    builder = InlineKeyboardBuilder()

    builder.add(
        InlineKeyboardButton(text=str("регистрация"), callback_data='register'),
        InlineKeyboardButton(text=str("установка подключения"), callback_data='settingup'),
    )
    if username in admins:
        builder.add(InlineKeyboardButton(text=str("(Ви админ!)"), callback_data='adminmarkup'))

    return builder.as_markup()

def get_admin_actions_markup():
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text=str("список подключений"), callback_data='conlist' ),
        InlineKeyboardButton(text=str("добавить подключение"), callback_data='addcon'),
    )
    return builder.as_markup()