from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base

class UserAudiobook(Base):
    __tablename__ = "user_audiobooks"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)

    text_url = Column(String(500), nullable=True)   # GCS URL to .txt
    audio_url = Column(String(500), nullable=True)  # GCS URL to .mp3

    
    title = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="audiobook", uselist=False)

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_audiobooks_user_id"),
    )
