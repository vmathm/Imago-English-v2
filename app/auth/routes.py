from flask import Blueprint, redirect, url_for, abort, current_app
from flask_login import login_user
from app.models import User
from app.database import db_session




bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/test')
def test():
    return "Auth route is working!"


@bp.route('/dev-login/<user_id>')
def dev_login(user_id):
    print("Attempting dev login for user:", user_id)
    # Secure: Only allowed in debug mode AND if explicitly enabled
    if not (current_app.config.get("ALLOW_DEV_LOGIN", False) and current_app.debug):
        abort(403)

    user = db_session.query(User).filter_by(id=user_id).first()
    if not user:
        print("User not found:", user_id)
        abort(404)

    login_user(user)
    print("User logged in:", user_id)
    return redirect("/dashboard")   