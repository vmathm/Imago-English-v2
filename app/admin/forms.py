from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField, FileRequired
from wtforms import BooleanField, SelectField, SubmitField, HiddenField, StringField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, Regexp, NumberRange


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




class BookForm(FlaskForm):
    title = StringField(
        "Title",
        validators=[
            DataRequired(),
            Length(max=255),
        ],
    )

    slug = StringField(
        "Slug",
        validators=[
            DataRequired(),
            Length(max=255),
        ],
    )

    author = StringField(
        "Author",
        validators=[
            Optional(),
            Length(max=255),
        ],
    )

    description = TextAreaField(
        "Description",
        validators=[Optional()],
    )

    level = SelectField(
        "Level",
        choices=[
            ("A1", "A1"),
            ("A2", "A2"),
            ("B1", "B1"),
            ("B2", "B2"),
            ("C1", "C1"),
            ("C2", "C2"),
        ],
        validators=[DataRequired()],
    )

    cover_object_name = StringField(
        "Cover object name",
        validators=[
            Optional(),
            Length(max=500),
        ],
    )

    submit = SubmitField("Create book")


class EditBookForm(FlaskForm):
    title = StringField(
        "Title",
        validators=[DataRequired()]
    )

    slug = StringField(
        "Slug",
        validators=[DataRequired()]
    )

    author = StringField("Author")

    description = TextAreaField("Description")

    level = SelectField(
        "Level",
        choices=[
            ("A1", "A1"),
            ("A2", "A2"),
            ("B1", "B1"),
            ("B2", "B2"),
            ("C1", "C1"),
            ("C2", "C2"),
        ],
        validators=[DataRequired()],
    )

    submit = SubmitField("Update Book")




class ChapterForm(FlaskForm):
    book_id = SelectField(
        "Book",
        coerce=int,
        validators=[DataRequired()],
        choices=[]
    )

    title = StringField(
        "Chapter title",
        validators=[DataRequired()]
    )

    slug = StringField(
        "Slug",
        validators=[DataRequired()]
    )

    position = IntegerField(
        "Position",
        validators=[
            DataRequired(),
            NumberRange(min=1)
        ]
    )

    text_file = FileField(
        "Text file",
        validators=[
            Optional(),
            FileAllowed(["txt"], "Text files only."),
        ],
    )

    audio_file = FileField(
        "Audio file",
        validators=[
            Optional(),
            FileAllowed(["mp3"], "MP3 files only."),
        ],
    )

    is_free = BooleanField("Free chapter")

    
    submit = SubmitField("Create Chapter")


class EditChapterForm(ChapterForm):
    submit = SubmitField("Update Chapter")

