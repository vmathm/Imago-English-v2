from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, HiddenField
from wtforms.validators import DataRequired


class FlashcardForm(FlaskForm):
    question = StringField("Question", validators=[DataRequired()])
    answer = StringField("Answer", validators=[DataRequired()])
    student_id = HiddenField()  
    submit = SubmitField("Adicionar")