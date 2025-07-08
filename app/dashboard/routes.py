# app/dashboard/routes.py
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.flashcard.form import FlashcardForm
from app.models import User            
from app.database import db_session
from app.admin.forms import AssignStudentForm, UnassignStudentForm, ChangeRoleForm
bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')



# Modular helper functions

def get_teacher_data():
    return {
        "assigned_students": current_user.assigned_students
    }

def get_admin_data():
    assign_form = AssignStudentForm()
    unassign_form = UnassignStudentForm()
    change_role_form = ChangeRoleForm()

    all_users = db_session.query(User).all()
    teachers = db_session.query(User).filter_by(role='teacher').all()
    unassigned_students = db_session.query(User).filter(
        User.role == 'student', User.assigned_teacher_id.is_(None)
    ).all()
    assigned_students_admin = db_session.query(User).filter(
        User.role == 'student', User.assigned_teacher_id.isnot(None)
    ).all()

    # Populate form choices
    assign_form.student_id.choices = [(s.id, f"{s.name} ({s.email})") for s in unassigned_students]
    assign_form.teacher_id.choices = [(t.id, f"{t.name} ({t.email})") for t in teachers]
    unassign_form.student_id.choices = [(s.id, f"{s.name} ({s.email})") for s in assigned_students_admin]
    change_role_form.user_id.choices = [(u.id, f"{u.name} ({u.email})") for u in all_users]
    return {
        "assign_form": assign_form,
        "unassign_form": unassign_form,
        "change_role_form": change_role_form,
        "all_users": all_users,
        "teachers": teachers,
        "unassigned_students": unassigned_students,
        "assigned_students_admin": assigned_students_admin,
        "change_role_form": change_role_form
    }

# ──────────────────────────────────────────────
# Dashboard route
# ──────────────────────────────────────────────

@bp.route('/')
@login_required
def index():
    context = {
        "form": FlashcardForm(),
        "assigned_students": [],
        "all_users": [],
        "teachers": [],
        "unassigned_students": [],
        "assigned_students_admin": [],
        "assign_form": None,
        "unassign_form": None,
        "change_role_form": None
    }

    if current_user.is_teacher():
        context.update(get_teacher_data())

    if current_user.is_admin():
        context.update(get_admin_data())

    return render_template('dashboard.html', **context)