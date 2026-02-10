from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Numeric
from decimal import Decimal
from sqlalchemy.orm import relationship
from .base import Base
from app.utils.time import utcnow

class Flashcard(Base):
    __tablename__ = 'flashcards'

    id = Column(Integer, primary_key=True)
    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    identify_language = Column(Integer, nullable=True, default='0')  # 0 for answer in English, 1 for Question in English, 2 for both in English
    part_of_speech = Column(String(20), nullable=True, default='None')  # 'noun', 'verb', 'adjective', etc.
    

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
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)

    # Relationship to User
    user_id = Column(String(50), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="flashcards")

    def to_dict(self):
        return {
            "id": self.id,
            "question": self.question,
            "answer": self.answer,
            "level": self.level,
            "ease": self.ease,
            "interval": self.interval,
            "last_review": self.last_review,
            "next_review": self.next_review,
            "user_id": self.user_id,
            "show_answer": False,
        }
