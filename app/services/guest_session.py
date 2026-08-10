from datetime import datetime, timedelta, timezone
from uuid import uuid4

from flask import session
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

    Authenticated users do not need a new guest identity.
    """
    if current_user.is_authenticated:
        return None

    guest_id = session.get(GUEST_SESSION_KEY)

    if guest_id is None:
        guest_id = str(uuid4())
        session[GUEST_SESSION_KEY] = guest_id
        session.permanent = True

    return guest_id


def get_or_create_guest_user() -> GuestUser | None:
    """
    Return the database GuestUser belonging to this browser.

    Creates the database row only when this function is called.
    """
    guest_id = ensure_guest_id()

    if guest_id is None:
        return None

    guest_user = db_session.get(GuestUser, guest_id)
    now = utcnow()

    if guest_user is None:
        guest_user = GuestUser(
            id=guest_id,
            created_at=now,
            last_activity_at=now,
            expires_at=now + timedelta(days=GUEST_LIFETIME_DAYS),
            role="student"
        )
        
        db_session.add(guest_user)
    else:
        guest_user.last_activity_at = now
        guest_user.expires_at = now + timedelta(
            days=GUEST_LIFETIME_DAYS
        )
        


    db_session.commit()

    return guest_user