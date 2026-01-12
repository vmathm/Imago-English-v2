from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR / ".env"

# 1. Load .env if it exists
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None
else:
    if ENV_PATH.exists():
        load_dotenv(ENV_PATH)

# 2. Now APP_ENV can come from .env OR real env
env_mode = os.getenv("APP_ENV", "development").lower()

class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY")
    if not SECRET_KEY:
        raise ValueError("No SECRET_KEY set! Set it in the environment.")
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    ALLOW_SEEDED_USERS = os.environ.get("ALLOW_SEEDED_USERS", "false").lower() in ("true", "1", "t")
    GOOGLE_OAUTH_CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    GOOGLE_OAUTH_CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
    GCS_AUDIOBOOK_BUCKET = os.getenv("GCS_AUDIOBOOK_BUCKET")

class DevConfig(Config):
    # Looser cookies for local dev (http://127.0.0.1)
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = False
    REMEMBER_COOKIE_HTTPONLY = True
    ALLOW_SEEDED_USERS =True
    AUTO_CREATE_DB = True

class ProdConfig(Config):
    # Strict cookie flags for production
    SESSION_COOKIE_SECURE = True         # HTTPS only
    SESSION_COOKIE_HTTPONLY = True       # not readable by JS
    SESSION_COOKIE_SAMESITE = "None"      
    REMEMBER_COOKIE_SECURE = True
    REMEMBER_COOKIE_HTTPONLY = True
    ALLOW_SEEDED_USERS =False
    REMEMBER_COOKIE_SAMESITE = "None"
    PREFERRED_URL_SCHEME = "https"
    AUTO_CREATE_DB = False
