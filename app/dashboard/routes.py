from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.flashcard.form import FlashcardForm

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
@login_required
def index():
    form = FlashcardForm()
    return render_template('dashboard.html', form=form)
