from flask import Flask, g
from werkzeug.middleware.proxy_fix import ProxyFix
import os

from config import DemoConfig, ProdConfig, DevConfig
from .models.base import Base
from .database import init_engine
from .extensions import login_manager
from .extensions import csrf
from .auth import user_loader
from .auth.guest_loader import load_guest_user
from pathlib import Path
from datetime import timedelta


def create_app():

    package_root = Path(__file__).resolve().parent       # -> /app/app
    static_dir = package_root / "static"                 # -> /app/app/static

    app = Flask(
        __name__,
        static_folder=str(static_dir),
        static_url_path="/static"
    )

    env = os.getenv("APP_ENV", "development").lower()

    if env == "production":
        app.config.from_object(ProdConfig)
    elif env == "demo":
        app.config.from_object(DemoConfig)
    else:
        app.config.from_object(DevConfig)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    csrf.init_app(app)
    login_manager.init_app(app)

    app.jinja_env.globals["timedelta"] = timedelta

    engine, db_session = init_engine(app)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db_session.remove()

    if app.config.get("AUTO_CREATE_DB"):
        Base.metadata.create_all(engine)

    if app.config.get("ALLOW_SEEDED_USERS", False):
        try:
            from scripts.seed_users import main as seed_main
            seed_main()
        except Exception as e:
            print("⚠️ Seeding skipped or failed:", e)

    # Load a valid guest user from the session for every request.
    @app.before_request
    def load_current_guest():
        load_guest_user()

    # Make guest_user automatically available in all Jinja templates.
    @app.context_processor
    def inject_guest_user():
        return {
            "guest_user": getattr(g, "guest_user", None)
        }


    @app.context_processor
    def inject_library_availability():
        from flask_login import current_user
        from app.models import Book

        library_available = False

        if (
            current_user.is_authenticated
            and current_user.role == "student"
            and current_user.level
        ):
            library_available = (
                db_session.query(Book.id)
                .filter(Book.level == current_user.level)
                .first()
                is not None
            )

        return {
            "library_available": library_available
        }


    

    from .auth.routes import bp as auth_bp, google_bp
    from .dashboard.routes import bp as dashboard_bp
    from .flashcard.routes import bp as flashcard_bp
    from .home.routes import bp as home_bp
    from .admin.routes import bp as admin_bp
    from .billing import bp as billing_bp
    from .audiobook.routes import bp as audiobook_bp
    from .progress.routes import bp as progress_bp
    from .calendar.routes import bp as calendar_bp
    from .staticpages.routes import bp as staticpages_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(flashcard_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(audiobook_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(calendar_bp)
    app.register_blueprint(google_bp, url_prefix="/auth")
    app.register_blueprint(staticpages_bp)
    app.register_blueprint(billing_bp)

    return app