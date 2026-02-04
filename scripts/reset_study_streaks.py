import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from datetime import datetime, timedelta, time, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import and_, or_

from app import create_app
from app.database import db_session
from app.models import User, Flashcard


def reset_study_streaks():
    tz_sp = ZoneInfo("America/Sao_Paulo")

    now_sp = datetime.now(tz_sp)
    today = now_sp.date()
    yesterday = today - timedelta(days=1)

    # end of yesterday in São Paulo time
    end_of_yesterday_sp = datetime.combine(yesterday, time.max, tzinfo=tz_sp)

    # convert to UTC for comparing with UTC timestamps in DB
    end_of_yesterday_utc = end_of_yesterday_sp.astimezone(timezone.utc)

    try:
        users = db_session.query(User).all()

        for user in users:
            had_due_yesterday = db_session.query(Flashcard.id).filter(
                Flashcard.user_id == user.id,
                Flashcard.created_at <= end_of_yesterday_utc,
                or_(
                    Flashcard.next_review.is_(None),
                    Flashcard.next_review <= end_of_yesterday_utc,
                )
            ).first() is not None

            missed_day = user.streak_last_date not in (yesterday, today)

            if missed_day and had_due_yesterday:
                user.study_streak = 0

        db_session.commit()

    except Exception:
        db_session.rollback()
        raise
    finally:
        db_session.remove()


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        reset_study_streaks()



    """
    Study streak reset logic (important):

    A user's study streak is reset ONLY if all conditions below are met:

    1) The user DID NOT study yesterday.
       - This is determined by `streak_last_date`.
       - Studying all available cards at least once during a day protects the streak,
         regardless of new cards due.

    2) The user HAD at least one flashcard that was genuinely due yesterday.
       A flashcard counts as "due yesterday" if:
         - It already existed by the end of yesterday (created_at <= end_of_yesterday_utc)
         - AND (
             - next_review IS NULL   (new / never scheduled cards are considered due)
             - OR next_review <= end_of_yesterday_utc
           )

    Why this matters:
    - Cards created today MUST NOT break yesterday’s streak.
    - New cards (next_review = NULL) SHOULD count as due,
      but only if they already existed yesterday.
    - Streaks are day-based, not card-based:
      studying once per day is enough to preserve the streak.

    This logic ensures fairness:
    - Users are not punished for cards they had no chance to study.
    - Users cannot keep a streak alive while ignoring due cards for a full day.
    """
