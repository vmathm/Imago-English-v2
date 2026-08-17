from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Numeric, Boolean
from decimal import Decimal
from sqlalchemy.orm import relationship

from app.models.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class GuestFlashcard(Base):
    __tablename__ = "guest_flashcards"

    id = Column(Integer, primary_key=True)

    guest_user_id = Column(
        String(36),
        ForeignKey("guest_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)

      # Spaced repetition fields
    level = Column(Integer, nullable=False, default=0) # number of repetitions
    ease = Column(Numeric(3, 2),nullable=False,default=Decimal("2.00"))
    interval = Column(Integer, nullable=False, default=1)
    last_review = Column(DateTime(timezone=True), nullable=True)
    next_review = Column(DateTime(timezone=True), nullable=True)

    # Visibility & source
    show_answer = Column(Boolean, nullable=False, default=False)
    reviewed_by_tc = Column(Boolean, nullable=False, default=False)
    add_by_tc = Column(Boolean, nullable=False, default=False)
    add_by_user = Column(Boolean, nullable=False, default=False)
   

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )

    guest_user = relationship(
        "GuestUser",
        back_populates="flashcards",
    )