from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length

def _strip(x):  # trims extra spaces safely
    return x.strip() if isinstance(x, str) else x

class FlashcardForm(FlaskForm):
    question = TextAreaField(
        "Question",
        validators=[DataRequired(), Length(max=500, message="Max 500 characters.")],
        filters=[_strip],
        render_kw={"maxlength": 500}
    )
    answer = TextAreaField(
        "Answer",
        validators=[DataRequired(), Length(max=500, message="Max 500 characters.")],
        filters=[_strip],
        render_kw={"maxlength": 500}
    )
    student_id = HiddenField()
    submit = SubmitField("Adicionar")