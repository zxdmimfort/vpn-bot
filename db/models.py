from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    chat_id: Mapped[int] = mapped_column(nullable=False)

    # One-to-many relationship: one user can have many connections.
    connections: Mapped[list["Connection"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username})>"


class Connection(Base):
    __tablename__ = "connections"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    inbound: Mapped[int] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    connection_url: Mapped[str] = mapped_column(String(100), nullable=False)
    host: Mapped[str] = mapped_column(String(100), nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Relationship back to the owning user.
    user: Mapped["User"] = relationship(back_populates="connections")

    def __repr__(self) -> str:
        return f"<Connection(id={self.id}, email={self.email})>"
