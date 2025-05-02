import logging
import datetime
from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart, or_f
from sqlalchemy.ext.asyncio import AsyncSession


from app.db.repository import ConnectionRepository, UserRepository
from app.dependencies.auth import get_admins_list
from app.kbds.menu_markups import (
    UserAction,
    UserActionData,
    get_my_connections_markup,
    get_user_actions_markup,
    get_view_connection_markup,
)
from app.db.models import User
from app.login_client import get_async_client

router = Router()
admins: tuple[str, ...] = get_admins_list()
logger = logging.getLogger(__name__)


@router.message(or_f(Command("help"), CommandStart()))
async def send_basic_actions(
    message: types.Message,
    user: User | None,
) -> None:
    """
    Handle the /start and /help commands and send the user a list of actions.
    """
    logger.info("User %s triggered /start or /help", message.chat.username)
    await message.answer(
        "Choose an action:",
        reply_markup=get_user_actions_markup(
            message.chat.username or "",
            admins,
            message.chat.id,
            user_id=user.id if user else None,
            is_admin=user.admin if user else False,
        ),
    )


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
    await query.message.answer(  # type: ignore
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

    await query.message.answer(  # type: ignore
        "Ваши подключения:",
        reply_markup=get_my_connections_markup(
            query.from_user.id, user.id, connections
        ),
    )


@router.callback_query(UserActionData.filter(F.action == UserAction.addcon))
async def add_connection(
    query: types.CallbackQuery,
    callback_data: UserActionData,
    session: AsyncSession,
    user: User | None,
) -> None:
    expiry_time_days = 3
    logger.info("User %s requested to add a connection", query.from_user.username)
    if not user:
        await query.answer(
            "You need to register first!",
            reply_markup=get_user_actions_markup(
                query.from_user.username or "",
                admins,
                query.from_user.id,
                user_id=user.id if user else None,
            ),
        )
        logger.warning(
            "User %s tried to add a connection without registration",
            query.from_user.username,
        )
        return
    api_client = get_async_client()
    email = await api_client.add_connection(
        query.from_user.username,  # type: ignore
        query.from_user.id,
        limit_ip=3,
        expiry_time_days=expiry_time_days,
    )
    if not email:
        await query.answer("Failed to create connection.")
        logger.error(
            "Failed to create connection for user %s", query.from_user.username
        )
        return
    inbound = await api_client.get_inbound()
    if not inbound:
        await query.answer("Inbound not found.")
        logger.error("Inbound not found for user %s", query.from_user.username)
        return
    # Check existing connection
    connection = await api_client.get_connection(inbound, email=email)
    if connection is None:
        await query.answer("Connection not found.")
        logger.error("Connection not found for user %s", query.from_user.username)
        return
    connection_url = api_client.create_link(connection, inbound)

    # Save connection to the database
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

    logger.info("Connection created successfully for user %s", query.from_user.username)
    await query.answer("Connection created successfully.")
    await query.message.answer(  # type: ignore
        "Connection created successfully.",
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
    logger.info("User %s requested to view a connection", query.from_user.username)
    if not user:
        await query.answer("You need to register first!")
        logger.warning(
            "User %s tried to view a connection without registration",
            query.from_user.username,
        )
        return
    if not callback_data.connection_id:
        logger.error(
            "Connection ID not provided for user %s",
            query.from_user.username,
        )
        await query.answer("❗️Connection ID not provided.")
        return
    # Fetch connection from the database
    connection = await ConnectionRepository(session).get_by_id(
        callback_data.connection_id
    )
    if not connection:
        await query.answer("❗️Connection not found.")
        logger.error("Connection not found for user %s", query.from_user.username)
        return
    await query.answer("✅ Connection found.")
    logger.info("Connection found for user %s", query.from_user.username)

    await query.message.answer(  # type: ignore
        (
            f"{connection.email} - {connection.connection_url}\n"
            f"Created at: {connection.created_at}\n"
            f"Expired at: {connection.expired_at}\n"
        ),
        reply_markup=get_view_connection_markup(
            chat_id=query.from_user.id, user_id=user.id, connection_id=connection.id
        ),
    )


@router.callback_query(UserActionData.filter(F.action == UserAction.deletecon))
async def delete_connection(
    query: types.CallbackQuery,
    callback_data: UserActionData,
    session: AsyncSession,
    user: User | None,
) -> None:
    skip_api_delete: bool = False
    logger.info("User %s requested to delete a connection", query.from_user.username)
    if not user:
        await query.answer("You need to register first!")
        logger.warning(
            "User %s tried to delete a connection without registration",
            query.from_user.username,
        )
        return
    if not callback_data.connection_id:
        logger.error(
            "Connection ID not provided for user %s",
            query.from_user.username,
        )
        return
    connection = await ConnectionRepository(session).get_by_id(
        callback_data.connection_id
    )
    if not connection:
        # Logging the error
        logger.error(
            "Connection not found in the database for user %s",
            query.from_user.username,
        )
        await query.answer("❗️Connection not found in the database.")
        return
    await query.answer("✅ Connection found.")
    logger.info(
        "Connection found in the database for user %s", query.from_user.username
    )

    api_client = get_async_client()
    # Check existing connection
    existing_connection = await api_client.get_connection(uuid=connection.uuid)
    if not existing_connection:
        logger.error(
            "Connection not found in the API for user %s",
            query.from_user.username,
        )
        await query.answer("❗️Connection not found in the API.")
        skip_api_delete = True

    # Delete connection from the API if it exists
    if not skip_api_delete:
        try:
            await api_client.delete_connection(connection.uuid)
        except Exception as e:
            logger.error(
                "Failed to delete connection from API for user %s: %s",
                query.from_user.username,
                e,
            )
            await query.answer("❗️Failed to delete connection from API.")
            return

    # Delete connection from the database
    await ConnectionRepository(session).update(connection, exists_in_api=False)
    logger.info("Connection deleted successfully for user %s", query.from_user.username)
    await query.answer("Connection deleted successfully.")
    await query.message.answer(  # type: ignore
        "Connection deleted successfully.",
        reply_markup=get_user_actions_markup(
            query.from_user.username or "",
            admins,
            query.from_user.id,
            user_id=user.id,
        ),
    )


# @router.message(Command("settingup"))
# async def send_setting_up_vpn_connection(message: Message) -> None:
#     await message.answer("Скачать nekoray, nekobox: https://matsuridayo.github.io/")
#     await message.answer_photo(photo=FSInputFile(path="img.png"), caption="")


@router.errors()
async def handle_errors(event: types.ErrorEvent) -> None:
    logger.critical("Critical error caused by %s", event.exception, exc_info=True)


# register_callback("register", lambda q: send_register(q.message))
