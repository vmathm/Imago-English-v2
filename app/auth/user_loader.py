from app.extensions import login_manager
from app.models.user import User
from app.database import db_session

@login_manager.user_loader
def load_user(user_id):
    return db_session.get(User, user_id)