from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_engine(db_path="database.db"):
    return create_engine(f"sqlite:///./{db_path}", echo=True)


def get_session(engine): 
    return sessionmaker(bind=engine)
