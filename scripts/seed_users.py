from datetime import date
import os
import sys
from dotenv import load_dotenv
load_dotenv()
# Add the parent directory of 'app/' to the Python path
'''
-  os.path.join(os.path.dirname(__file__) - Returns the directory path where the current script (seed_users.py) lives

- os.path.join(os.path.dirname(__file__), '..') - Joins the above path with '..' to go one level up, which is the root of the project

- os.path.abspath() - Converts the relative path to an absolute path.

- sys.path.append() - Adds the absolute path to the Python path so that modules in the parent directory can be imported.
'''
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.models.user import User
from app.database import db_session

# Common fields
today = date.today()

users = [
    User(
        id="9990",
        name="admin",
        email="admin@example.com",
        google_access_token="fake-admin-token",
        role="@dmin!",
        join_date=today,
        active=True
    ),
    User(
        id="9991",
        name="teacher",
        email="teacher@example.com",
        google_access_token="fake-teacher-token",
        role="teacher",
        join_date=today,
        active=True
    ),

        User(
        id="9996",
        name="ReverendTeacher",
        email="teacher@example.com",
        google_access_token="fake-teacher-token",
        role="teacher",
        join_date=today,
        active=True
    ),

    User(
        id="9992",
        name="Alia",
        email="student@example.com",
        google_access_token="fake-student-token",
        role="student",
        join_date=today,
        active=True
    ),

    User(
        id="9993",
        name="Duncan",
        email="student@example.com",
        google_access_token="fake-student-token",
        role="student",
        join_date=today,
        active=True
    ),

    User(
        id="9994",
        name="MilesTeg",
        email="student@example.com",
        google_access_token="fake-student-token",
        role="student",
        join_date=today,
        active=True
    ),

    User(
        id="9995",
        name="Stilgar",
        email="student@example.com",
        google_access_token="fake-student-token",
        role="student",
        join_date=today,
        active=True
    )
]

# Add and commit
for user in users:
    if not db_session.query(User).filter_by(id=user.id).first():
        db_session.add(user)

db_session.commit()

print("✅ Seeded test users.")