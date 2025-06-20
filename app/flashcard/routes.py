from flask import Blueprint, request, redirect, url_for, flash
from flask_login import current_user, login_required
from app.database import db_session
from app.flashcard.form import FlashcardForm
from app.models import Flashcard, User 



bp = Blueprint('flashcard', __name__, url_prefix='/flashcard')

@bp.route("/addcards", methods=["POST"])
@login_required
def addcards():
    form = FlashcardForm()
    if form.validate_on_submit():
        question = form.question.data
        answer = form.answer.data

        # Get optional student_id from the form or query string
        student_id = request.form.get("student_id")

        # Determine the owner of the flashcard
        if student_id:
            if not current_user.is_admin and not current_user.is_teacher:
                flash("Unauthorized to add flashcards for other users.", "danger")
                return redirect(url_for('dashboard.index'))

            # Optional: validate that the student exists and is connected to the teacher
            student = db_session.query(User).filter_by(id=student_id).first()
            if not student:
                flash("Student not found.", "danger")
                return redirect(url_for('dashboard.index'))

            flashcard_owner_id = student.id
        else:
            flashcard_owner_id = current_user.id

        # Create the flashcard
        new_flashcard = Flashcard(
            question=question,
            answer=answer,
            user_id=flashcard_owner_id
        )

        db_session.add(new_flashcard)
        db_session.commit()

        flash("Flashcard added successfully!", "success")
        return redirect(url_for('dashboard.index'))

    flash("Something went wrong. Please check your input.", "danger")
    return redirect(url_for('dashboard.index'))