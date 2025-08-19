# app/dashboard/routes.py
from flask import Blueprint, render_template, redirect, url_for, abort
from flask_login import current_user
from app.flashcard.form import FlashcardForm
from app.models import User            
from app.database import db_session
from app.admin.forms import AssignStudentForm, UnassignStudentForm, ChangeRoleForm, DeleteUserForm, ToggleActiveStatusForm, ChangeStudentLevelForm
from app.models.flashcard import Flashcard 
from sqlalchemy import func



bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')



# Modular helper functions

def get_teacher_data():
    change_student_level_form = ChangeStudentLevelForm()

    assigned = list(current_user.assigned_students)
    student_ids = [s.id for s in assigned]

    
    unreviewed = (
        db_session.query(Flashcard.user_id, func.count(Flashcard.id))
        .filter(Flashcard.reviewed_by_tc.is_(False))
        .group_by(Flashcard.user_id)
        .all()
    )
    unreviewed_counts = {user_id: cnt for user_id, cnt in unreviewed}

    return {
        "assigned_students": assigned,
        "change_student_level_form": change_student_level_form,
        "unreviewed_counts": unreviewed_counts,
    }

def get_admin_data():
    assign_form = AssignStudentForm()
    unassign_form = UnassignStudentForm()
    change_role_form = ChangeRoleForm()
    delete_user_form = DeleteUserForm()
    toggle_active_status_form = ToggleActiveStatusForm()
    change_student_level_form = ChangeStudentLevelForm()

    all_users = db_session.query(User).all()
    teachers = db_session.query(User).filter_by(role='teacher').all()
    unassigned_students = db_session.query(User).filter(
        User.role == 'student', User.assigned_teacher_id.is_(None)
    ).all()
    assigned_students_admin = db_session.query(User).filter(
        User.role == 'student', User.assigned_teacher_id.isnot(None)
    ).all()

    # Populate form choices
    assign_form.student_id.choices = [(s.id, f"{s.name} ({s.email}) | ID: {s.id}") for s in unassigned_students]
    assign_form.teacher_id.choices = [(t.id, f"{t.name} ({t.email}) | ID: {t.id}") for t in teachers]
    unassign_form.student_id.choices = [(s.id, f"{s.name} ({s.email}) | Teacher: {s.assigned_teacher.name}") for s in assigned_students_admin]
    change_role_form.user_id.choices = [(u.id, f"{u.name} ({u.email}) | role: {u.role} | ID: {u.id}") for u in all_users]
    delete_user_form.user_id.choices = [(u.id, f"{u.name} ({u.email}) | ID: {u.id}") for u in all_users]
    toggle_active_status_form.user_id.choices = [(u.id, f"{u.name} ({u.email}) | status: {'Active' if u.active else 'Inactive'} | ID: {u.id}") for u in all_users]
    return {
        "assign_form": assign_form,
        "unassign_form": unassign_form,
        "change_role_form": change_role_form,
        "all_users": all_users,
        "teachers": teachers,
        "unassigned_students": unassigned_students,
        "assigned_students_admin": assigned_students_admin,
        "change_role_form": change_role_form,
        "delete_user_form": delete_user_form,
        "toggle_active_status_form": toggle_active_status_form
    }

# ──────────────────────────────────────────────
# Dashboard route
# ──────────────────────────────────────────────

@bp.route('/')
def index():
    if not current_user.is_authenticated:
        return render_template('dashboard.html')
    context = {
        "form": FlashcardForm(),
        "assigned_students": [],
        "all_users": [],
        "teachers": [],
        "unassigned_students": [],
        "assigned_students_admin": [],
        "assign_form": None,
        "unassign_form": None,
        "change_role_form": None,
        "toggle_active_status_form": None,
        "change_student_level_form": None
    }

    if current_user.is_teacher():
        context.update(get_teacher_data())

    if current_user.is_admin():
        context.update(get_admin_data())
        

    return render_template('dashboard.html', **context)


