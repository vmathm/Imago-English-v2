from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix
import os

from config import ProdConfig, DevConfig
from .models.base import Base
from .database import init_engine
from .extensions import login_manager
from .extensions import csrf
from .auth import user_loader
from pathlib import Path
from datetime import timedelta




def create_app():
    # Load .env only outside production, only if the file exists, and only if python-dotenv is installed.
    try:
        env_mode = os.getenv("APP_ENV", "development").lower()
        if env_mode != "production":
            env_path = Path(__file__).resolve().parents[1] / ".env"
            if env_path.exists():
                from dotenv import load_dotenv  # optional dependency
                load_dotenv(env_path)
    except Exception:
        pass

    package_root = Path(__file__).resolve().parent       # -> /app/app
    static_dir = package_root / "static"                 # -> /app/app/static

    app = Flask(__name__, static_folder=str(static_dir), static_url_path="/static")
    env = os.getenv("APP_ENV", "development").lower()
    app.config.from_object(ProdConfig if env == "production" else DevConfig)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
    csrf.init_app(app)
    login_manager.init_app(app)

    app.jinja_env.globals['timedelta'] = timedelta
   
    engine, db_session = init_engine(app)
    Base.metadata.create_all(engine)

      
    if app.config.get("ALLOW_SEEDED_USERS", False):
        try:
            from scripts.seed_users import main as seed_main
            seed_main()
        except Exception as e:
            print("⚠️ Seeding skipped or failed:", e)
    




    from .auth.routes import bp as auth_bp, google_bp
    from .dashboard.routes import bp as dashboard_bp
    from .flashcard.routes import bp as flashcard_bp
    from .home.routes import bp as home_bp
    from .admin.routes import bp as admin_bp
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
    app.register_blueprint(google_bp, url_prefix="/login")
    app.register_blueprint(staticpages_bp)
   
    return app  
