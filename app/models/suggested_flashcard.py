from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import Base


class SuggestedFlashcard(Base):
    __tablename__ = "suggested_flashcards"

    id = Column(Integer, primary_key=True)

    chapter_id = Column(
        Integer,
        ForeignKey("chapters.id", ondelete="CASCADE"),
        nullable=False,
    )

    question = Column(String, nullable=False)
    answer = Column(String, nullable=False)

    position = Column(
        Integer,
        nullable=False,
        default=1,
    )

    chapter = relationship(
        "Chapter",
        back_populates="suggested_flashcards",
    )