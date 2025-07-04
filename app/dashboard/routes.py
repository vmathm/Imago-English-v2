from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.flashcard.form import FlashcardForm

bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')

@bp.route('/')
@login_required
def index():
    form = FlashcardForm()
    assigned_students = []
    if current_user.is_teacher():
        assigned_students = current_user.assigned_students
    return render_template('dashboard.html', form=form,
                           assigned_students=assigned_students)
