import os
from dotenv import load_dotenv
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def get_engine(db_path: str = "database.db") -> AsyncEngine:
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=True)

    @event.listens_for(engine.sync_engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    return engine


session_maker = async_sessionmaker(
    bind=get_engine(), class_=AsyncSession, expire_on_commit=False
)


def get_session_maker() -> async_sessionmaker[AsyncSession]:
    return session_maker


load_dotenv(dotenv_path="token.env")


VPN_USERNAME: str = os.getenv("VPN_USERNAME") or ""
VPN_PASSWORD: str = os.getenv("VPN_PASSWORD") or ""
DEFAULT_INBOUND: str = os.getenv("DEFAULT_INBOUND") or "1"
BASE_URL: str = os.getenv("BASE_URL") or ""
