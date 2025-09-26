from datetime import datetime, timezone
import os
import sys
import random
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.user import User
from app.models.flashcard import Flashcard
from app.database import db_session

today = datetime.now(timezone.utc).date()


def main():
    
    if db_session.query(User).count() > 0:
        print("⚠️ Database already has users, skipping seed.")
        return

   
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


    dune_names = [
        "Paul", "Jessica", "Gurney", "Chani", "Baron",
        "Feyd", "Irulan", "Leto", "Piter", "Thufir",
        "Jamis", "Rabban", "Mapes", "Wellington", "Korba"
    ]

    
    students = []
    for i, name in enumerate(dune_names):
        student = User(
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
        users.append(student)
        students.append(student)

   
    for user in users:
        if not db_session.query(User).filter_by(id=user.id).first():
            db_session.add(user)

    db_session.commit()


    dune_lore_map = {
        "Crysknife": "Faca cristal",
        "Sandworm": "Verme da areia",
        "Spice Melange": "Especiaria Melange",
        "Arrakis": "Arrakis",
        "Water of Life": "Água da Vida",
        "Guild Navigator": "Navegador da Guilda",
        "Sietch": "Sietch (abrigo Fremen)",
        "Kanly": "Kanly (vingança formal)",
        "Mentat": "Mentate",
        "Fremen": "Fremen"
    }

    for student in students:
        for eng_term, pt_term in dune_lore_map.items():
            flashcard = Flashcard(
                user_id=student.id,
                question=pt_term,   
                answer=eng_term,   
                next_review=today,
                created_at=today
            )
            db_session.add(flashcard)

    db_session.commit()

    print("✅ Seeded admin, 5 teachers, 15 students, and 10 fixed flashcards each (PT → EN Dune Lore).")


if __name__ == "__main__":
    main()
