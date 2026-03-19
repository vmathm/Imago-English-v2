from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.utils.time import utcnow
from .base import Base

class UserAudiobook(Base):
    __tablename__ = "user_audiobooks"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        String(50),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )

    text_url = Column(String(500), nullable=True)
    audio_url = Column(String(500), nullable=True)
    title = Column(String(255), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow
    )

    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=utcnow,
        onupdate=utcnow
    )

    user = relationship("User", back_populates="audiobook")


