from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from dependencies.auth import get_current_user_or_none


class DataBaseSession(BaseMiddleware):
    def __init__(self, session_pool: async_sessionmaker[AsyncSession]):
        self.session_pool = session_pool

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ):
        async with self.session_pool() as session:
            data["session"] = session
            return await handler(event, data)


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Update, dict[str, Any]], Awaitable[Any]],
        event: Update,  # type: ignore
        data: dict[str, Any],
    ):
        chat_id = event.event.from_user.id  # type: ignore
        session = data["session"]
        user = await get_current_user_or_none(chat_id, session)
        data["user"] = user
        return await handler(event, data)
