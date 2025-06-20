from flask import Blueprint, render_template, redirect, url_for, flash
from flask_login import current_user, login_required
from app.database import db_session
from app.flashcard.form import FlashcardForm
from app.models import Flashcard  


bp = Blueprint('flashcard', __name__, url_prefix='/flashcard')

@bp.route("/addcards", methods=["POST"])
@login_required  
def addcards():
    form = FlashcardForm()
    if form.validate_on_submit():
        question = form.question.data
        answer = form.answer.data

        # Create new flashcard
        new_flashcard = Flashcard(
            question=question,
            answer=answer,
            user_id=current_user.id  # assuming Flashcard has a foreign key to User
        )

        # Save to database
        db_session.add(new_flashcard)
        db_session.commit()

        flash("Flashcard added successfully!", "success")
        return redirect(url_for('dashboard.index'))  # Redirect to a dashboard or flashcard list page
       

    # If validation fails, redirect or handle as needed
    flash("Something went wrong. Please check your input.", "danger")
    return redirect(url_for('dashboard.i'))
    