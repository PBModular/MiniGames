from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy import String
from typing import Optional
from datetime import datetime
from .config import CockConfig

class Base(DeclarativeBase):
    pass


class CockState(Base):
    __tablename__ = 'cock_state'
    chat_id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(primary_key=True)
    cock_size: Mapped[float] = mapped_column(nullable=True, default=lambda: float(CockConfig.DEFAULT_COCK_SIZE))
    is_participating: Mapped[bool]
    active_event: Mapped[Optional[str]] = mapped_column(nullable=True)
    event_duration: Mapped[int] = mapped_column(default=0)
    cooldown: Mapped[Optional[datetime]] = mapped_column(nullable=True, default=None)
    event_data: Mapped[Optional[str]] = mapped_column(nullable=True)
    last_confession: Mapped[Optional[str]] = mapped_column(nullable=True)
    prestige_badge: Mapped[Optional[str]] = mapped_column(String(CockConfig.PRESTIGE_BADGE_MAX_LENGTH), nullable=True)

    def __repr__(self):
        return (f"<CockState(chat_id={self.chat_id}, user_id={self.user_id}, "
                f"cock_size={self.cock_size}, is_participating={self.is_participating}, "
                f"active_event='{self.active_event}', event_duration={self.event_duration}, "
                f"cooldown={self.cooldown}, event_data='{self.event_data}', "
                f"last_confession='{self.last_confession}', prestige_badge='{self.prestige_badge}')>")
