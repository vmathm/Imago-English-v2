from sqlalchemy import Column, String, Boolean, Integer, Date, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.hybrid import hybrid_property
from flask_login import UserMixin
from .base import Base

class User(Base, UserMixin):
    __tablename__ = 'users'

    id = Column(String(50), primary_key=True)
    name = Column(String(15), nullable=False)
    user_name = Column(String(20), nullable=True)
    email = Column(String(254), nullable=False, server_default='none')
    phone = Column(String(15), nullable=True)
    profilepic = Column(String(300), nullable=False, server_default='none')
    level = Column(String(2), nullable=True)
    role = Column(String(10), nullable=False)  # 'student', 'teacher', 'admin'

    delete_date = Column(Date, nullable=True)
    user_stripe_id = Column(String(50), nullable=True)
    join_date = Column(Date, nullable=True)
    last_payment_date = Column(Date, nullable=True)

    active = Column(Boolean, nullable=False, default=True)  # replaces is_active
    study_streak = Column(Integer, nullable=True, default=0)
    study_max_streak = Column(Integer, nullable=True, default=0)
    streak_last_date = Column(Date, nullable=True)
    points = Column(Integer, nullable=True, default=0)
    max_points = Column(Integer, nullable=True, default=0)
    flashcards_studied = Column(Integer, nullable=True, default=0)
    flashcards_studied_today = Column(Integer, nullable=True, default=0)
    rate_three_count = Column(Integer, nullable=True, default=0)

    # 🔗 Teacher assignment (self-referencing FK)
    assigned_teacher_id = Column(String(50), ForeignKey('users.id'), nullable=True)
    assigned_teacher = relationship('User', remote_side=[id], backref='assigned_students')

    # 🔗 Relationships to other tables
    flashcards = relationship('Flashcard', back_populates='user')
    calendar_settings = relationship("CalendarSettings", uselist=False, back_populates="teacher")
    

    @property
    def is_active(self):
        return self.active

    # Role helpers
    def is_student(self):
        return self.role in ('teacher', '@dmin!', 'student')

    def is_teacher(self):
        return self.role in ('teacher', '@dmin!')

    def is_admin(self):
        return self.role == '@dmin!'
    