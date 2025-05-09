import logging
import datetime
from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart, or_f
from sqlalchemy.ext.asyncio import AsyncSession
from typing import cast

from app.db.repository import ConnectionRepository, UserRepository
from app.dependencies.auth import get_admins_list
from app.kbds.menu_markups import (
    UserAction,
    UserActionData,
    create_back_button,
    get_my_connections_markup,
    get_user_actions_markup,
    get_view_connection_markup,
)
from app.db.models import User
from app.login_client import get_async_client

router = Router()
admins: tuple[str, ...] = get_admins_list()
logger = logging.getLogger(__name__)


async def _check_message_accessible(query: types.CallbackQuery) -> types.Message | None:
    """
    Проверяет, доступно ли сообщение для обработки.

    Args:
        query: Callback query от пользователя

    Returns:
        Message | None: Объект Message если сообщение доступно, None в противном случае
    """
    if not query.message or isinstance(query.message, types.InaccessibleMessage):
        await query.answer("❌ Ошибка: сообщение недоступно")
        return None
    return cast(types.Message, query.message)


def _handle_start_action(
    chat: types.Chat,
    user: User | None,
) -> tuple[str, types.InlineKeyboardMarkup]:
    """
    Общая логика для обработки команд start/help.

    Аргументы:
        chat: Объект чата
        user: Пользователь из базы данных

    Возвращает:
        tuple: Текст сообщения и клавиатура для ответа
    """
    logger.info("Пользователь %s вызвал команду /start или /help", chat.username)

    markup = get_user_actions_markup(
        username=chat.username or "",
        admins=admins,
        chat_id=chat.id,
        user_id=user.id if user else None,
        is_admin=user.admin if user else False,
    )

    return "Выберите действие:", markup


@router.message(or_f(Command("help"), CommandStart()))
async def start_command(
    message: types.Message,
    user: User | None,
) -> None:
    """
    Обработка команд /start и /help через сообщение.

    Args:
        message: Входящее сообщение
        user: Пользователь из базы данных
    """
    text, markup = _handle_start_action(message.chat, user)
    await message.answer(text=text, reply_markup=markup)


@router.callback_query(UserActionData.filter(F.action == UserAction.startbutton))
async def start_callback(
    query: types.CallbackQuery,
    user: User | None,
) -> None:
    """
    Обработка callback query для кнопки старт.

    Args:
        query: Callback query
        user: Пользователь из базы данных
    """
    message = await _check_message_accessible(query)
    if not message:
        return

    await query.answer()
    text, markup = _handle_start_action(message.chat, user)
    await query.message.answer(text=text, reply_markup=markup)


@router.message(Command("op"))
async def op_me(
    message: types.Message,
    user: User | None,
    session: AsyncSession,
) -> None:
    """
    Op/deop if username exist in admin list.
    """
    logger.info("User %s triggered /op", message.chat.username)
    if not user:
        await message.answer("You need to register first!")
        logger.warning(
            "User %s tried to access /op without registration",
            message.chat.username,
        )
        return

    if message.chat.username in admins:
        user = await UserRepository(session).update(
            user,
            admin=not user.admin,
        )
    logger.info("User %s updated admin status to %s", message.chat.username, user.admin)
    await message.answer(f"OP successfully and your status: {user.admin}")


@router.callback_query(UserActionData.filter(F.action == UserAction.register))
async def send_register(
    query: types.CallbackQuery,
    callback_data: UserActionData,
    session: AsyncSession,
    user: User | None,
) -> None:
    """
    Register a user in the database.
    """
    logger.info("User %s triggered registration", query.from_user.username)
    if not user:
        user = await UserRepository(session).create(
            chat_id=query.from_user.id,
            username=query.from_user.username,
            first_name=query.from_user.first_name,
        )
        text = f"Охайо, {query.from_user.username}!🖖"
        logger.info("User %s registered successfully", query.from_user.username)
    else:
        text = "Вы уже прошли регистрацию!"
        logger.warning("User %s attempted to register again", query.from_user.username)

    await query.answer(text)

    message = await _check_message_accessible(query)
    if message is None:
        return

    await message.answer(
        text,
        reply_markup=get_user_actions_markup(
            query.from_user.username or "",
            admins,
            query.from_user.id,
            user_id=user.id if user else None,
        ),
    )


@router.callback_query(UserActionData.filter(F.action == UserAction.conlist))
async def get_connections(
    query: types.CallbackQuery,
    callback_data: UserActionData,
    session: AsyncSession,
    user: User | None,
) -> None:
    logger.info("User %s requested connections list", query.from_user.username)
    if not user:
        await query.answer("You need to register first!")
        logger.warning(
            "User %s tried to get connections without registration",
            query.from_user.username,
        )
        return

    connections = await ConnectionRepository(session).get_by_user_id(
        user_id=user.id, show_deleted=user.admin
    )
    if not connections:
        await query.answer("No connections found.")
        logger.info("No connections found for user %s", query.from_user.username)
        return

    await query.answer("We found your connections.")
    logger.info("Connections found for user %s", query.from_user.username)

    message = await _check_message_accessible(query)
    if message is None:
        return

    back_button = create_back_button(
        UserActionData(
            action=UserAction.startbutton,
            chat_id=query.from_user.id,
            user_id=user.id,
        )
    )
    await message.answer(
        "Ваши подключения:",
        reply_markup=get_my_connections_markup(
            query.from_user.id,
            user.id,
            connections,
            back_button=back_button,
        ),
    )


@router.callback_query(UserActionData.filter(F.action == UserAction.addcon))
async def add_connection(
    query: types.CallbackQuery,
    callback_data: UserActionData,
    session: AsyncSession,
    user: User | None,
) -> None:
    """
    Создание нового подключения для пользователя.

    Args:
        query: Callback query от пользователя
        callback_data: Данные из callback
        session: Сессия базы данных
        user: Текущий пользователь
    """
    expiry_time_days = 3
    logger.info("User %s requested to add a connection", query.from_user.username)

    if not user:
        await query.answer("Внутренняя ошибка")
        logger.warning(
            "Попытка создания подключения без регистрации: %s", query.from_user.username
        )
        return

    username = user.username
    if not username:
        await query.answer(
            "Для создания подключения необходимо указать username в Telegram"
        )
        logger.warning(
            "Попытка создания подключения без username в Telegram: user_id=%s",
            user.id,
        )
        return

    try:
        api_client = get_async_client()
        email = await api_client.add_connection(
            username=username,
            tg_id=user.id,
            limit_ip=3,
            expiry_time_days=expiry_time_days,
        )

        if not email:
            raise ValueError("Не удалось получить email для подключения")

        inbound = await api_client.get_inbound()
        if not inbound:
            raise ValueError("Не удалось получить inbound")

        connection = await api_client.get_connection(inbound, email=email)
        if not connection:
            raise ValueError("Не удалось получить данные подключения")

        connection_url = api_client.create_link(connection, inbound)

        # Сохранение в базу данных
        await ConnectionRepository(session).create(
            inbound=api_client.inbound_id,
            email=email,
            connection_url=connection_url,
            created_at=datetime.datetime.now(datetime.UTC),
            expired_at=datetime.datetime.now(datetime.UTC)
            + datetime.timedelta(days=expiry_time_days),
            uuid=connection.id,
            user=user,
            host="scvnotready.online",
        )

        logger.info("Подключение успешно создано для %s", query.from_user.username)
        await query.answer("✅ Подключение успешно создано")
    except Exception as e:
        error_msg = f"Ошибка при создании подключения: {str(e)}"
        logger.error(error_msg, exc_info=True)
        await query.answer("❌ Не удалось создать подключение")
        return

    message = await _check_message_accessible(query)
    if message is None:
        return

    await message.answer(
        "Подключение успешно создано.",
        reply_markup=get_user_actions_markup(
            query.from_user.username or "",
            admins,
            query.from_user.id,
            user_id=user.id,
        ),
    )


@router.callback_query(UserActionData.filter(F.action == UserAction.viewcon))
async def view_connection(
    query: types.CallbackQuery,
    callback_data: UserActionData,
    session: AsyncSession,
    user: User | None,
) -> None:
    """
    Просмотр информации о подключении.

    Args:
        query: Callback query от пользователя
        callback_data: Данные из callback
        session: Сессия базы данных
        user: Текущий пользователь
    """
    logger.info("Запрос на просмотр подключения от %s", query.from_user.username)

    if not user:
        await query.answer("Сначала необходимо зарегистрироваться!")
        logger.warning(
            "Попытка просмотра подключения без регистрации: %s",
            query.from_user.username,
        )
        return

    if not callback_data.connection_id:
        await query.answer("❗️ Не указан ID подключения")
        logger.error("ID подключения не предоставлен для %s", query.from_user.username)
        return

    connection = await ConnectionRepository(session).get_by_id(
        callback_data.connection_id
    )
    if not connection:
        await query.answer("❗️ Подключение не найдено")
        logger.error("Подключение не найдено для %s", query.from_user.username)
        return

    # Форматирование дат в местную временную зону
    created_at = connection.created_at.strftime("%Y-%m-%d %H:%M:%S")
    expired_at = connection.expired_at.strftime("%Y-%m-%d %H:%M:%S")

    await query.answer("✅ Подключение найдено")

    message = await _check_message_accessible(query)
    if message is None:
        return

    back_button = create_back_button(
        UserActionData(
            action=UserAction.conlist,
            chat_id=query.from_user.id,
            user_id=user.id,
        )
    )

    await message.answer(
        f"📡 Данные подключения:\n\n"
        f"Email: {connection.email}\n"
        f"URL: <code>{connection.connection_url}</code>\n"
        f"Создано: {created_at}\n"
        f"Истекает: {expired_at}",
        reply_markup=get_view_connection_markup(
            chat_id=query.from_user.id,
            user_id=user.id,
            connection_id=connection.id,
            back_button=back_button,
            is_admin=user.admin,
        ),
        parse_mode="HTML",
    )


@router.callback_query(UserActionData.filter(F.action == UserAction.deletecon))
async def delete_connection(
    query: types.CallbackQuery,
    callback_data: UserActionData,
    session: AsyncSession,
    user: User | None,
) -> None:
    """
    Удаление подключения пользователя.

    Args:
        query: Callback query от пользователя
        callback_data: Данные из callback
        session: Сессия базы данных
        user: Текущий пользователь
    """
    logger.info("Запрос на удаление подключения от %s", query.from_user.username)

    if not user:
        await query.answer("Сначала необходимо зарегистрироваться!")
        logger.warning(
            "Попытка удаления подключения без регистрации: %s", query.from_user.username
        )
        return

    if not callback_data.connection_id:
        await query.answer("❗️ Не указан ID подключения")
        logger.error("ID подключения не предоставлен для %s", query.from_user.username)
        return

    try:
        connection = await ConnectionRepository(session).get_by_id(
            callback_data.connection_id
        )
        if not connection:
            await query.answer("❗️ Подключение не найдено в базе данных")
            logger.error("Подключение не найдено в БД для %s", query.from_user.username)
            return

        api_client = get_async_client()
        existing_connection = await api_client.get_connection(uuid=connection.uuid)

        if existing_connection:
            try:
                await api_client.delete_connection(connection.uuid)
                logger.info(
                    "Подключение успешно удалено из API для %s",
                    query.from_user.username,
                )
            except Exception as e:
                error_msg = f"Ошибка при удалении подключения из API: {str(e)}"
                logger.error(error_msg, exc_info=True)
                await query.answer("❗️ Ошибка при удалении подключения из API")
                return
        else:
            logger.warning(
                "Подключение не найдено в API для %s (uuid: %s)",
                query.from_user.username,
                connection.uuid,
            )

        # Удаление или обновление записи в БД
        if callback_data.absolute_delete:
            await ConnectionRepository(session).delete(connection)
            logger.info(
                "Подключение полностью удалено из БД для %s", query.from_user.username
            )
        else:
            await ConnectionRepository(session).update(connection, exists_in_api=False)
            logger.info(
                "Подключение помечено как удаленное для %s", query.from_user.username
            )

        await query.answer("✅ Подключение успешно удалено")

        message = await _check_message_accessible(query)
        if message is None:
            return

        text, markup = _handle_start_action(message.chat, user)
        await message.answer(text, reply_markup=markup)

    except Exception as e:
        error_msg = f"Неожиданная ошибка при удалении подключения: {str(e)}"
        logger.error(error_msg, exc_info=True)
        await query.answer("❌ Произошла ошибка при удалении подключения")


@router.errors()
async def handle_errors(event: types.ErrorEvent) -> None:
    """
    Глобальный обработчик ошибок для роутера.

    Args:
        event: Событие с ошибкой
    """
    logger.critical(
        "Критическая ошибка в обработчике: %s", event.exception, exc_info=True
    )
