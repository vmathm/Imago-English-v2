from flask import Blueprint, request, redirect, url_for, abort, flash
from flask_login import login_required, current_user
from app.models import User, Flashcard
from app.database import db_session
from functools import wraps
from app.admin.forms import (
    AssignStudentForm, 
    UnassignStudentForm, 
    ChangeRoleForm, 
    DeleteUserForm, 
    ToggleActiveStatusForm, 
    ChangeStudentLevelForm
)

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin():
            abort(403)
        return fn(*args, **kwargs)
    return wrapped



@bp.route('/assign_student', methods=['POST'])
@admin_required
def assign_student():
    form = AssignStudentForm()
    form.student_id.choices = [(s.id, s.name) for s in db_session.query(User).filter_by(role='student').all()]
    form.teacher_id.choices = [(t.id, t.name) for t in db_session.query(User).filter_by(role='teacher').all()]

    if form.validate_on_submit():
        student = db_session.query(User).filter_by(id=form.student_id.data, role='student').first()
        teacher = db_session.query(User).filter_by(id=form.teacher_id.data, role='teacher').first()
        if not student or not teacher:
            flash('Invalid selection', 'danger')
            return redirect(url_for('dashboard.index'))

        student.assigned_teacher_id = teacher.id
        db_session.commit()
        flash(f'{student.name} assigned to {teacher.name}', 'success')
    else:
        flash('Invalid form submission', 'danger')

    return redirect(url_for('dashboard.index'))


@bp.route('/unassign_student', methods=['POST'])
@admin_required
def unassign_student():
    form = UnassignStudentForm()
    form.student_id.choices = [(s.id, s.name) for s in db_session.query(User).filter_by(role='student').all()]

    if form.validate_on_submit():
        student = db_session.query(User).filter_by(id=form.student_id.data, role='student').first()
        if not student:
            flash('Invalid student', 'danger')
            return redirect(url_for('dashboard.index'))

        student.assigned_teacher_id = None
        db_session.commit()
        flash(f'{student.name} unassigned', 'success')
    else:
        flash('Invalid form submission', 'danger')

    return redirect(url_for('dashboard.index'))


@bp.route('/change_role', methods=['POST'])
@admin_required
def change_role():
    form = ChangeRoleForm()
    form.user_id.choices = [(u.id, u.name) for u in db_session.query(User).all()]
    form.role.choices = [('student', 'Student'), ('teacher', 'Teacher'), ('@dmin!', 'Admin')]

    if form.validate_on_submit():
        user = db_session.query(User).filter_by(id=form.user_id.data).first()
        if not user or user.id == current_user.id:
            flash('User not found', 'danger')
            return redirect(url_for('dashboard.index'))

        user.role = form.role.data
        db_session.commit()
        flash(f"{user.name}'s role updated to {form.role.data}", 'success')
    else:
        flash('Invalid form submission', 'danger')

    return redirect(url_for('dashboard.index'))


@bp.route('/delete_user', methods=['POST'])
@admin_required
def delete_user():
    form = DeleteUserForm()
    form.user_id.choices = [(u.id, u.name) for u in db_session.query(User).all()]

    if form.validate_on_submit():
        user = db_session.query(User).filter_by(id=form.user_id.data).first()

        if user and user.role != '@dmin!' and user.id != current_user.id and user.role != 'teacher':
            flashcards = db_session.query(Flashcard).filter_by(user_id=user.id).all()
            for fc in flashcards:
                db_session.delete(fc)

            db_session.delete(user)
            db_session.commit()
            flash(f"User {user.name} and their flashcards have been deleted", 'success')
        else:
            flash("User not found", 'danger')
    else:
        flash("Invalid form submission", 'danger')

    return redirect(url_for('dashboard.index'))

@bp.route('/toggle_active_status', methods=['POST'])
@admin_required
def toggle_active_status():
    form = ToggleActiveStatusForm()
    form.user_id.choices = [(u.id, u.name) for u in db_session.query(User).all()]

    if form.validate_on_submit():
        user = db_session.query(User).filter_by(id=form.user_id.data).first()
        if user and user.role != '@dmin!':
            user.active = not user.active
            db_session.commit()

            status = "activated" if user.active else "deactivated"
            flash(f"User {user.name} has been {status}.", 'success')
        else:
            flash("User not found", 'danger')
    else:
        flash("Invalid form submission", 'danger')

    return redirect(url_for('dashboard.index'))


@bp.route("/update_student_level", methods=["POST"])
@login_required
def update_student_level():
    form = ChangeStudentLevelForm()
    if not (current_user.is_teacher() or current_user.is_admin()):
        abort(403)

    if form.validate_on_submit():
        student = db_session.query(User).filter_by(id=form.student_id.data, role='student').first()
        if not student:
            flash("Student not found.", "danger")
        elif current_user.is_teacher() and student.assigned_teacher_id != current_user.id:
            abort(403)
        else:
            student.level = form.level.data
            db_session.commit()
            flash(f"{student.name}'s level updated to {form.level.data}", "success")
    else:
        print("DEBUG form.errors:", form.errors)
        print("DEBUG form data:", form.data)
        flash("Invalid form submission.", "danger")

    return redirect(url_for("dashboard.index"))
