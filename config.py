import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session


def get_engine(db_path: str = "database.db") -> Engine:
    return create_engine(f"sqlite:///{db_path}", echo=True)


def get_session(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker[Session](bind=engine)


load_dotenv(dotenv_path="token.env")


VPN_USERNAME: str = os.getenv("VPN_USERNAME") or ""
VPN_PASSWORD: str = os.getenv("VPN_PASSWORD") or ""
DEFAULT_INBOUND: str = os.getenv("DEFAULT_INBOUND") or "2"
BASE_URL: str = os.getenv("BASE_URL") or ""
