from datetime import datetime
import hashlib
from flask import Blueprint, redirect, abort, current_app, request, url_for, session, render_template
from flask_login import login_user, logout_user, current_user
from app.flashcard.routes import SP_TZ
from app.models import User
from app.database import db_session
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.consumer import oauth_authorized
from app.services.google_auth import get_google_user_info 
from urllib.parse import urlparse, urljoin
import os




bp = Blueprint('auth', __name__, url_prefix='/auth')



def is_safe_url(target: str) -> bool:
    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))
    return (
        redirect_url.scheme in ("http", "https")
        and host_url.netloc == redirect_url.netloc
    )

    

google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile"
    ],
    redirect_url="/auth/login/google/complete")







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
    next_url = request.args.get("next") or request.referrer

    if next_url and is_safe_url(next_url):
        session["post_login_redirect"] = next_url

    return redirect(url_for("google.login"))


@bp.route("/login/google/complete")
def google_complete():
    if not google.authorized:
        return redirect(url_for("auth.login"))

    info = get_google_user_info()

    email = info["email"]
    name = info.get("name", "No Name")
    google_id = info["id"]

    user = db_session.query(User).filter_by(email=email).first()

    if not user:
        user = User(
            id=google_id,
            email=email,
            name=name,
            user_name=email.split("@")[0],
            role="student",
            profilepic=info.get("picture", "none"),
            learning_language="en",
            join_date= datetime.now(SP_TZ).date()
        )
        db_session.add(user)
    else:
        if user.user_name is None:
            user.user_name = email.split("@")[0]
        user.name = name
        user.profilepic = info.get("picture", "none")

    db_session.commit()

    login_user(user, remember=True)
    session.modified = True


    target = session.pop("post_login_redirect", None)
    if not target or not is_safe_url(target):
        target = url_for("dashboard.index")  

    return redirect(target)


@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home.index"))