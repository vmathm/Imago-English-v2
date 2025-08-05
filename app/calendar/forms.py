from flask_wtf import FlaskForm
from wtforms import IntegerField, BooleanField, SubmitField
from wtforms.validators import NumberRange

class CalendarSettingsForm(FlaskForm):
    start_hour = IntegerField("Start time", validators=[NumberRange(min=0, max=23)])
    end_hour = IntegerField("End time", validators=[NumberRange(min=0, max=23)])
    lesson_duration = IntegerField("Lesson Duration:", validators=[NumberRange(min=1, max=120)])
    available_saturday = BooleanField("Available on Saturday?")
    available_sunday = BooleanField("Available on Sunday?")
    show_today = BooleanField("Show Today?")
    submit = SubmitField("Save Settings")