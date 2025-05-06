from enum import Enum
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import Sequence, Tuple

from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.db.models import Connection, User


class UserAction(str, Enum):
    register = "register"
    op = "op"
    settingup = "settingup"
    addcon = "addcon"
    conlist = "conlist"
    adminmarkup = "adminmarkup"
    viewcon = "viewcon"
    deletecon = "deletecon"
    startbutton = "startbutton"


@CallbackData.prefix("user")
class UserActionData(CallbackData):
    """A callback data class for handling user-related actions.

    This class extends CallbackData and is used to structure callback data
    for user-related operations in the bot's menu system.

    Attributes:
        action (Action): The type of action to be performed.
        chat_id (int): The ID of the chat where the action is taking place.
        user_id (int | None): The ID of the target user, if applicable.
        connection_id (int | None): The ID of the target connection, if applicable.
        absolute_delete (bool): Flag to indicate if the connection should be deleted completely from database.
        back_string (UserAction | None): The action to return to after the current action is completed.
    """

    action: UserAction
    chat_id: int
    user_id: int | None = None
    connection_id: int | None = None
    absolute_delete: bool = False
    back_string: UserAction | None = None


def get_user_actions_markup(
    username: str,
    admins: Tuple[str, ...],
    chat_id: int,
    user_id: int | None,
    is_admin: bool = False,
    back_string: UserAction | None = None,
) -> InlineKeyboardMarkup:
    """Buttons for startbutton"""
    builder = InlineKeyboardBuilder()
    if user_id is None:
        builder.add(
            InlineKeyboardButton(
                text=str("Регистрация"),
                callback_data=UserActionData(
                    action=UserAction.register,
                    chat_id=chat_id,
                    user_id=user_id,
                    back_string=UserAction.startbutton,
                ).pack(),
            )
        )
    else:
        builder.add(
            InlineKeyboardButton(
                text=str("Список моих подключений"),
                callback_data=UserActionData(
                    action=UserAction.conlist,
                    chat_id=chat_id,
                    user_id=user_id,
                    back_string=UserAction.startbutton,
                ).pack(),
            ),
            InlineKeyboardButton(
                text=str("Добавить новое подключение"),
                callback_data=UserActionData(
                    action=UserAction.addcon,
                    chat_id=chat_id,
                    user_id=user_id,
                    back_string=UserAction.startbutton,
                ).pack(),
            ),
            InlineKeyboardButton(
                text=str("Установка подключения"),
                callback_data=UserActionData(
                    action=UserAction.settingup,
                    chat_id=chat_id,
                    user_id=user_id,
                    back_string=UserAction.startbutton,
                ).pack(),
            ),
        )
    if username in admins or is_admin:
        builder.add(
            InlineKeyboardButton(
                text=str("Админка"),
                callback_data=UserActionData(
                    action=UserAction.adminmarkup,
                    chat_id=chat_id,
                    user_id=user_id,
                    back_string=UserAction.startbutton,
                ).pack(),
            )
        )

    builder.adjust(2)
    return builder.as_markup()


def get_my_connections_markup(
    chat_id: int,
    user_id: int,
    connections: Sequence[Connection],
    back_string: UserAction,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, connection in enumerate(connections, 1):
        builder.add(
            InlineKeyboardButton(
                text=f"{'❌' if not connection.exists_in_api else '✅'} {connection.email}",
                callback_data=UserActionData(
                    action=UserAction.viewcon,
                    chat_id=chat_id,
                    user_id=user_id,
                    connection_id=connection.id,
                    back_string=UserAction.conlist,
                ).pack(),
            )
        )
    builder.add(
        InlineKeyboardButton(
            text=str("Назад"),
            callback_data=UserActionData(
                action=back_string,
                chat_id=chat_id,
                user_id=user_id,
            ).pack(),
        )
    )
    builder.adjust(2)
    return builder.as_markup()


def get_view_connection_markup(
    chat_id: int,
    user_id: int,
    connection_id: int,
    back_string: UserAction,
    is_admin: bool = False,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=str("Удалить подключение"),
            callback_data=UserActionData(
                action=UserAction.deletecon,
                chat_id=chat_id,
                user_id=user_id,
                connection_id=connection_id,
                back_string=UserAction.conlist,
            ).pack(),
        )
    )
    if is_admin:
        builder.add(
            InlineKeyboardButton(
                text=str("Полностью удалить подключение"),
                callback_data=UserActionData(
                    action=UserAction.deletecon,
                    chat_id=chat_id,
                    user_id=user_id,
                    connection_id=connection_id,
                    absolute_delete=True,
                    back_string=UserAction.conlist,
                ).pack(),
            )
        )
    builder.add(
        InlineKeyboardButton(
            text=str("Назад"),
            callback_data=UserActionData(
                action=back_string, chat_id=chat_id, user_id=user_id
            ).pack(),
        )
    )
    builder.adjust(2)
    return builder.as_markup()


class AdminAction(str, Enum):
    """An enumeration of admin actions for the bot's menu system."""

    userlist = "userlist"
    userconn = "userconn"
    requests = "requests"
    connstat = "connstat"
    opuser = "opuser"
    deleteuser = "deleteuser"


@CallbackData.prefix("admin")
class AdminActionData(CallbackData):
    """A callback data class for handling admin-related actions.

    This class extends CallbackData and is used to structure callback data
    for admin-related operations in the bot's menu system.

    Attributes:
        action (AdminAction): The type of action to be performed.
        chat_id (int): The ID of the chat where the action is taking place.
        user_id (int): The ID of the target user.
        connection_id (int | None): The ID of the connection, if applicable.
    """

    action: AdminAction
    chat_id: int
    user_id: int
    connection_id: int | None = None


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


def get_admin_userlist_markup(
    chat_id: int,
    user_id: int,
    users: list[User],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, user in enumerate(users, 1):
        builder.add(
            InlineKeyboardButton(
                text=f"{user.username}",
                callback_data=AdminActionData(
                    action=AdminAction.userconn,
                    chat_id=chat_id,
                    user_id=user.id,
                ).pack(),
            )
        )
    builder.add(
        InlineKeyboardButton(
            text=str("Назад"),
            callback_data=UserActionData(
                action=UserAction.adminmarkup, chat_id=chat_id, user_id=user_id
            ).pack(),
        )
    )
    builder.adjust(2)
    return builder.as_markup()


def get_admin_user_connections_markup(
    chat_id: int,
    user_id: int,
    connections: list[Connection],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, connection in enumerate(connections, 1):
        builder.add(
            InlineKeyboardButton(
                text=f"{connection.email}",
                callback_data=AdminActionData(
                    action=AdminAction.connstat,
                    chat_id=chat_id,
                    user_id=user_id,
                    connection_id=connection.id,
                ).pack(),
            )
        )
    builder.add(
        InlineKeyboardButton(
            text=str("Назад"),
            callback_data=AdminActionData(
                action=AdminAction.userlist, chat_id=chat_id, user_id=user_id
            ).pack(),
        )
    )
    builder.adjust(2)
    return builder.as_markup()


def get_admin_user_actions_markup(
    chat_id: int,
    user_id: int,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text=str("Выдать админа пользователю"),
            callback_data=AdminActionData(
                action=AdminAction.userlist, chat_id=chat_id, user_id=user_id
            ).pack(),
        ),
    )
    builder.add(
        InlineKeyboardButton(
            text=str("Назад"),
            callback_data=AdminActionData(
                action=AdminAction.userlist, chat_id=chat_id, user_id=user_id
            ).pack(),
        ),
    )
    builder.adjust(2)
    return builder.as_markup()
