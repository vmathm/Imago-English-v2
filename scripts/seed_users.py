from datetime import date
import os
import sys
import random
from dotenv import load_dotenv
load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.user import User
from app.database import db_session

today = date.today()

# Keep existing admin
users = [
    User(
        id="9990",
        name="admin",
        email="admin@example.com",
        role="@dmin!",
        join_date=today,
        active=True
    )
]

# Create 5 teachers
for i in range(5):
    users.append(
        User(
            id=f"900{i}",
            name=f"teacher{i}",
            user_name=f"u_name_teacher{i}",
            email=f"vitornorace@gmail.com",
            role="teacher",
            join_date=today,
            active=True,
            points=random.randint(50, 500),
            max_points=random.randint(50, 500),
            study_streak=random.randint(0, 30),
            study_max_streak=random.randint(5, 60)
        )
    )

# Dune character names
dune_names = [
    "Paul", "Jessica", "Gurney", "Chani", "Baron",
    "Feyd", "Irulan", "Leto", "Piter", "Thufir",
    "Jamis", "Rabban", "Mapes", "Wellington", "Korba"
]

# Create 15 students
for i, name in enumerate(dune_names):
    users.append(
        User(
            id=f"800{i}",
            name=name,
            email=f"{name.lower()}@example.com",
            role="student",
            join_date=today,
            active=True,
            points=random.randint(50, 1000),
            max_points=random.randint(50, 1000),
            study_streak=random.randint(0, 50),
            study_max_streak=random.randint(5, 100)
        )
    )

# Add and commit if not already in DB
for user in users:
    if not db_session.query(User).filter_by(id=user.id).first():
        db_session.add(user)

db_session.commit()

print("✅ Seeded admin, 5 teachers, and 15 students with random leaderboard data.")
