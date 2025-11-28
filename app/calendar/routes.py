from flask import  Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from app.models import User, CalendarSettings
from app.services.google_calendar import get_teacher_availability
from app.database import db_session
from .forms import CalendarSettingsForm
from app.admin.forms import UpdatePhoneForm


bp = Blueprint('calendar', __name__, url_prefix='/calendar')

@bp.app_template_filter('dateformat')
def dateformat(value, fmt='%H:%M'):
    """Jinja filter to format datetime objects."""
    return value.strftime(fmt)

@bp.route('/<string:user_name>')
def teacher_calendar(user_name):
    if user_name  == 'admin':
        teacher = db_session.query(User).filter(User.email == 'vitornorace@gmail.com').first()
    else:
        teacher = db_session.query(User).filter(User.user_name == user_name, User.role.in_(("teacher", "@dmin!"))).first()
    if not teacher:
        abort(404)
    grouped_slots = get_teacher_availability(teacher.id)
    return render_template('calendar/calendar.html', teacher=teacher, grouped_slots=grouped_slots)



@bp.route("/settings", methods=["GET", "POST"])
@login_required
def calendar_settings():
    if current_user.role not in ("teacher", "@dmin!"):
        abort(403)

    settings = db_session.query(CalendarSettings).filter_by(teacher_id=current_user.id).first()
    
    

    
    if not settings:
        settings = CalendarSettings(
            teacher_id=current_user.id,
            start_hour=7,
            end_hour=21,
            lesson_duration=30,
        )
        db_session.add(settings)  
        db_session.commit()

        form = CalendarSettingsForm()

    else:
        form = CalendarSettingsForm(obj=settings)

    if form.validate_on_submit():
        form.populate_obj(settings)

        db_session.add(settings)  
        db_session.commit()

        flash("Calendar settings saved!", "success")
        return redirect(url_for("calendar.calendar_settings"))



    calendar_url = url_for("calendar.teacher_calendar", user_name=current_user.user_name, _external=True)
    return render_template("calendar/settings.html", form=form, phone_form=UpdatePhoneForm(), calendar_url=calendar_url)


@bp.route("/update-phone", methods=["POST"])
@login_required
def update_phone():
    

    form = UpdatePhoneForm()

    if form.validate_on_submit():
        current_user.phone = form.phone.data
        db_session.commit()
        flash("Phone number updated!", "success")
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{error}", "danger")

    return redirect(url_for("calendar.calendar_settings"))
