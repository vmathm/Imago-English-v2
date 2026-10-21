from sqlalchemy import (
    Column,
    Integer,
    String,
    ForeignKey,
)

from sqlalchemy.orm import relationship


from .base import Base

class Video(Base):
    __tablename__ = "videos"

    id = Column(
        Integer,
        primary_key=True,
    )

    title = Column(
        String(255),
        nullable=False,
    )

    thumbnail_object_name = Column(
        String(500),
        nullable=True,
    )

    video_url = Column(
        String(500),
        nullable=False,
    )

    level = Column(
        String(2),
        nullable=True,
    )

    text_path = Column(
        String(500),
        nullable=True,
    )   

    suggested_flashcards = relationship(
    "VideoSuggestedFlashcard",
    back_populates="video",
    cascade="all, delete-orphan",
    order_by="VideoSuggestedFlashcard.position",
    )