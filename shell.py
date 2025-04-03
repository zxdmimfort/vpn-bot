from IPython.terminal.embed import InteractiveShellEmbed
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.config import get_session_maker
from db.models import Base, Connection, User


def main() -> None:
    # Определяем переменные, доступные в сессии шелла
    locals_dict = globals().copy()
    session_maker = get_session_maker()
    session: AsyncSession = session_maker()
    locals_dict.update(
        {
            "session": session,
            "Base": Base,
            "User": User,
            "Connection": Connection,
            "select": select,
        }
    )
    shell = InteractiveShellEmbed()
    shell(header="Shell session", user_ns=locals_dict)


if __name__ == "__main__":
    main()
