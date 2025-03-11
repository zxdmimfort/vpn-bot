from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), nullable=False)
    first_name = Column(String(100), nullable=False)
    chat_id = Column(Integer(), nullable=False)

    # One-to-many relationship: one user can have many connections.
    connections = relationship("Connection", back_populates="user")

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"


class Connection(Base):
    __tablename__ = "connections"
    id = Column(Integer, primary_key=True, autoincrement=True)
    inbound = Column(Integer(), nullable=False)
    email = Column(String(100), nullable=False)
    connection_url = Column(String(100), nullable=False)
    # Foreign key to link Connection with User.
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationship back to the owning user.
    user = relationship("User", back_populates="connections")

    def __repr__(self) -> str:
        return f"<Connection(id={self.id}, email={self.email})>"
