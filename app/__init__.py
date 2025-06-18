from flask import Flask
from dotenv import load_dotenv
from flask_login import LoginManager
import os

from config import Config
from .models.base import Base
from .database import init_engine

login_manager = LoginManager()

def create_app():
    # Load environment variables from .env file
    load_dotenv()

    app = Flask(__name__)
    login_manager.init_app(app)

    # Dynamically load config based on FLASK_CONFIG env variable
    app.config.from_object("config.Config")
    
   # Initialize DB
    engine, db_session = init_engine(app)
    Base.metadata.create_all(engine)


    

    # Register blueprints
    from .auth.routes import bp as auth_bp
    app.register_blueprint(auth_bp)
    

    '''
    from .flashcards.routes import bp as flashcards_bp
    from .progress.routes import bp as progress_bp
   
    from .audiobook.routes import bp as audiobook_bp

    
    app.register_blueprint(flashcards_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(audiobook_bp)
    '''

    return app  
