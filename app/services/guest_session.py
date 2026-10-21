from datetime import datetime, timedelta, timezone
from uuid import uuid4

from flask import session, g
from flask_login import current_user

from app.database import db_session
from app.models import GuestUser


GUEST_SESSION_KEY = "guest_id"
GUEST_LIFETIME_DAYS = 7


def utcnow():
    return datetime.now(timezone.utc)


def ensure_guest_id() -> str | None:
    """
    Return the current anonymous visitor's guest ID.

    Authenticated users do not need a guest identity.
    """
    if current_user.is_authenticated:
        return None

    session.permanent = True

    guest_id = session.get(GUEST_SESSION_KEY)

    if guest_id is None:
        guest_id = str(uuid4())
        session[GUEST_SESSION_KEY] = guest_id

    return guest_id


def get_or_create_guest_user() -> GuestUser | None:
    """
    Return the current anonymous visitor's GuestUser.

    Creates a new guest workspace if no valid one exists.
    Active guests retain their workspace and receive a
    renewed seven-day expiration.
    """
    guest_id = ensure_guest_id()

    if guest_id is None:
        return None

    now = utcnow()
    guest_user = db_session.get(GuestUser, guest_id)

    if guest_user is not None:
        expires_at = guest_user.expires_at

        # Some databases return naive UTC timestamps.
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if guest_user.is_claimed or expires_at <= now:
            session.pop(GUEST_SESSION_KEY, None)
            guest_user = None

    if guest_user is None:
        guest_id = str(uuid4())
        session[GUEST_SESSION_KEY] = guest_id

        guest_user = GuestUser(
            id=guest_id,
            created_at=now,
            last_activity_at=now,
            expires_at=now + timedelta(
                days=GUEST_LIFETIME_DAYS
            ),
            role="student",
        )

        db_session.add(guest_user)

    else:
        guest_user.last_activity_at = now
        guest_user.expires_at = now + timedelta(
            days=GUEST_LIFETIME_DAYS
        )

    db_session.commit()

    g.guest_user = guest_user

    return guest_user