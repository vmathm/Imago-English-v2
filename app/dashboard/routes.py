import hashlib
from flask import Blueprint, current_app, flash, render_template, redirect, request, url_for
from flask_login import current_user, login_required
from app.flashcard.form import FlashcardForm
from app.models import User            
from app.database import db_session
from app.admin.forms import AssignStudentForm, UnassignStudentForm, ChangeRoleForm, DeleteUserForm, ToggleActiveStatusForm, ChangeStudentLevelForm, UpdateLearningLanguageForm
from app.models.flashcard import Flashcard 
from sqlalchemy import func, or_
from datetime import datetime, timedelta, timezone
from app.audiobook.forms import UserAudiobookForm, UsernameForm




bp = Blueprint('dashboard', __name__, url_prefix='/dashboard')



def get_teacher_data():
    change_student_level_form = ChangeStudentLevelForm()
    audiobook_form = UserAudiobookForm()
    update_learning_language_form = UpdateLearningLanguageForm()
    assigned = list(current_user.assigned_students)
    student_ids = [s.id for s in assigned]

    
    unreviewed = (
        db_session.query(Flashcard.user_id, func.count(Flashcard.id))
        .filter(Flashcard.reviewed_by_tc.is_(False))
        .group_by(Flashcard.user_id)
        .all()
    )
    unreviewed_counts = {user_id: cnt for user_id, cnt in unreviewed}

    
    needs_review = [s for s in assigned if unreviewed_counts.get(s.id, 0) > 0]
    cleared = [s for s in assigned if unreviewed_counts.get(s.id, 0) == 0]

    
    needs_review.sort(key=lambda s: (s.name or "").lower())
    cleared.sort(key=lambda s: (s.name or "").lower())

    
    ordered_students = needs_review + cleared

    return {
        "assigned_students": ordered_students,
        "change_student_level_form": change_student_level_form,
        "unreviewed_counts": unreviewed_counts,
        "audiobook_form": audiobook_form,
        "update_learning_language_form": update_learning_language_form
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


@bp.route('/')
def index():
    if not current_user.is_authenticated:
        print("User not authenticated, rendering dashboard without user data.")
        return render_template('dashboard.html')
    
    user_name_form = UsernameForm()

    if current_user.user_name:
        suggested_username = current_user.user_name
    else:   
        suggested_username = current_user.email.split("@")[0]

    user_name_form = UsernameForm(data={"user_name": suggested_username})
    
    

    total_flashcards = db_session.query(func.count(Flashcard.id)).filter_by(user_id=current_user.id).scalar()

    due_flashcards = db_session.query(func.count(Flashcard.id)).filter(
            Flashcard.user_id == current_user.id,
            or_(
                Flashcard.next_review == None,
                Flashcard.next_review <= datetime.now(timezone.utc) - timedelta(hours=3)
            )
        ).scalar()

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
        "change_student_level_form": None,
        "total_flashcards": total_flashcards,
        "due_flashcards": due_flashcards,
        "user_name_form": user_name_form,
        "suggested_username": suggested_username
    }

    if current_user.is_teacher():
        context.update(get_teacher_data())

    if current_user.is_admin():
        context.update(get_admin_data())

    return render_template('dashboard.html', **context)


@bp.route("/set_username", methods=["POST"])
@login_required
def set_username():
    user_name_form = UsernameForm()

    if user_name_form.validate_on_submit():
        desired_name = user_name_form.user_name.data.strip()

       
        existing = (
            db_session.query(User)
            .filter(
                User.user_name == desired_name,
                User.id != current_user.id  
            )
            .first()
        )

        if existing:
            flash("Este nome de usuário já está em uso. Por favor, escolha outro.", "danger")
            return redirect(url_for("dashboard.index"))

       
        current_user.user_name = desired_name
        db_session.commit()
        flash("Nome de usuário salvo com sucesso!", "success")
    else:
        
        for field, errors in user_name_form.errors.items():
            for error in errors:
                flash(error, "danger")

    return redirect(url_for("dashboard.index"))