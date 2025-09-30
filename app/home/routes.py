from flask import Blueprint, abort, redirect, url_for, current_app
from flask_login import current_user
from app.models import User

bp = Blueprint("home", __name__)



@bp.route("/", defaults={"user_id": None})
@bp.route("/<user_id>")
def index(user_id):

    if user_id is None:
        if current_user.is_authenticated:
            return redirect(url_for("dashboard.index"))
    
        if current_app.config["ALLOW_SEEDED_USERS"]:
            return redirect(url_for("auth.demo_login"))
    else:
        if not current_app.config["ALLOW_SEEDED_USERS"]:
            abort(403)
        return redirect(url_for("auth.demo_login", user_id=user_id))

        