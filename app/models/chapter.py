from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.models.base import Base


def utcnow():
    return datetime.now(timezone.utc)


class Chapter(Base):
    __tablename__ = "chapters"

    __table_args__ = (
        UniqueConstraint(
            "book_id",
            "slug",
            name="uq_chapters_book_slug",
        ),
        UniqueConstraint(
            "book_id",
            "position",
            name="uq_chapters_book_position",
        ),
    )

    id = Column(Integer, primary_key=True)

    book_id = Column(
        Integer,
        ForeignKey("books.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    position = Column(Integer, nullable=False)

    text_path = Column(
        String(500),
        nullable=False,
    )

    audio_path = Column(
        String(500),
        nullable=False,
    )
    
    is_free = Column(
        Boolean,
        nullable=False,
        default=False,
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

    book = relationship(
        "Book",
        back_populates="chapters",
    )

    user_progress = relationship(
    "UserChapterProgress",
    back_populates="chapter",
    cascade="all, delete-orphan",
    )

    guest_progress = relationship(
        "GuestChapterProgress",
        back_populates="chapter",
        cascade="all, delete-orphan",
    )