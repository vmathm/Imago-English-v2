from functools import wraps
from flask import render_template, request
from flask_login import current_user, login_required
from app.services.access import sync_internal_access
from app.database import db_session



def active_required(view_func=None, *, template_name="inactive_user.html"):

    def decorator(fn):
        @wraps(fn)
        @login_required
        def wrapped(*args, **kwargs):
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
