from enum import Enum
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Sequence, Tuple

from aiogram.utils.keyboard import InlineKeyboardBuilder

from db.models import Connection


class UserAction(str, Enum):
    register = "register"
    settingup = "settingup"
    adminmarkup = "adminmarkup"
    addcon = "addcon"
    conlist = "conlist"


class UserActionData(CallbackData, prefix="user"):  # type: ignore
    """A callback data class for handling user-related actions.

    This class extends CallbackData and is used to structure callback data
    for user-related operations in the bot's menu system.

    Attributes:
        action (Action): The type of action to be performed.
        chat_id (int): The ID of the chat where the action is taking place.
        user_id (int | None): The ID of the target user, if applicable. # type: ignore
    """

    action: UserAction
    chat_id: int
    user_id: int | None = None
    connection_id: int | None = None


def get_user_actions_markup(
    username: str,
    admins: Tuple[str, ...],
    chat_id: int,
    user_id: int | None,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if user_id is None:
        builder.add(
            InlineKeyboardButton(
                text=str("Регистрация"),
                callback_data=UserActionData(
                    action=UserAction.register, chat_id=chat_id, user_id=user_id
                ).pack(),
            )
        )
    else:
        builder.add(
            InlineKeyboardButton(
                text=str("Список моих подключений"),
                callback_data=UserActionData(
                    action=UserAction.conlist, chat_id=chat_id, user_id=user_id
                ).pack(),
            ),
            InlineKeyboardButton(
                text=str("Добавить новое подключение"),
                callback_data=UserActionData(
                    action=UserAction.addcon, chat_id=chat_id, user_id=user_id
                ).pack(),
            ),
            InlineKeyboardButton(
                text=str("Установка подключения"),
                callback_data=UserActionData(
                    action=UserAction.settingup, chat_id=chat_id, user_id=user_id
                ).pack(),
            ),
        )
    if username in admins:
        builder.add(
            InlineKeyboardButton(text=str("Админка"), callback_data="adminmarkup")
        )
    builder.adjust(2)
    return builder.as_markup()


def get_my_connections_markup(
    chat_id: int,
    user_id: int,
    connections: Sequence[Connection],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, connection in enumerate(connections, 1):
        builder.add(
            InlineKeyboardButton(
                text=f"{i}) - {connection.email}",
                callback_data=AdminActionData(
                    action=AdminAction.requests,
                    chat_id=chat_id,
                    user_id=user_id,
                    connection_id=connection.id,
                ).pack(),
            )
        )
    builder.adjust(2)
    return builder.as_markup()


class AdminAction(str, Enum):
    """An enumeration of admin actions for the bot's menu system."""

    userlist = "userlist"
    requests = "requests"
    userstat = "userstat"


class AdminActionData(CallbackData, prefix="admin"):  # type: ignore
    """A callback data class for handling admin-related actions.

    This class extends CallbackData and is used to structure callback data
    for admin-related operations in the bot's menu system.

    Attributes:
        action (AdminAction): The type of action to be performed.
        chat_id (int): The ID of the chat where the action is taking place.
        user_id (int | None): The ID of the target user, if applicable. # type: ignore
    """

    action: AdminAction
    chat_id: int
    user_id: int


def get_admin_actions_markup(
    chat_id: int,
    user_id: int,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=str("Пользователи"),
            callback_data=AdminActionData(
                action=AdminAction.userlist, chat_id=chat_id, user_id=user_id
            ).pack(),
        ),
        InlineKeyboardButton(
            text=str("Запросы"),
            callback_data=AdminActionData(
                action=AdminAction.requests, chat_id=chat_id, user_id=user_id
            ).pack(),
        ),
    )
    builder.adjust(2)
    return builder.as_markup()
