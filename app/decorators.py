from functools import wraps

from flask import redirect, render_template, url_for, g
from flask_login import current_user

from app.database import db_session
from app.services.access import sync_internal_access

def active_required(view_func=None, *, template_name="inactive_user.html"):

    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):

            # Registered user
            if current_user.is_authenticated:
                if current_user.billing_mode == "internal":
                    sync_internal_access(current_user)
                    db_session.commit()

                if not current_user.active:
                    return render_template(template_name), 403

                return fn(*args, **kwargs)

            # Valid guest
            if getattr(g, "guest_user", None):
                return fn(*args, **kwargs)

            # Neither logged-in user nor guest
            return redirect(url_for("auth.login"))

        return wrapped

    if view_func is None:
        return decorator

    return decorator(view_func)


def user_or_guest_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if current_user.is_authenticated:
            return fn(*args, **kwargs)

        if getattr(g, "guest_user", None):
            return fn(*args, **kwargs)

        return redirect(url_for("auth.login"))

    return wrapped