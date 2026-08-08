from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.models.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class UserChapterProgress(Base):
    __tablename__ = "user_chapter_progress"

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "chapter_id",
            name="uq_user_chapter_progress",
        ),
    )

    id = Column(Integer, primary_key=True)

    user_id = Column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    chapter_id = Column(
        Integer,
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    is_read = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

    user = relationship(
        "User",
        back_populates="chapter_progress",
    )

    chapter = relationship(
        "Chapter",
        back_populates="user_progress",
    )


class GuestChapterProgress(Base):
    __tablename__ = "guest_chapter_progress"

    __table_args__ = (
        UniqueConstraint(
            "guest_user_id",
            "chapter_id",
            name="uq_guest_chapter_progress",
        ),
    )

    id = Column(Integer, primary_key=True)

    guest_user_id = Column(
        String(36),
        ForeignKey("guest_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    chapter_id = Column(
        Integer,
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    is_read = Column(
        Boolean,
        nullable=False,
        default=False,
    )

    completed_at = Column(
        DateTime(timezone=True),
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow,
    )

    guest_user = relationship(
        "GuestUser",
        back_populates="chapter_progress",
    )

    chapter = relationship(
        "Chapter",
        back_populates="guest_progress",
    )