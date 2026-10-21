from sqlalchemy import (
    Column,
    ForeignKey,
    Integer,
    String,
)

from sqlalchemy.orm import relationship

from app.models.base import Base


class VideoSuggestedFlashcard(Base):
    __tablename__ = "video_suggested_flashcards"

    id = Column(
        Integer,
        primary_key=True,
    )

    video_id = Column(
        Integer,
        ForeignKey(
            "videos.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    question = Column(
        String,
        nullable=False,
    )

    answer = Column(
        String,
        nullable=False,
    )

    position = Column(
        Integer,
        nullable=False,
        default=1,
    )

    video = relationship(
        "Video",
        back_populates="suggested_flashcards",
    )