from flask_wtf import FlaskForm
from wtforms import SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired

class AssignStudentForm(FlaskForm):
    student_id = SelectField("Student", validators=[DataRequired()], coerce=int, choices=[])
    teacher_id = SelectField("Teacher", validators=[DataRequired()], coerce=int, choices=[])
    submit = SubmitField("Assign")

class UnassignStudentForm(FlaskForm):
    student_id = SelectField("Student", validators=[DataRequired()], coerce=int, choices=[])
    submit = SubmitField("Unassign")

class ChangeRoleForm(FlaskForm):
    user_id = SelectField("User", validators=[DataRequired()], coerce=int, choices=[])
    role = SelectField("Role", choices=[("student", "student"), ("teacher", "teacher"), ("@dmin!", "@dmin!")], validators=[DataRequired()])
    submit = SubmitField("Change Role")

class DeleteUserForm(FlaskForm):
    user_id = SelectField("User", validators=[DataRequired()], coerce=int, choices=[])
    submit = SubmitField("Delete")

class ToggleActiveStatusForm(FlaskForm):
    user_id = SelectField("User", validators=[DataRequired()], coerce=int, choices=[])
    submit = SubmitField("Toggle Status")

class ChangeStudentLevelForm(FlaskForm):
    student_id = HiddenField(validators=[DataRequired()])
    level = SelectField(
        'Level',
        choices=[('A1','A1'), ('A2','A2'), ('B1','B1'), ('B2','B2'), ('C1','C1'), ('C2','C2')],
        validators=[DataRequired()]
    )
    submit = SubmitField('Update level')
