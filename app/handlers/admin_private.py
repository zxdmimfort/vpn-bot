import logging
from aiogram import F, Router, types
from sqlalchemy.ext.asyncio import AsyncSession

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


@router.callback_query(UserActionData.filter(F.action == UserAction.adminmarkup))
async def send_admin_actions(
    query: types.CallbackQuery,
    callback_data: UserActionData,
    user: User | None,
    session: AsyncSession,
) -> None:
    """
    Handle the admin actions.
    """
    if not user:
        logger.warning(
            f"User {query.from_user.id} attempted to access admin actions without being logged in."
        )
        await query.answer("You are not authorized to perform this action.")
        return
    if not user.admin:
        logger.warning(
            f"User {user.username} attempted to access admin actions without permission."
        )
        await query.answer("You are not authorized to perform this action.")
    await query.answer("Loading admin actions...")
    await query.message.answer(  # type: ignore
        f"Admin: {user.admin}",
        reply_markup=get_admin_actions_markup(query.from_user.id, user.id),
    )


@router.callback_query(AdminActionData.filter(F.action == AdminAction.userlist))
async def send_user_list(
    query: types.CallbackQuery,
    callback_data: AdminActionData,
    user: User | None,
    session: AsyncSession,
) -> None:
    """
    Handle the user list action.
    """
    # Check if the user is an admin
    if not user:
        logger.warning(
            f"User {query.from_user.id} attempted to access admin actions without being logged in."
        )
        await query.answer("You are not authorized to perform this action.")
        return

    if not user.admin:
        logger.warning(
            f"User {user.username} attempted to access admin actions without permission."
        )
        await query.answer("You are not authorized to perform this action.")
        return

    users = await UserRepository(session).get_all()
    if not users:
        await query.answer("No users found.")
        return

    await query.answer("Loading user list...")
    await query.message.answer(  # type: ignore
        "User List:",
        reply_markup=get_admin_userlist_markup(
            query.from_user.id,
            user.id,
            users,
        ),
    )


@router.callback_query(AdminActionData.filter(F.action == AdminAction.userconn))
async def send_user_stat(
    query: types.CallbackQuery,
    callback_data: AdminActionData,
    user: User | None,
    session: AsyncSession,
) -> None:
    """
    Handle the user stat action. And get user connections.
    """
    # Check if the user is an admin
    if not user:
        logger.warning(
            f"User {query.from_user.id} attempted to access admin actions without being logged in."
        )
        await query.answer("You are not authorized to perform this action.")
        return

    if not user.admin:
        logger.warning(
            f"User {user.username} attempted to access admin actions without permission."
        )
        await query.answer("You are not authorized to perform this action.")
        return

    user_connections = await ConnectionRepository(session).get_by_user_id(
        callback_data.user_id
    )
    if not user_connections:
        await query.answer("No connections found for this user.")
        return

    # Return user connections
    await query.answer("Loading user connections...")
    await query.message.answer(  # type: ignore
        "User Connections:",
        reply_markup=get_admin_user_connections_markup(
            query.from_user.id,
            user.id,
            user_connections,
        ),
    )


@router.callback_query(AdminActionData.filter(F.action == AdminAction.connstat))
async def send_user_connection_stat(
    query: types.CallbackQuery,
    callback_data: AdminActionData,
    user: User | None,
    session: AsyncSession,
) -> None:
    """
    Handle the user connection stat action.
    """
    # Check if the user is an admin
    if not user:
        logger.warning(
            f"User {query.from_user.id} attempted to access admin actions without being logged in."
        )
        await query.answer("You are not authorized to perform this action.")
        return

    if not user.admin:
        logger.warning(
            f"User {user.username} attempted to access admin actions without permission."
        )
        await query.answer("You are not authorized to perform this action.")
        return

    if not callback_data.connection_id:
        logger.warning(
            f"User {user.username} attempted to access admin actions without connection_id."
        )
        await query.answer("Connection ID not found.")
        return

    async_client = get_async_client()
    connection = await ConnectionRepository(session).get_by_id(
        callback_data.connection_id
    )
    if not connection:
        logger.warning(f"Connection {callback_data.connection_id} not found.")
        await query.answer("Connection not found.")
        return

    clients_stats = await async_client.get_clients_stats()
    stats = clients_stats.get(connection.email)
    if not isinstance(stats, ClientStats):
        logger.warning(f"Client stats for {connection.email} not found in the inbound.")
        await query.answer("Client stats not found.")
        return

    # Return user connections
    await query.answer("Loading user connection stats...")
    await query.message.answer(  # type: ignore
        (
            f"User {stats.email} Connection Stats:\n"
            f"Up: {stats.up}\n"
            f"Down: {stats.down}\n"
            f"Total: {stats.total}\n"
            f"Expiry Time: {stats.expiryTime}\n"
        )
    )
