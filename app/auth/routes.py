from datetime import datetime, timedelta, date
from flask import Blueprint, redirect, abort, current_app, request, url_for, session, render_template
from flask_login import login_user, logout_user
from app.utils.time import SP_TZ
from app.models import User
from app.database import db_session
from flask_dance.contrib.google import make_google_blueprint, google
from app.services.google_auth import get_google_user_info
from app.services.access import sync_internal_access
from urllib.parse import urlparse, urljoin
import os


bp = Blueprint("auth", __name__, url_prefix="/auth")


def is_safe_url(target: str) -> bool:
    if not target:
        return False

    host_url = urlparse(request.host_url)
    redirect_url = urlparse(urljoin(request.host_url, target))

    return (
        redirect_url.scheme in ("http", "https")
        and host_url.netloc == redirect_url.netloc
    )


def is_allowed_post_login_target(target: str) -> bool:
    """
    Prevent redirecting back into auth endpoints that can loop or log the user out.
    """
    if not target or not is_safe_url(target):
        return False

    blocked_paths = {
        url_for("auth.login"),
        url_for("auth.logout"),
        url_for("auth.demo_login"),
    }

    parsed = urlparse(urljoin(request.host_url, target))
    return parsed.path not in blocked_paths


google_bp = make_google_blueprint(
    client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
    scope=[
        "openid",
        "https://www.googleapis.com/auth/userinfo.email",
        "https://www.googleapis.com/auth/userinfo.profile",
    ],
    redirect_url="/auth/login/google/complete",
)


@bp.route("/demo_login/", defaults={"user_id": None})
@bp.route("/demo_login/<user_id>")
def demo_login(user_id):
    logout_user()

    if not current_app.config.get("ALLOW_SEEDED_USERS", False):
        abort(403)

    if not user_id:
        return render_template("demo_login.html")

    user = db_session.query(User).filter_by(id=user_id).first()
    if not user:
        return render_template("demo_login.html")
    
    sync_internal_access(user)
    db_session.commit()

    success = login_user(user, force=True)
    print(f"Demo login {'successful' if success else 'failed'} for user: {user_id}")

    return redirect(url_for("dashboard.index"))


@bp.route("/login/google")
def login():
    """
    Start Google OAuth flow.

    Only trust an explicit ?next=... parameter.
    Do not use request.referrer, because it can easily point to /auth/demo_login
    or another auth route and create loops / accidental logout.
    """
    next_url = request.args.get("next")

    if next_url and is_allowed_post_login_target(next_url):
        session["post_login_redirect"] = next_url
    else:
        session.pop("post_login_redirect", None)

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
    is_new_user = False

    forced_join_date = session.pop("forced_join_date", None)

    join_date = (
        date.fromisoformat(forced_join_date)
        if forced_join_date
        else datetime.now(SP_TZ).date()
    )

    if not user:
        user = User(
            id=google_id,
            email=email,
            name=name,
            user_name=email.split("@")[0],
            role="student",
            profilepic=info.get("picture", "none"),
            learning_language="en",
            join_date=join_date,
        )
        db_session.add(user)
        is_new_user = True
    else:
        if not user.user_name:
            user.user_name = email.split("@")[0]
        user.name = name
        user.profilepic = info.get("picture", "none")

    pending_teacher_id = session.pop("pending_teacher_id", None)
    pending_activation = session.pop("pending_activation", False)
    billing_mode = session.pop("billing_mode", "external")

    # Persist billing mode for brand-new users.
    # For existing users, only set it if the field is empty / missing.
    if hasattr(user, "billing_mode"):
        if is_new_user:
            user.billing_mode = billing_mode
        elif not getattr(user, "billing_mode", None):
            user.billing_mode = billing_mode

    if pending_teacher_id and user.role == "student":
        teacher = (
            db_session.query(User)
            .filter_by(id=pending_teacher_id, role="teacher")
            .first()
        )

        if teacher and not user.assigned_teacher_id:
            user.assigned_teacher_id = teacher.id

    if pending_activation and is_new_user:
        user.active = True


    sync_internal_access(user)
    db_session.commit()

    login_user(user, remember=True)
    session.modified = True

    target = session.pop("post_login_redirect", None)
    if not is_allowed_post_login_target(target):
        target = url_for("dashboard.index")

    return redirect(target)


@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("home.index"))


@bp.route("/join/<user_name>")
def join_teacher(user_name):
    teacher = (
        db_session.query(User)
        .filter_by(user_name=user_name, role="teacher")
        .first()
    )

    if not teacher:
        abort(404)

    session["pending_teacher_id"] = teacher.id
    session["pending_activation"] = True
    session["billing_mode"] = "external"

    return redirect(url_for("auth.login"))


@bp.route("/join_trial")
def join_trial():
    session.pop("pending_teacher_id", None)
    session["pending_activation"] = True
    session["billing_mode"] = "internal"

    return redirect(url_for("auth.login"))


@bp.route("/join_trial_expired")
def join_trial_expired():

    vitor = db_session.query(User).filter_by(user_name="Vitor").first()

    if vitor:
        session["pending_teacher_id"] = vitor.id

    session["pending_activation"] = True
    session["billing_mode"] = "internal"

    # Expired 7-day trial using São Paulo date
    expired_date = (
        datetime.now(SP_TZ).date() - timedelta(days=8)
    )

    session["forced_join_date"] = expired_date.isoformat()

    return redirect(url_for("auth.login"))