from datetime import datetime
from sqlalchemy import ForeignKey, String, false
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)


class User(Base):
    __tablename__ = "users"
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    admin: Mapped[bool] = mapped_column(default=False, server_default=false())
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
    inbound: Mapped[int] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False)
    connection_url: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    expired_at: Mapped[datetime] = mapped_column(nullable=False)
    uuid: Mapped[str] = mapped_column(String(100), nullable=False)
    exists_in_api: Mapped[bool] = mapped_column(default=True)
    enabled: Mapped[bool] = mapped_column(default=True)
    total_gb: Mapped[float] = mapped_column(default=0.0)
    host: Mapped[str] = mapped_column(String(100), default="scvnotready.online")
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    # Relationship back to the owning user.
    user: Mapped["User"] = relationship(back_populates="connections")

    def __repr__(self) -> str:
        return f"<Connection(id={self.id}, email={self.email})>"
