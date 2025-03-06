import sqlalchemy
from sqlalchemy import create_engine, Column, Integer, BigInteger,  String, ForeignKey, Table
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import DeclarativeBase
class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'  # Define the table name

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False)
    first_name = Column(String(100), nullable=False)
    chat_id = Column(Integer(), nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username})>"