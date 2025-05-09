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


# Тут не получается избавиться от ошибки mypy
class UserActionData(CallbackData, prefix="user"):  # type: ignore[call-arg]
    """Класс данных обратного вызова для обработки действий пользователя.

    Этот класс расширяет CallbackData и используется для структурирования данных
    обратного вызова для пользовательских операций в системе меню бота.

    Атрибуты:
        action (Action): Тип выполняемого действия.
        chat_id (int): ID чата, где происходит действие.
        user_id (int | None): ID целевого пользователя, если применимо.
        connection_id (int | None): ID подключения, если применимо.
        absolute_delete (bool): Флаг, указывающий на полное удаление подключения из базы данных.
        back_string (UserAction | None): Действие для возврата после завершения текущего действия.
    """

    action: UserAction
    chat_id: int
    user_id: int | None = None
    connection_id: int | None = None
    absolute_delete: bool = False


class AdminAction(str, Enum):
    """Перечисление действий администратора для системы меню бота."""

    userlist = "userlist"
    userconn = "userconn"
    requests = "requests"
    connstat = "connstat"
    opuser = "opuser"
    deleteuser = "deleteuser"


# Тут не получается избавиться от ошибки mypy
class AdminActionData(CallbackData, prefix="admin"):  # type: ignore[call-arg]
    """Класс данных обратного вызова для обработки действий администратора.

    Этот класс расширяет CallbackData и используется для структурирования данных
    обратного вызова для операций администратора в системе меню бота.

    Атрибуты:
        action (AdminAction): Тип выполняемого действия.
        chat_id (int): ID чата, где происходит действие.
        user_id (int): ID целевого пользователя.
        connection_id (int | None): ID подключения, если применимо.
    """

    action: AdminAction
    chat_id: int
    user_id: int
    connection_id: int | None = None


def create_back_button(
    callback_data: CallbackData,
) -> InlineKeyboardButton:
    """Создает кнопку "Назад" с заданными данными обратного вызова."""
    button = InlineKeyboardButton(
        text=str("Назад"),
        callback_data=callback_data.pack(),
    )
    return button


def get_user_actions_markup(
    username: str,
    admins: Tuple[str, ...],
    chat_id: int,
    user_id: int | None,
    is_admin: bool = False,
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
                ).pack(),
            ),
            InlineKeyboardButton(
                text=str("Добавить новое подключение"),
                callback_data=UserActionData(
                    action=UserAction.addcon,
                    chat_id=chat_id,
                    user_id=user_id,
                ).pack(),
            ),
            InlineKeyboardButton(
                text=str("Установка подключения"),
                callback_data=UserActionData(
                    action=UserAction.settingup,
                    chat_id=chat_id,
                    user_id=user_id,
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
    back_button: InlineKeyboardButton,
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
    builder.add(back_button)
    builder.adjust(2)
    return builder.as_markup()


def get_view_connection_markup(
    chat_id: int,
    user_id: int,
    connection_id: int,
    back_button: InlineKeyboardMarkup,
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
    builder.add(back_button)
    builder.adjust(2)
    return builder.as_markup()


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
                text=f"{'❌' if not connection.exists_in_api else '✅'} {connection.email}",
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
