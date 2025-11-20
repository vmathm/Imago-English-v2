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

    # Admin user
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

        # Teachers
    for i in range(5):
        p = random.randint(50, 500)        # current points
        s = random.randint(0, 30)          # current streak
        max_s = max(s, s + random.randint(0, 10))
        fc_studied = random.randint(150, 600) + p // 3 + s * 2

        users.append(
            User(
                id=f"900{i}",
                name=f"teacher{i}",
                user_name=f"u_name_teacher{i}",
                email="vitornorace@gmail.com",
                role="teacher",
                join_date=today,
                active=True,
                points=p,
                study_streak=s,
                max_study_streak=max_s,
                max_points=p * max_s,   # <-- formula
                flashcards_studied=fc_studied
            )
        )
        

    # Students

    dune_names = [ "Paul", "Jessica", "Gurney", "Chani", "Baron", "Feyd", "Irulan",
     "Leto", "Piter", "Thufir", "Jamis", "Rabban", "Mapes", "Wellington", "Korba" ]
    
    
    students = []
    for i, name in enumerate(dune_names):
        p = random.randint(50, 1000)
        s = random.randint(0, 50)
        max_s = max(s, s + random.randint(0, 15))
        fc_studied = random.randint(50, 1000) + p // 2 + s * 3
        
        student = User(
            id=f"800{i}",
            name=name,
            email=f"{name.lower()}@example.com",
            role="student",
            join_date=today,
            active=True,
            points=p,
            study_streak=s,
            max_study_streak=max_s,
            max_points=p * max_s,   
            flashcards_studied=fc_studied
        )
        users.append(student)
        students.append(student)


    # Commit users
    for user in users:
        if not db_session.query(User).filter_by(id=user.id).first():
            db_session.add(user)

    db_session.commit()

    # Fixed flashcards for students
    dune_lore_map = {
    "Desert": "Deserto",
    "Sand": "Areia",
    "Worm": "Verme",
    "Spice": "Especiaria",
    "Water": "Água",
    "Life": "Vida",
    "Planet": "Planeta",
    "Wind": "Vento",
    "Battle": "Batalha",
    "Dream": "Sonho",
    "Fear": "Medo",
    "Voice": "Voz",
    "Mind": "Mente",
    "Power": "Poder",
    "Prophecy": "Profecia",
    "Faith": "Fé",
    "Tribe": "Tribo",
    "Leader": "Líder",
    "Destiny": "Destino"
    }


    for student in students:
        for eng_term, pt_term in dune_lore_map.items():
            flashcard = Flashcard(
                user_id=student.id,
                question=pt_term,   # Portuguese term
                answer=eng_term,    # English term
                next_review=today,
                created_at=today
            )
            db_session.add(flashcard)

    db_session.commit()

    print("✅ Seeded admin, 5 teachers, 15 students, and 10 fixed flashcards each.")


if __name__ == "__main__":
    main()