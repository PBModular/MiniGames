from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from typing import Optional
from datetime import datetime

class Base(DeclarativeBase):
    pass


class CockState(Base):
    __tablename__ = 'cock_state'
    chat_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(primary_key=True)
    cock_size: Mapped[float] = mapped_column(nullable=True)
    is_participating: Mapped[bool]
    active_event: Mapped[Optional[str]] = mapped_column(nullable=True)
    event_duration: Mapped[int] = mapped_column(default=0)
    cooldown: Mapped[Optional[datetime]] = mapped_column(nullable=True, default=None)
    event_data: Mapped[Optional[str]] = mapped_column(nullable=True)

    def __repr__(self):
        return f"chat_id={self.chat_id}, user_id={self.user_id}, cock_size={self.cock_size}, is_participating={self.is_participating}, \
            active_event={self.active_event}, event_duration={self.event_duration}, cooldown={self.cooldown}, event_data={self.event_data}"
