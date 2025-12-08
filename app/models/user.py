from sqlalchemy import Column, String, Boolean, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from flask_login import UserMixin
from .base import Base

class User(UserMixin, Base):
    __tablename__ = 'users'

    id = Column(String(50), primary_key=True)
    name = Column(String(15), nullable=False)
    user_name = Column(String(20), nullable=True)
    email = Column(String(254), nullable=False, server_default='none')
    phone = Column(String(15), nullable=True)
    profilepic = Column(String(300), nullable=False, server_default='none')
    level = Column(String(2), nullable=True)
    role = Column(String(10), nullable=False)  # 'student', 'teacher', 'admin'


    
    # "en"   → learning English
    # "pt-BR" → learning Brazilian Portuguese
    learning_language = Column(String(10), nullable=False, default="en")

    delete_date = Column(Date, nullable=True)
    user_stripe_id = Column(String(50), nullable=True)
    join_date = Column(Date, nullable=True)
    last_payment_date = Column(Date, nullable=True)

    active = Column(Boolean, nullable=False, default=False)  # replaces is_active
    study_streak = Column(Integer, nullable=True, default=0)
    max_study_streak = Column(Integer, nullable=True, default=0)
    streak_last_date = Column(Date, nullable=True)
    points = Column(Integer, nullable=True, default=0)
    max_points = Column(Integer, nullable=True, default=0) # points * max_study_streak
    flashcards_studied = Column(Integer, nullable=True, default=0)
    rate_three_count = Column(Integer, nullable=True, default=0)

    # Self-referential relationship for assigned teacher
    assigned_teacher_id = Column(String(50), ForeignKey('users.id'), nullable=True)
    assigned_teacher = relationship('User', remote_side=[id], backref='assigned_students')

    # Relationships to other tables
    flashcards = relationship('Flashcard', back_populates='user')
    calendar_settings = relationship("CalendarSettings", uselist=False, back_populates="teacher")

    audiobook = relationship("UserAudiobook", back_populates="user", uselist=False)
    



    def is_student(self):
        return self.role in ('teacher', '@dmin!', 'student')

    def is_teacher(self):
        return self.role in ('teacher', '@dmin!')

    def is_admin(self):
        return self.role == '@dmin!'
    

    def learning_en(self) -> bool:
        return (self.learning_language or "").startswith("en")

    def learning_pt(self) -> bool:
        return (self.learning_language or "").startswith("pt")