from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


async def is_user_registered(message: Message, session: AsyncSession) -> bool:
    stmt = select(User).where(User.chat_id == message.chat.id)
    result = await session.execute(stmt)
    return bool(result.scalars().all())


async def get_current_user_or_none(chat_id: int, session: AsyncSession) -> User | None:
    stmt = select(User).where(User.chat_id == chat_id)
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


def get_admins_list() -> tuple[str, ...]:
    admins: tuple[str, ...] = ("aoi_dev", "mimfort")
    return admins
