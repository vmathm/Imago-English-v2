from flask import Blueprint, render_template
from flask_login import login_required
from app.models import User
from app.database import db_session

bp = Blueprint('progress', __name__)

@bp.route('/leaderboard')
def leaderboard():
    students = (
        db_session.query(User)
        .filter_by(role='student')
        .all()
    )
    teachers = db_session.query(User).filter_by(role='teacher').all()
    total_students = len(students)
    total_teachers = len(teachers)

    top_students = (
        db_session.query(User)
        .filter_by(role='student')
        .order_by(User.max_points.desc())
        .limit(3)
        .all()
    )

    return render_template(
        'progress/leaderboard.html',
        students=students,
        teachers=teachers,
        total_students=total_students,
        total_teachers=total_teachers,
        top_students=top_students,
    )
