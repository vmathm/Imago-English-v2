from flask_wtf import FlaskForm
from wtforms import IntegerField, BooleanField, SubmitField
from wtforms.validators import NumberRange

class CalendarSettingsForm(FlaskForm):
    start_hour = IntegerField("Start Hour", validators=[NumberRange(min=0, max=23)])
    end_hour = IntegerField("End Hour", validators=[NumberRange(min=0, max=23)])
    available_saturday = BooleanField("Available on Saturday?")
    available_sunday = BooleanField("Available on Sunday?")
    show_today = BooleanField("Show Today?")
    submit = SubmitField("Save Settings")