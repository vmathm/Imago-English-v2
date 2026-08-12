from flask import Blueprint, abort, redirect, url_for, current_app, jsonify, render_template
from flask_login import current_user, logout_user
from app.models import User
from app.services.guest_session import ensure_guest_id
from app.services.guest_session import get_or_create_guest_user
from app.flashcard.form import FlashcardForm
from app.database import db_session

bp = Blueprint("home", __name__)



@bp.route("/", defaults={"user_id": None})
@bp.route("/<user_id>")
def index(user_id):

    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if user_id is None:
        if current_app.config["ALLOW_SEEDED_USERS"]:
            return redirect(url_for("auth.demo_login"))
        
        return redirect(url_for("dashboard.index"))
    else:
        if not current_app.config["ALLOW_SEEDED_USERS"]:
            abort(403)
        return redirect(url_for("auth.demo_login", user_id=user_id))


@bp.route("/guest-test")
def guest_test():
    guest_user = get_or_create_guest_user()

    guest_user.level = "A1"
    db_session.commit()

    return redirect(url_for("dashboard.index"))