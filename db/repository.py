from typing import Generic, Sequence, Type, TypeVar
from sqlalchemy import Column, Integer, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

from db.models import Connection, User


class Base(DeclarativeBase):
    id = Column(Integer, primary_key=True)


ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    model: Type[ModelType]

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, id: int) -> ModelType | None:
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def create(self, **kwargs) -> ModelType:
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj, **kwargs) -> ModelType:
        for key, value in kwargs.items():
            setattr(obj, key, value)
        self.session.add(obj)
        await self.session.commit()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj) -> None:
        await self.session.delete(obj)
        await self.session.commit()


class UserRepository(BaseRepository):
    model = User

    async def get_by_username(self, username: str) -> User | None:
        result = await self.session.execute(
            select(self.model).where(self.model.username == username)
        )
        return result.scalar_one_or_none()

    async def get_by_chat_id(self, chat_id: int) -> User | None:
        result = await self.session.execute(
            select(self.model).where(self.model.chat_id == chat_id)
        )
        return result.scalar_one_or_none()


class ConnectionRepository(BaseRepository):
    model = Connection

    async def get_by_email(self, email: str) -> Connection | None:
        result = await self.session.execute(
            select(self.model).where(self.model.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int) -> Sequence[Connection]:
        result = await self.session.execute(
            select(self.model).where(self.model.user_id == user_id)
        )
        return result.scalars().all()
