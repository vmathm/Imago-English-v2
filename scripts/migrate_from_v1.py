import os, sys
from dotenv import load_dotenv

# ensure correct imports and environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

import sqlite3
from datetime import datetime, date, timezone
from app import create_app
from app.database import db_session
from app.models import User, Flashcard

OLD_DB_PATH = "old_imago.db"  # your v1 dump loaded here

app = create_app()

def map_role(v1_role: str | None) -> str:
    if not v1_role:
        return "student"
    r = v1_role.strip()
    if r == "tc":
        return "teacher"
    if r == "master!":
        return "@dmin!"
    return r  # already something like 'student' / 'teacher'

def to_date(d):
    if not d:
        return None
    if isinstance(d, date) and not isinstance(d, datetime):
        return d
    # accept 'YYYY-MM-DD'
    try:
        return datetime.strptime(str(d)[:10], "%Y-%m-%d").date()
    except Exception:
        return None

from datetime import datetime, date, timezone

def to_dt(value):
    """
    Convert various timestamp representations to an aware UTC datetime.
    Accepts:
      - datetime (naive or aware)
      - date (set to 00:00:00)
      - ISO strings (with 'T'/'Z'/'±HH:MM' offsets)
      - SQLite-ish strings: 'YYYY-MM-DD HH:MM:SS[.ffffff]'
      - 'YYYY-MM-DD' (date-only)
      - UNIX epoch (int/float seconds)
    Returns None on failure.
    """
    if not value:
        return None

    # Already datetime
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)

    # Date only
    if isinstance(value, date):
        return datetime(value.year, value.month, value.day, tzinfo=timezone.utc)

    # Epoch seconds?
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except Exception:
            pass

    s = str(value).strip()
    if not s:
        return None

    # Normalize common variants
    s_norm = s.replace("T", " ")  # ISO to space
    s_norm = s_norm.replace("Z", "+00:00")  # Zulu to explicit offset

    # 1) Try ISO first
    try:
        dt = datetime.fromisoformat(s_norm)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception:
        pass

    # 2) Try explicit format list (no slicing!)
    fmts = [
        "%Y-%m-%d %H:%M:%S.%f%z",
        "%Y-%m-%d %H:%M:%S%z",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",  # date-only
    ]
    for fmt in fmts:
        try:
            dt = datetime.strptime(s_norm, fmt)
            if dt.tzinfo:
                return dt.astimezone(timezone.utc)
            # if date-only, time is 00:00
            return dt.replace(tzinfo=timezone.utc)
        except Exception:
            continue

    # Couldn’t parse
    return None


def migrate_users():
    print("🚀 Migrating users (v1.users → v2.users) with role mapping...")
    old = sqlite3.connect(OLD_DB_PATH)
    old.row_factory = sqlite3.Row
    cur = old.cursor()
    cur.execute("SELECT * FROM users")

    count = 0
    for row in cur.fetchall():
        if db_session.get(User, row["id"]):
            continue  # already inserted (re-run safe)

        user = User(
            id=row["id"],
            name=row["name"],
            user_name=row["user_name"],
            email=row["email"],
            phone=row["phone"],
            profilepic=row["profilepic"],
            level=row["level"],
            role=map_role(row["role"]),
            delete_date=to_date(row["delete_date"]),
            user_stripe_id=row["user_stripe_id"],
            join_date=to_date(row["join_date"]),
            last_payment_date=to_date(row["last_payment_date"]),
            active=(row["is_active"] if row["is_active"] is not None else True),
            study_streak=row["study_streak"] or 0,
            max_study_streak=row["study_streak"] or 0,
            streak_last_date=to_date(row["streak_last_date"]),
            points=row["points"] or 0,
            max_points=(row["points"] or 0) * max(1, row["study_streak"] or 0),
            flashcards_studied=row["flashcards_studied"] or 0,
            rate_three_count=row["rate_three_count"] or 0,
            assigned_teacher_id=None,
        )
        db_session.add(user)
        count += 1

    db_session.commit()
    print(f"✅ {count} users migrated.\n")

def migrate_missing_teacher_users():
    """
    v1 has a separate `teachers` table (inherits UserCommon), with:
      - teachers.id           (primary key of Teacher)
      - teachers.user_id      (FK to users.id, unique)
    If a teacher exists only in v1.teachers (not in v1.users dump you inserted), we need a v2.users row for teachers.user_id.
    If it already exists, ensure role normalization and update a couple of fields.
    """
    print("🚀 Ensuring teachers exist in v2.users and normalizing roles...")
    old = sqlite3.connect(OLD_DB_PATH)
    old.row_factory = sqlite3.Row
    cur = old.cursor()
    cur.execute("SELECT * FROM teachers")

    inserted, updated = 0, 0
    for row in cur.fetchall():
        v2_id = row["user_id"] or row["id"]  # prefer the base user id
        target = db_session.get(User, v2_id)

        role = map_role(row["role"])  # likely 'teacher' or '@dmin!' after mapping

        if not target:
            # Create a new v2 user using the teacher's base user_id
            user = User(
                id=v2_id,
                name=row["name"],
                user_name=row["name"],
                email=row["email"],
                phone=row["phone"],
                profilepic=row["profilepic"],
                level=row["level"],
                role=role or "teacher",
                delete_date=to_date(row["delete_date"]),
                user_stripe_id=row["user_stripe_id"],
                join_date=to_date(row["join_date"]),
                last_payment_date=to_date(row["last_payment_date"]),
                active=(row["is_active"] if row["is_active"] is not None else True),
                study_streak=row["study_streak"] or 0,
                max_study_streak=row["study_streak"] or 0,
                streak_last_date=to_date(row["streak_last_date"]),
                points=row["points"] or 0,
                max_points=(row["points"] or 0) * max(1, row["study_streak"] or 0),
                flashcards_studied=row["flashcards_studied"] or 0,
                rate_three_count=row["rate_three_count"] or 0,
                assigned_teacher_id=None,
            )
            db_session.add(user)
            inserted += 1
        else:
            # Update role/fields if needed
            new_role = role or target.role or "teacher"
            target.role = new_role
            # keep existing values if present; fill from teacher row if missing
            target.phone = target.phone or row["phone"]
            target.profilepic = target.profilepic or row["profilepic"]
            target.level = target.level or row["level"]
            updated += 1

    db_session.commit()
    print(f"✅ Teachers ensured in v2.users — inserted: {inserted}, updated: {updated}\n")

def migrate_stcommunication():
    print("🚀 Linking students to teachers...")
    old = sqlite3.connect(OLD_DB_PATH)
    old.row_factory = sqlite3.Row
    cur = old.cursor()
    cur.execute("SELECT * FROM stcommunication")

    linked = 0
    for row in cur.fetchall():
        student = db_session.query(User).filter_by(id=row["user_id"]).first()
        if student:
            student.assigned_teacher_id = row["teacher_id"]
            linked += 1

    db_session.commit()
    print(f"✅ {linked} student–teacher links established.\n")

  

def migrate_flashcards():
    print("🚀 Migrating flashcards...")
    old = sqlite3.connect(OLD_DB_PATH)
    old.row_factory = sqlite3.Row
    cur = old.cursor()
    cur.execute("SELECT * FROM flashcards")

    # Build a fast lookup of teacher/admin IDs from the *v2* DB
    teacher_like_roles = {"teacher", "@dmin!"}
    teacher_ids = {
        u.id for u in db_session.query(User.id, User.role).all()
        if (u.role or "").strip() in teacher_like_roles
    }

    count = 0
    for row in cur.fetchall():
        if db_session.get(Flashcard, row["id"]):
            continue

        owner_id = row["user_id"]
        owner_is_teacher = owner_id in teacher_ids

        card = Flashcard(
            id=row["id"],
            question=row["question"],
            answer=row["answer"],
            identify_language=2,
            part_of_speech=None,
            level=row["level"] or 0,
            ease=row["ease"] or 2.0,
            interval=row["interval"] or 1,
            last_review=to_dt(row["last_review"]),
            next_review=to_dt(row["next_review"]),
            show_answer=(bool(row["show_answer"]) if row["show_answer"] is not None else False),

            # ✅ If the card belongs to a teacher/admin, force True on migration
            reviewed_by_tc=True if owner_is_teacher else bool(row["reviewed_by_tc"]),

            add_by_tc=bool(row["add_by_tc"]),
            add_by_user=bool(row["add_by_user"]),
            created_at=(to_dt(row["last_review"]) or to_dt(row["next_review"]) or datetime.now(timezone.utc)),
            user_id=owner_id,
        )
        db_session.add(card)
        count += 1

    db_session.commit()
    print(f"✅ {count} flashcards migrated.\n")


if __name__ == "__main__":
    with app.app_context():
        migrate_users()                 # 1) users from v1.users with role mapping
        migrate_missing_teacher_users() # 2) ensure teacher users exist from v1.teachers
        migrate_stcommunication()    # 3) wire stcommunication → assigned_teacher_id
        migrate_flashcards()            # 4) cards
        print("🎉 Migration completed successfully.")
