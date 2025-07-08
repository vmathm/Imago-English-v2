# app/admin/routes.py
from flask import Blueprint, request, redirect, url_for, abort, flash
from flask_login import login_required, current_user
from app.models import User
from app.database import db_session
from functools import wraps

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
    student_id = request.form.get('student_id')
    teacher_id = request.form.get('teacher_id')
    student = db_session.query(User).filter_by(id=student_id, role='student').first()
    teacher = db_session.query(User).filter_by(id=teacher_id, role='teacher').first()
    if not student or not teacher:
        flash('Invalid selection', 'danger')
        return redirect(url_for('dashboard.index'))
    student.assigned_teacher_id = teacher.id
    db_session.commit()
    flash(f'{student.name} assigned to {teacher.name}', 'success')
    return redirect(url_for('dashboard.index'))


@bp.route('/unassign_student', methods=['POST'])
@admin_required
def unassign_student():
    student_id = request.form.get('student_id')
    student = db_session.query(User).filter_by(id=student_id, role='student').first()
    if not student:
        flash('Invalid student', 'danger')
        return redirect(url_for('dashboard.index'))
    student.assigned_teacher_id = None
    db_session.commit()
    flash(f'{student.name} unassigned', 'success')
    return redirect(url_for('dashboard.index'))


@bp.route('/change_role', methods=['POST'])
@admin_required
def change_role():
    user_id = request.form.get('user_id')
    role = request.form.get('role')
    user = db_session.query(User).filter_by(id=user_id).first()
    if not user or role not in ['student', 'teacher', '@dmin!']:
        flash('Invalid user or role', 'danger')
        return redirect(url_for('dashboard.index'))
    user.role = role
    db_session.commit()
    flash(f"{user.name}'s role updated to {role}", 'success')
    return redirect(url_for('dashboard.index'))
