import logging
from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.repository import UserRepository

logger = logging.getLogger(__name__)


class DataBaseSession(BaseMiddleware):
    def __init__(self, session_maker: async_sessionmaker[AsyncSession]):
        self.session_maker = session_maker

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ):
        logger.debug("Opening a new database session")
        async with self.session_maker() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
                logger.debug("Handler executed successfully")
                return result
            except Exception as e:
                logger.error(f"Error during handler execution: {e}")
                raise
            finally:
                logger.debug("Closing the database session")


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ):
        if (
            isinstance(event, Update)
            and event.event
            and hasattr(event.event, "from_user")
            and event.event.from_user
        ):
            chat_id = event.event.from_user.id
            session = data["session"]
            user = await UserRepository(session=session).get_by_chat_id(chat_id)
            data["user"] = user
        else:
            logger.warning("Event is not an Update or user data is missing")
            data["user"] = None

        return await handler(event, data)
