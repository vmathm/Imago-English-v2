from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, IntegerField, BooleanField
from wtforms.validators import DataRequired, Length, NumberRange, Regexp
from flask_wtf.file import FileField, FileAllowed, FileRequired

class UsernameForm(FlaskForm):
    user_name = StringField(
        "Nome de usuário",
        validators=[
            DataRequired(message="Escolha um nome de usuário."),
            Length(min=3, max=20, message="Use entre 3 e 20 caracteres."),
            Regexp(
                r"^[A-Za-z0-9_.-]+$",
                message="Use apenas letras, números, ponto, hífen ou underline."
            ),
        ],
    )
    submit = SubmitField("Save username (Salvar nome de usuário)")



class UserAudiobookForm(FlaskForm):
    text_file = FileField(
        "Text file (.txt) (optional)",
        validators=[
            FileAllowed(["txt"], "Only .txt files are allowed.")
        ]
    )
    audio_file = FileField(
        "Audio file (.mp3) (optional)",
        validators=[
            FileAllowed(["mp3"], "Only .mp3 files are allowed.")
        ]
    )
    submit = SubmitField("Upload audiobook")




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
            FileAllowed(["txt"], "Only .txt files are allowed.")
        ]
    )

    audio_file = FileField(
        "Audio file",
        validators=[
            FileAllowed(["mp3"], "Only .mp3 files are allowed.")
        ]
    )

    submit = SubmitField("Create Chapter")


class EditChapterForm(ChapterForm):
    submit = SubmitField("Update Chapter")