from .base import Base
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

class CalendarSettings(Base):
    __tablename__ = "calendar_settings"

    id = Column(Integer, primary_key=True)
    start_hour = Column(Integer, default=7)
    end_hour = Column(Integer, default=21)
    available_saturday = Column(Boolean, default=False)
    available_sunday = Column(Boolean, default=True)
    show_today = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    lesson_duration = Column(Integer, default=30)  # in minutes 

    teacher_id = Column(String(50), ForeignKey("users.id"), unique=True)
    teacher = relationship("User", back_populates="calendar_settings")
    