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
try:
    from app.utils.time import utcnow, now_sp
except Exception as e:
    print("[reset_study_streaks] IMPORT ERROR:", e)
    raise

# Prefer the shared helpers if you created them:
# from app.utils.time import utcnow, now_sp, sp_midnight_as_utc
# But to keep this script self-contained and robust for cron, we define minimal equivalents here.

SP_TZ = ZoneInfo("America/Sao_Paulo")


def now_sp() -> datetime:
    return datetime.now(SP_TZ)


def end_of_day_sp_as_utc(d) -> datetime:
    """
    São Paulo end-of-day for date d (23:59:59.999999 SP), converted to UTC (aware).
    Used as the cutoff to answer: "was this card due at any time yesterday?"
    """
    end_sp = datetime.combine(d, time.max, tzinfo=SP_TZ)
    return end_sp.astimezone(timezone.utc)


def reset_study_streaks():
    sp_now = now_sp()
    utc_now = sp_now.astimezone(timezone.utc)

    today_sp = sp_now.date()
    yesterday_sp = today_sp - timedelta(days=1)

    cutoff_utc = end_of_day_sp_as_utc(yesterday_sp)

    print(
        f"[reset_study_streaks] RUN | now_sp={sp_now.isoformat()} | "
        f"now_utc={utc_now.isoformat()} | yesterday_sp={yesterday_sp.isoformat()} | "
        f"cutoff_utc(end_of_yesterday_sp)={cutoff_utc.isoformat()}"
    )

    reset_count = 0

    try:
        # If your user table is large later, you can filter here.
        # For now this is fine.
        users = db_session.query(User).all()

        for user in users:
            # If they studied yesterday or today, we do not reset.
            last = user.streak_last_date  # DATE (São Paulo local date)
            missed_day = last not in (yesterday_sp, today_sp)

            # Only bother checking due cards if they actually have a streak.
            has_streak = (user.study_streak or 0) > 0
            if not (missed_day and has_streak):
                continue

            # "Had due yesterday" means: by the end of yesterday SP (converted to UTC),
            # the user had at least one card that existed and was due.
            #
            # Since timestamps are stored as UTC-aware, compare in UTC-aware instants.
            had_due_yesterday = db_session.query(
                exists().where(
                    Flashcard.user_id == user.id,
                    Flashcard.created_at <= cutoff_utc,
                    or_(
                        Flashcard.next_review.is_(None),
                        Flashcard.next_review <= cutoff_utc,
                    ),
                )
            ).scalar()

            if missed_day and had_due_yesterday and has_streak:
                reset_count += 1
                print(
                    f"[RESET] user_id={user.id} | name={getattr(user, 'name', None)!r} | "
                    f"study_streak_before={user.study_streak} | streak_last_date={user.streak_last_date} | "
                    f"reason=missed_day_and_had_due_cards_yesterday"
                )
                print(
                    f"        details: missed_day={missed_day} (expected {yesterday_sp} or {today_sp}), "
                    f"had_due_yesterday={had_due_yesterday}, cutoff_utc={cutoff_utc.isoformat()}"
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
