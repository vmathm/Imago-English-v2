from flask import  Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.models import User, CalendarSettings
from app.services.google_calendar import get_teacher_availability
from app.database import db_session
from .forms import CalendarSettingsForm


bp = Blueprint('calendar', __name__, url_prefix='/calendar')

@bp.app_template_filter('dateformat')
def dateformat(value, fmt='%H:%M'):
    """Jinja filter to format datetime objects."""
    return value.strftime(fmt)

@bp.route('/<string:user_name>')
def teacher_calendar(user_name):
    teacher = db_session.query(User).filter_by(user_name=user_name, role='teacher').first()
    if not teacher:
        abort(404)
    grouped_slots = get_teacher_availability(teacher.id)
    return render_template('calendar/calendar.html', teacher=teacher, grouped_slots=grouped_slots)


@bp.route("/settings", methods=["GET", "POST"])
@login_required
def calendar_settings():
    if current_user.role != "teacher":
        abort(403)

    settings = (
        db_session.query(CalendarSettings)
        .filter_by(teacher_id=current_user.id)
        .first()
    )

    form = CalendarSettingsForm(obj=settings)

    if form.validate_on_submit():
        if not settings:
            settings = CalendarSettings(teacher_id=current_user.id)

        form.populate_obj(settings)
        db_session.add(settings)
        db_session.commit()
        flash("Calendar settings saved!", "success")
        return redirect(url_for("calendar.calendar_settings"))

    return render_template("calendar/settings.html", form=form, calendar_url = url_for("calendar.teacher_calendar", user_name=current_user.user_name, _external=True))