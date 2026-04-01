from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, IntegerField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional


class AsaasSettingsForm(FlaskForm):
    provider = HiddenField(default="asaas")

    api_key = StringField(
        "API Key",
        validators=[Optional(), Length(max=1000)],
    )

    webhook_auth_token = StringField(
        "Webhook Auth Token",
        validators=[Optional(), Length(max=120)],
    )

    is_sandbox = BooleanField("Sandbox mode")
    active = BooleanField("Billing account active", default=True)

    submit = SubmitField("Save settings")




class PlanForm(FlaskForm):
    name = StringField(
        "Plan name",
        validators=[DataRequired(), Length(min=2, max=120)]
    )
    amount_reais = IntegerField(
        "Amount (R$)",
        validators=[DataRequired(), NumberRange(min=1, max=100000)]
    )
    currency = SelectField(
        "Currency",
        choices=[("BRL", "BRL")],
        validators=[DataRequired()],
        default="BRL",
    )
    interval = SelectField(
        "Interval",
        choices=[("month", "Monthly")],
        validators=[DataRequired()],
        default="month",
    )
    active = BooleanField("Active", default=True)
    submit = SubmitField("Create Plan")


class SubscriptionForm(FlaskForm):
    student_id = SelectField(
        "Student",
        validators=[DataRequired()],
        coerce=str,
        choices=[],
    )
    plan_id = SelectField(
        "Plan",
        validators=[DataRequired()],
        coerce=int,
        choices=[],
    )
    submit = SubmitField("Create Subscription")