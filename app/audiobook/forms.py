from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp
from flask_wtf.file import FileField, FileAllowed

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