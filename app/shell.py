from IPython.terminal.embed import InteractiveShellEmbed
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.login_client import get_async_client
from app.db.config import get_session_maker
from app.db.models import Base, Connection, User


def main() -> None:
    # Определяем переменные, доступные в сессии шелла
    locals_dict = globals().copy()
    session_maker = get_session_maker()
    session: AsyncSession = session_maker()
    api = get_async_client()
    locals_dict.update(
        {
            "session": session,
            "Base": Base,
            "User": User,
            "Connection": Connection,
            "select": select,
            "api": api,
        }
    )
    print("Welcome to the interactive shell!")
    shell = InteractiveShellEmbed()
    shell(header="Shell session", user_ns=locals_dict)


if __name__ == "__main__":
    main()
