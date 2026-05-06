from datetime import timedelta
import os
import sys
import random
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.models.user import User
from app.models.flashcard import Flashcard
from app.database import db_session
from app.utils.time import now_sp


def main():
    today = now_sp().date()

    if db_session.query(User).count() > 0:
        print("⚠️ Database already has users, skipping seed.")
        return

    users = [
        # Admin
        User(
            id="9990",
            name="admin",
            user_name="admin",
            email="admin@example.com",
            role="@dmin!",
            join_date=today,
            active=True,
            learning_language="en",
        ),

        # External users
        User(
            id="external_active",
            email="external_active@test.com",
            name="External Active",
            user_name="external_active",
            role="student",
            billing_mode="external",
            active=True,
            join_date=today,
        ),
        User(
            id="external_inactive",
            email="external_inactive@test.com",
            name="External Inactive",
            user_name="external_inactive",
            role="student",
            billing_mode="external",
            active=False,
            join_date=today,
        ),

        # Internal users
        User(
            id="internal_trial_active",
            email="internal_trial_active@test.com",
            name="Internal Trial Active",
            user_name="internal_trial_active",
            role="student",
            billing_mode="internal",
            active=True,
            join_date=today,
        ),
        User(
            id="internal_trial_expired",
            email="internal_trial_expired@test.com",
            name="Internal Trial Expired",
            user_name="internal_trial_expired",
            role="student",
            billing_mode="internal",
            active=True,  # login logic should deactivate
            join_date=today - timedelta(days=7),
        ),
    ]

    # Teachers
    for i in range(5):
        p = random.randint(50, 500)
        s = random.randint(0, 30)
        max_s = max(s, s + random.randint(0, 10))
        fc_studied = random.randint(150, 600) + p // 3 + s * 2

        users.append(
            User(
                id=f"900{i}",
                name=f"teacher{i}",
                user_name=f"u_name_teacher{i}",
                email="vitornorace@gmail.com",  # for calendar demo
                role="teacher",
                join_date=today,
                active=True,
                points=p,
                study_streak=s,
                max_study_streak=max_s,
                max_points=p * max_s,
                flashcards_studied=fc_studied,
                learning_language="en",
            )
        )

    # Students
    dune_names = [
        "Paul", "Jessica", "Gurney", "Chani", "Baron", "Feyd", "Irulan",
        "Leto", "Piter", "Thufir", "Jamis", "Rabban", "Mapes", "Wellington", "Korba"
    ]

    students = []
    for i, name in enumerate(dune_names):
        p = random.randint(50, 1000)
        s = random.randint(0, 50)
        max_s = max(s, s + random.randint(0, 15))
        fc_studied = random.randint(50, 1000) + p // 2 + s * 3

        student = User(
            id=f"800{i}",
            name=name,
            user_name=name,
            email=f"{name.lower()}@example.com",
            role="student",
            join_date=today,
            active=False,
            points=p,
            study_streak=s,
            max_study_streak=max_s,
            max_points=p * max_s,
            flashcards_studied=fc_studied,
            learning_language="en",
        )

        users.append(student)
        students.append(student)

    # Save users
    for user in users:
        if not db_session.query(User).filter_by(id=user.id).first():
            db_session.add(user)

    db_session.commit()

    # Flashcards
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
        "Destiny": "Destino",
    }

    terms = list(dune_lore_map.items())

    for student in students:
        random.shuffle(terms)
        unreviewed_set = set(terms[:5])

        for eng_term, pt_term in terms:
            flashcard = Flashcard(
                user_id=student.id,
                question=pt_term,
                answer=eng_term,
                next_review=today,
                created_at=today,
                reviewed_by_tc=((eng_term, pt_term) not in unreviewed_set),
            )
            db_session.add(flashcard)

    db_session.commit()

    print("✅ Seeded admin, users, teachers, students, and flashcards.")


if __name__ == "__main__":
    main()