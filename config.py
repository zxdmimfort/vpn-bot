from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session


def get_engine(db_path: str = "database.db") -> Engine:
    return create_engine(f"sqlite:///./{db_path}", echo=True)


def get_session(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker[Session](bind=engine)
