import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))

from datetime import datetime, timedelta, time, timezone
from zoneinfo import ZoneInfo
from sqlalchemy import or_, exists

from app import create_app
from app.database import db_session
from app.models import User, Flashcard


def reset_study_streaks():
    tz_sp = ZoneInfo("America/Sao_Paulo")

    now_sp = datetime.now(tz_sp)
    now_utc = now_sp.astimezone(timezone.utc)

    today_sp = now_sp.date()
    yesterday_sp = today_sp - timedelta(days=1)

    # End of "yesterday" in São Paulo time (23:59:59.999999)
    end_of_yesterday_sp = datetime.combine(yesterday_sp, time.max, tzinfo=tz_sp)

    # Convert to UTC because DB timestamps (created_at / next_review) are UTC
    end_of_yesterday_utc = end_of_yesterday_sp.astimezone(timezone.utc)

    print(
        f"[reset_study_streaks] RUN | now_sp={now_sp.isoformat()} | "
        f"now_utc={now_utc.isoformat()} | yesterday_sp={yesterday_sp.isoformat()} | "
        f"end_of_yesterday_utc={end_of_yesterday_utc.isoformat()}"
    )

    reset_count = 0

    try:
        users = db_session.query(User).all()

        for user in users:
            # Condition A: user did NOT study yesterday (or today)
            # If they studied today already, we don't want to reset.
            missed_day = user.streak_last_date not in (yesterday_sp, today_sp)

            # Condition B: user HAD at least one card that was due "yesterday"
            # - it existed by end of yesterday (created_at <= cutoff)
            # - and next_review is NULL or <= cutoff
            had_due_yesterday = db_session.query(
                exists().where(
                    Flashcard.user_id == user.id,
                    Flashcard.created_at <= end_of_yesterday_utc,
                    or_(
                        Flashcard.next_review.is_(None),
                        Flashcard.next_review <= end_of_yesterday_utc,
                    ),
                )
            ).scalar()

            # Only act if they actually had a streak to reset (optional but cleaner)
            has_streak = (user.study_streak or 0) > 0

            if missed_day and had_due_yesterday and has_streak:
                reset_count += 1

                print(
                    f"[RESET] user_id={user.id} | name={getattr(user, 'name', None)!r} | "
                    f"study_streak_before={user.study_streak} | streak_last_date={user.streak_last_date} | "
                    f"reason=missed_day_and_had_due_cards_yesterday"
                )
                print(
                    f"        details: missed_day={missed_day} (expected {yesterday_sp} or {today_sp}), "
                    f"had_due_yesterday={had_due_yesterday}, cutoff_utc={end_of_yesterday_utc.isoformat()}"
                )

                user.study_streak = 0

        db_session.commit()
        print(f"[reset_study_streaks] DONE | reset_count={reset_count}")

    except Exception as e:
        db_session.rollback()
        print(f"[reset_study_streaks] ERROR | {type(e).__name__}: {e}")
        raise
    finally:
        db_session.remove()


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        reset_study_streaks()
