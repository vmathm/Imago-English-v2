from datetime import datetime, timezone

from flask import g, session
from flask_login import current_user

from app.database import db_session
from app.models import GuestUser
from app.services.guest_session import GUEST_SESSION_KEY


def load_guest_user():
    g.guest_user = None

    if current_user.is_authenticated:
        return

    guest_id = session.get(GUEST_SESSION_KEY)

    if not guest_id:
        return

    guest_user = db_session.get(GuestUser, guest_id)

    if not guest_user:
        session.pop(GUEST_SESSION_KEY, None)
        return

    if guest_user.expires_at <= datetime.now(timezone.utc):
        session.pop(GUEST_SESSION_KEY, None)
        return

    g.guest_user = guest_user