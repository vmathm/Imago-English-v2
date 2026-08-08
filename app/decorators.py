from functools import wraps

from flask import render_template
from flask_login import current_user

from app.database import db_session
from app.services.access import sync_internal_access


def active_required(view_func=None, *, template_name="inactive_user.html"):

    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            # Anonymous visitors are allowed through.
            # The route itself decides whether to create/use guest data.
            if not current_user.is_authenticated:
                return fn(*args, **kwargs)

            # From here onward, current_user is a real User.
            if current_user.billing_mode == "internal":
                sync_internal_access(current_user)
                db_session.commit()

            if not current_user.active:
                return render_template(template_name), 403

            return fn(*args, **kwargs)

        return wrapped

    if view_func is None:
        return decorator

    return decorator(view_func)