from flask import Blueprint, redirect, url_for

bp = Blueprint("home", __name__)

@bp.route("/", defaults={"user_id": "student123"})
@bp.route("/<user_id>")
def index(user_id):
    return redirect(url_for("auth.dev_login", user_id=user_id))