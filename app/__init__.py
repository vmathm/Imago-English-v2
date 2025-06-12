from flask import Flask

def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('../config.py')  

    # Register Blueprints
    from .auth.routes import bp as auth_bp
    app.register_blueprint(auth_bp)
    '''
    from .flashcards.routes import bp as flashcards_bp
    from .progress.routes import bp as progress_bp
    from .dashboard.routes import bp as dashboard_bp
    from .audiobook.routes import bp as audiobook_bp

    
    app.register_blueprint(flashcards_bp)
    app.register_blueprint(progress_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(audiobook_bp)
    '''
    return app