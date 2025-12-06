from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, SubmitField, HiddenField, StringField
from wtforms.validators import DataRequired, Optional, Regexp

class AssignStudentForm(FlaskForm):
    student_id = SelectField("Student", validators=[DataRequired()], coerce=str, choices=[])
    teacher_id = SelectField("Teacher", validators=[DataRequired()], coerce=str, choices=[])
    submit = SubmitField("Assign")

class UnassignStudentForm(FlaskForm):
    student_id = SelectField("Student", validators=[DataRequired()], coerce=str, choices=[])
    submit = SubmitField("Unassign")

class ChangeRoleForm(FlaskForm):
    user_id = SelectField("User", validators=[DataRequired()], coerce=str, choices=[])
    role = SelectField("Role", choices=[("student", "student"), ("teacher", "teacher"), ("@dmin!", "@dmin!")], validators=[DataRequired()])
    submit = SubmitField("Change Role")

class DeleteUserForm(FlaskForm):
    user_id = SelectField("User", validators=[DataRequired()], coerce=str, choices=[])
    submit = SubmitField("Delete")

class ToggleActiveStatusForm(FlaskForm):
    user_id = SelectField("User", validators=[DataRequired()], coerce=str, choices=[])
    active = BooleanField("Active") 
    submit = SubmitField("Toggle Status")

class ChangeStudentLevelForm(FlaskForm):
    student_id = HiddenField(validators=[DataRequired()])
    level = SelectField(
        'Level',
        choices=[('', 'Level'),('A1','A1'), ('A2','A2'), ('B1','B1'), ('B2','B2'), ('C1','C1'), ('C2','C2')],
        validators=[DataRequired()]
    )
    submit = SubmitField('Update level')

class UpdatePhoneForm(FlaskForm):
    phone = StringField("phone", validators=[
        Optional(),
        Regexp(r'^\d{10,13}$', message="Digite o DDD seguido do número, sem espaços ou caracteres especiais (ex: 11987654321)")
    ])
    submit = SubmitField("Update Phone")


class UpdateLearningLanguageForm(FlaskForm):
    learning_language = SelectField(
        "Language you’re learning",
        choices=[
            ("en", "English"),
            ("pt-BR", "Brazilian Portuguese"),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Update Language")