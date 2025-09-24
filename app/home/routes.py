from flask import Blueprint, redirect, url_for, current_app

bp = Blueprint("home", __name__)



@bp.route("/", defaults={"user_id": None})
@bp.route("/<user_id>")
def index(user_id):
    if current_app.config["ALLOW_SEEDED_USERS"]:
        return redirect(url_for("auth.demo_login", user_id=user_id))
    else:
        return redirect(url_for("dashboard.index"))