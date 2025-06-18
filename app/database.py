from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import current_app
import os



DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///app.db")
engine = create_engine(DATABASE_URL, echo=False)
db_session = scoped_session(sessionmaker(bind=engine))

# This function lets you initialize the engine with the app config
def init_engine(app):
   
    return engine, db_session
