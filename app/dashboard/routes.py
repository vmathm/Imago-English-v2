from flask import Blueprint, render_template
from flask_login import login_required, current_user

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
@login_required
def index():
    print("current_user:", current_user)
    print("is_authenticated:", current_user.is_authenticated)
    return render_template('dashboard.html')
