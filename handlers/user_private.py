from asyncio.log import logger
import datetime
from aiogram import F, Router, types
from aiogram.filters import Command, CommandStart, or_f
from sqlalchemy.ext.asyncio import AsyncSession


from db.repository import ConnectionRepository, UserRepository
from kbds.menu_markups import (
    UserAction,
    UserActionData,
    get_my_connections_markup,
    get_user_actions_markup,
)
from db.models import User
from login_client import get_async_client

router = Router()
admins: tuple[str, ...] = ("aoi_dev", "mimfort")


@router.message(or_f(Command("help"), CommandStart()))
async def send_basic_actions(
    message: types.Message,
    user: User | None,
) -> None:
    """
    Handle the /start and /help commands and send the user a list of actions.
    """
    await message.answer(
        "Choose an action:",
        reply_markup=get_user_actions_markup(
            message.chat.username or "",
            admins,
            message.chat.id,
            user_id=user.id if user else None,
        ),
    )


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
    if not user:
        user = await UserRepository(session).create(
            chat_id=query.from_user.id,
            username=query.from_user.username,
            first_name=query.from_user.first_name,
        )
        text = f"Охайо, {query.from_user.username}!🖖"
    else:
        text = "Вы уже прошли регистрацию!"
    await query.answer(text)
    await query.message.answer(
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
    if not user:
        await query.answer("You need to register first!")
        return
    connections = await ConnectionRepository(session).get_by_user_id(user.id)
    if not connections:
        await query.answer("No connections found.")
        return
    await query.answer("We found your connections.")

    await query.message.answer(
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
        return
    api_client = await get_async_client()
    email = await api_client.add_connection(
        query.from_user.username, limit_ip=3, expiry_time_days=expiry_time_days
    )
    if not email:
        await query.answer("Failed to create connection.")
        return
    connection_url = await api_client.get_connection_by_email(email)
    if not connection_url:
        await query.answer("Failed to get connection URL.")
        return

    # Save connection to the database
    await ConnectionRepository(session).create(
        inbound=api_client.inbound_id,
        email=email,
        connection_url=connection_url,
        created_at=datetime.datetime.now(datetime.UTC),
        expired_at=datetime.datetime.now(datetime.UTC)
        + datetime.timedelta(days=expiry_time_days),
        user=user,
        host="scvnotready.online",
    )

    await query.answer("Connection created successfully.")
    await query.message.answer(
        "Connection created successfully.",
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
