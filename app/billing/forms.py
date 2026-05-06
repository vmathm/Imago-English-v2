from flask_wtf import FlaskForm
from wtforms import BooleanField, HiddenField, IntegerField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Length, NumberRange, Optional, Regexp


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



from wtforms import BooleanField, SelectMultipleField
from wtforms.validators import Optional

class PlanForm(FlaskForm):
    name = StringField("Plan name", validators=[DataRequired()])
    amount_reais = IntegerField(
        "Amount (R$)",
        validators=[DataRequired(), NumberRange(min=1)]
    )
    currency = SelectField(
        "Currency",
        choices=[("BRL", "BRL")],
        validators=[DataRequired()],
    )
    interval = SelectField(
        "Interval",
        choices=[("monthly", "Monthly")],
        validators=[DataRequired()],
    )
    active = BooleanField("Active", default=True)

    available_to_all_students = BooleanField("Make available to all my students")

    eligible_student_ids = SelectMultipleField(
        "Specific students",
        coerce=str,
        choices=[],
        validators=[Optional()],
    )

    submit = SubmitField("Create plan")


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



class StudentBillingForm(FlaskForm):
    plan_id = HiddenField(validators=[DataRequired()])
    cpf_cnpj = StringField("CPF ou CNPJ", validators=[DataRequired()])
    submit = SubmitField("Assinar")