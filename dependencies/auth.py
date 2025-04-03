from typing import Awaitable, Callable

from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import User


async def is_user_registered(message: Message, session: AsyncSession) -> bool:
    stmt = select(User).where(User.chat_id == message.chat.id)
    result = await session.execute(stmt)
    return bool(result.scalars().all())


async def get_current_user_or_none(chat_id: int, session: AsyncSession) -> User | None:
    stmt = select(User).where(User.chat_id == chat_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


# def login_required(admins: tuple[str, ...]) -> Callable:
#     def mid_wrapper(handler: Callable[[Message, User], Awaitable[None]]) -> Callable:
#         async def wrapper(message: Message, session: AsyncSession) -> None:
#             user = get_current_user_or_none(session, message)
#             if user:
#                 await handler(message, user)
#             else:
#                 await message.answer(
#                     "You need to register first!",
#                     reply_markup=get_user_actions_markup(
#                         message.chat.username or "", admins
#                     ),
#                 )

#         return wrapper

#     return mid_wrapper


def admin_required(admins: tuple[str, ...]) -> Callable:
    def mid_wrapper(handler: Callable[[Message], Awaitable[None]]) -> Callable:
        async def wrapper(message: Message) -> None:
            if message.chat.username in admins:
                await handler(message)
            else:
                await message.answer("You don't have permission to access this.")

        return wrapper

    return mid_wrapper
