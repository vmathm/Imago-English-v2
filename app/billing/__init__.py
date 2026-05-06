from flask import Blueprint

bp = Blueprint("billing", __name__, url_prefix="/billing")

from app.billing import routes