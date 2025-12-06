from flask import Blueprint, redirect, abort, current_app, url_for, session, render_template
from flask_login import login_user, logout_user
from app.models import User
from app.database import db_session
from flask_dance.contrib.google import make_google_blueprint, google
from app.services.google_auth import get_google_user_info 
import os



bp = Blueprint('auth', __name__, url_prefix='/auth')


google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ],
    redirect_url="/auth/login/google/complete"
)


@bp.route('/demo_login/', defaults={"user_id": None})
@bp.route('/demo_login/<user_id>')
def demo_login(user_id):
    logout_user()
    

    if not current_app.config.get("ALLOW_SEEDED_USERS", False):
        abort(403)

    if not user_id:
        return render_template("demo_login.html")
    
    user = db_session.query(User).filter_by(id=user_id).first()
    if not user:
        return render_template("demo_login.html")

    if login_user(user):
        print("Demo login successful for user:", user_id)
    else:
        print("Demo login failed for user:", user_id)
    return redirect("/dashboard")



@bp.route("/login/google")
def login():
    return redirect(url_for("google.login"))



@bp.route("/login/google/complete")
def google_complete():
    
    if not google.authorized:
        print("Google authorized:", google.authorized)
        return f"Not authorized. Session: {session}", 403

   
    info = get_google_user_info()

    email = info["email"]
    name = info.get("name", "No Name")
    id = info["id"]
    user = db_session.query(User).filter_by(email=email).first()
    if not user:
        user = User(
            id=id,
            email=email,
            name=name,
            user_name=email.split("@")[0],
            role="student",
            profilepic=info.get("picture", "none"),
            learning_language="en"
        )
        db_session.add(user)  # only here

    else:
        if user.user_name is None:
            user.user_name = email.split("@")[0]
        user.name = name
        user.profilepic = info.get("picture", "none")

    db_session.commit()

    login_user(user, force=True)
    return redirect("/dashboard")


@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home.index"))