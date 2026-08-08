from datetime import datetime, timedelta, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String, Integer, Date  
from sqlalchemy.orm import relationship

from app.models.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class GuestUser(Base):
    __tablename__ = "guest_users"

    # This matches session["guest_id"].
    id = Column(String(36), primary_key=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )

    last_activity_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: utcnow() + timedelta(days=7),
    )

    # Filled only after the guest logs in and claims the workspace.
    claimed_by_user_id = Column(
        String,
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    claimed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    claimed_by_user = relationship(
        "User",
        foreign_keys=[claimed_by_user_id],
    )

    flashcards = relationship(
    "GuestFlashcard",
    back_populates="guest_user",
    cascade="all, delete-orphan",
    )


    level = Column(String(2), nullable=True)
    role = Column(String(10), nullable=False)  # 'student', 'teacher', 'admin'
    study_streak = Column(Integer, nullable=True, default=0)
    max_study_streak = Column(Integer, nullable=True, default=0)
    streak_last_date = Column(Date, nullable=True)
    points = Column(Integer, nullable=True, default=0)
    max_points = Column(Integer, nullable=True, default=0) # points * max_study_streak
    flashcards_studied = Column(Integer, nullable=True, default=0)
    rate_three_count = Column(Integer, nullable=True, default=0)

    chapter_progress = relationship(
        "GuestChapterProgress",
        back_populates="guest_user",
        cascade="all, delete-orphan",
    )

    @property
    def is_claimed(self):
        return self.claimed_by_user_id is not None