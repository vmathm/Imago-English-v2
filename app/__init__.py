from flask import Flask
from dotenv import load_dotenv
import os

from config import Config
from .models.base import Base
from .database import init_engine
from .extensions import login_manager, csrf
from .auth import user_loader


def create_app():
    # Load environment variables from .env file
    load_dotenv()

    app = Flask(__name__)
    # Dynamically load config based on FLASK_CONFIG env variable
    app.config.from_object("config.Config")
    csrf.init_app(app)
    login_manager.init_app(app)

    
   # Initialize DB
    engine, db_session = init_engine(app)
    Base.metadata.create_all(engine)


    

    # Register blueprints
    from .auth.routes import bp as auth_bp
    from .dashboard.routes import bp as dashboard_bp
    from .flashcard.routes import bp as flashcard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(flashcard_bp)

    '''
    
    from .audiobook.routes import bp as audiobook_bp

    
    app.register_blueprint(flashcards_bp)
    app.register_blueprint(audiobook_bp)
    '''

    return app  
