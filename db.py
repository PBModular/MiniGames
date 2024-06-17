from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from typing import Optional


class Base(DeclarativeBase):
    pass


class ChatState(Base):
    __tablename__ = 'chat_state'
    chat_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(primary_key=True)
    cock_size: Mapped[int] = mapped_column(nullable=True)
    is_participating: Mapped[bool]

    def __repr__(self):
        return f"chat_id={self.chat_id}, user_id={self.user_id}, cock_size={self.cock_size}, is_participating={self.is_participating}"
