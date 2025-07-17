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