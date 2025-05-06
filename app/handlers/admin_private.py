import logging
from aiogram import F, Router, types
from sqlalchemy.ext.asyncio import AsyncSession
from typing import cast

from app.db.models import User
from app.db.repository import ConnectionRepository, UserRepository
from app.dependencies.auth import get_admins_list
from app.kbds.menu_markups import (
    AdminAction,
    AdminActionData,
    UserAction,
    UserActionData,
    get_admin_actions_markup,
    get_admin_user_connections_markup,
    get_admin_userlist_markup,
)
from app.login_client import get_async_client
from app.schemas import ClientStats


admins: tuple[str, ...] = get_admins_list()
logger = logging.getLogger(__name__)


router = Router()


async def _check_message_accessible(query: types.CallbackQuery) -> types.Message | None:
    """
    Проверяет доступность сообщения для обработки.

    Args:
        query: Callback query от пользователя

    Returns:
        types.Message | None: Сообщение если оно доступно, иначе None
    """
    if not query.message:
        await query.answer("❌ Ошибка: сообщение недоступно")
        return None
    return cast(types.Message, query.message)


@router.callback_query(UserActionData.filter(F.action == UserAction.adminmarkup))
async def send_admin_actions(
    query: types.CallbackQuery,
    callback_data: UserActionData,
    user: User | None,
    session: AsyncSession,
) -> None:
    """
    Обработка действий администратора.

    Args:
        query: Callback query от пользователя
        callback_data: Данные из callback
        user: Текущий пользователь
        session: Сессия базы данных
    """
    logger.info("Пользователь %s запросил админ-панель", query.from_user.username)

    if not user or not user.admin:
        await query.answer("❌ Недостаточно прав")
        logger.warning(
            "Попытка доступа к админ-панели без прав: %s", query.from_user.username
        )
        return

    message = await _check_message_accessible(query)
    if message is None:
        return

    await message.answer(
        "Панель администратора:",
        reply_markup=get_admin_actions_markup(
            chat_id=query.from_user.id,
            user_id=user.id,
        ),
    )


@router.callback_query(AdminActionData.filter(F.action == AdminAction.userlist))
async def send_users_list(
    query: types.CallbackQuery,
    callback_data: AdminActionData,
    user: User | None,
    session: AsyncSession,
) -> None:
    """
    Отправляет список пользователей администратору.

    Args:
        query: Callback query от пользователя
        callback_data: Данные из callback
        user: Текущий пользователь
        session: Сессия базы данных
    """
    logger.info(
        "Администратор %s запросил список пользователей", query.from_user.username
    )

    if not user or not user.admin:
        await query.answer("❌ Недостаточно прав")
        logger.warning(
            "Попытка просмотра списка пользователей без прав: %s",
            query.from_user.username,
        )
        return

    users = await UserRepository(session).get_all()
    if not users:
        await query.answer("❗️ Пользователи не найдены")
        logger.warning("Список пользователей пуст")
        return

    message = await _check_message_accessible(query)
    if message is None:
        return

    await message.answer(
        "Список пользователей:",
        reply_markup=get_admin_userlist_markup(
            chat_id=query.from_user.id,
            user_id=user.id,
            users=users,
        ),
    )


@router.callback_query(AdminActionData.filter(F.action == AdminAction.userconn))
async def send_user_connections(
    query: types.CallbackQuery,
    callback_data: AdminActionData,
    user: User | None,
    session: AsyncSession,
) -> None:
    """
    Отправляет список подключений выбранного пользователя.

    Args:
        query: Callback query от администратора
        callback_data: Данные из callback
        user: Текущий пользователь (администратор)
        session: Сессия базы данных
    """
    logger.info(
        "Администратор %s запросил подключения пользователя ID=%s",
        query.from_user.username,
        callback_data.user_id,
    )

    if not user or not user.admin:
        await query.answer("❌ Недостаточно прав")
        logger.warning(
            "Попытка просмотра подключений пользователя без прав: %s",
            query.from_user.username,
        )
        return

    connections = await ConnectionRepository(session).get_by_user_id(
        user_id=callback_data.user_id, show_deleted=True
    )
    if not connections:
        await query.answer("❗️ Подключения не найдены")
        logger.warning(
            "Подключения не найдены для пользователя ID=%s", callback_data.user_id
        )
        return

    message = await _check_message_accessible(query)
    if message is None:
        return

    await message.answer(
        "Подключения пользователя:",
        reply_markup=get_admin_user_connections_markup(
            chat_id=query.from_user.id,
            user_id=callback_data.user_id,
            connections=connections,
        ),
    )


@router.callback_query(AdminActionData.filter(F.action == AdminAction.connstat))
async def send_connection_stats(
    query: types.CallbackQuery,
    callback_data: AdminActionData,
    user: User | None,
    session: AsyncSession,
) -> None:
    """
    Отправляет статистику по выбранному подключению.

    Args:
        query: Callback query от администратора
        callback_data: Данные из callback
        user: Текущий пользователь (администратор)
        session: Сессия базы данных
    """
    logger.info(
        "Администратор %s запросил статистику подключения ID=%s",
        query.from_user.username,
        callback_data.connection_id,
    )

    if not user or not user.admin:
        await query.answer("❌ Недостаточно прав")
        logger.warning(
            "Попытка просмотра статистики подключения без прав: %s",
            query.from_user.username,
        )
        return

    if not callback_data.connection_id:
        await query.answer("❗️ ID подключения не указан")
        logger.error("ID подключения не предоставлен")
        return

    connection = await ConnectionRepository(session).get_by_id(
        callback_data.connection_id
    )
    if not connection:
        await query.answer("❗️ Подключение не найдено")
        logger.error("Подключение не найдено в БД")
        return

    try:
        api_client = get_async_client()
        api_connection = await api_client.get_connection(uuid=connection.uuid)
        if not api_connection:
            await query.answer("❗️ Подключение не найдено в API")
            logger.warning("Подключение не найдено в API (uuid: %s)", connection.uuid)
            return

        stats = await api_client.get_stats()
        if not isinstance(stats, ClientStats):
            await query.answer("❗️ Не удалось получить статистику")
            logger.error("Ошибка получения статистики из API")
            return

        message = await _check_message_accessible(query)
        if message is None:
            return

        # Форматируем даты
        created_at = connection.created_at.strftime("%Y-%m-%d %H:%M:%S")
        expired_at = connection.expired_at.strftime("%Y-%m-%d %H:%M:%S")

        await message.answer(
            f"📊 Статистика подключения:\n\n"
            f"Email: {connection.email}\n"
            f"Создано: {created_at}\n"
            f"Истекает: {expired_at}\n"
            f"Всего загружено: {stats.down / 1024 / 1024:.2f} MB\n"
            f"Всего отправлено: {stats.up / 1024 / 1024:.2f} MB\n"
            f"Общий трафик: {(stats.up + stats.down) / 1024 / 1024:.2f} MB",
            reply_markup=get_admin_user_connections_markup(
                chat_id=query.from_user.id,
                user_id=callback_data.user_id,
                connections=[connection],
            ),
        )
    except Exception as e:
        error_msg = f"Ошибка при получении статистики: {str(e)}"
        logger.error(error_msg, exc_info=True)
        await query.answer("❌ Произошла ошибка при получении статистики")
