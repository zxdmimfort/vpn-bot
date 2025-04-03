from enum import Enum
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Tuple

from aiogram.utils.keyboard import InlineKeyboardBuilder


class Action(str, Enum):
    register = "register"
    settingup = "settingup"
    adminmarkup = "adminmarkup"
    addcon = "addcon"
    conlist = "conlist"


class UserAction(CallbackData, prefix="user"):  # type: ignore
    """A callback data class for handling user-related actions.

    This class extends CallbackData and is used to structure callback data
    for user-related operations in the bot's menu system.

    Attributes:
        action (Action): The type of action to be performed.
        chat_id (int): The ID of the chat where the action is taking place.
        user_id (int | None): The ID of the target user, if applicable. # type: ignore
    """

    action: Action
    chat_id: int
    user_id: int | None


def get_user_actions_markup(
    username: str,
    admins: Tuple[str, ...],
    chat_id: int,
    user_id: int | None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if user_id is None:
        builder.row(
            InlineKeyboardButton(
                text=str("Регистрация"),
                callback_data=UserAction(
                    action=Action.register, chat_id=chat_id, user_id=user_id
                ).pack(),
            )
        )
    builder.add(
        InlineKeyboardButton(
            text=str("Установка подключения"), callback_data="settingup"
        ),
        InlineKeyboardButton(
            text=str("Список моих подключений"), callback_data="conlist"
        ),
        InlineKeyboardButton(
            text=str("Добавить новое подключение"), callback_data="addcon"
        ),
    )
    if username in admins:
        builder.add(
            InlineKeyboardButton(text=str("Админка"), callback_data="adminmarkup")
        )

    return builder.as_markup()


def get_admin_actions_markup() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text=str("список подключений"), callback_data="conlist"),
        InlineKeyboardButton(text=str("добавить подключение"), callback_data="addcon"),
    )
    return builder.as_markup()
