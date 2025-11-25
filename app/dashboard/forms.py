from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length, Regexp

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
