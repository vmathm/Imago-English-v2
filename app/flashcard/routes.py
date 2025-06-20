from flask import Blueprint, request, redirect, url_for, flash, render_template
from flask_login import current_user, login_required
from app.database import db_session
from app.flashcard.form import FlashcardForm
from app.models import Flashcard, User 



bp = Blueprint('flashcard', __name__, url_prefix='/flashcard')


@bp.route("/flashcards", methods=["POST"])
@login_required
def flashcards():
    return render_template("flashcards.html", form=FlashcardForm())



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

@bp.route("/edit_cards", methods=["GET"])
@login_required
def edit_cards():
    if current_user.is_student():
        flashcards = (
            db_session.query(Flashcard)
            .filter_by(user_id=current_user.id)
            .all()
        )
        return render_template("edit_cards.html", flashcards=flashcards)

    if current_user.is_teacher() or current_user.is_admin():
        student_id = request.args.get("student_id") 

        if not student_id:
            flash("Please select a student to view their flashcards.", "warning")
            return redirect(url_for("dashboard.index"))

        # Verify the student exists
        student = db_session.query(User).filter_by(id=student_id).first()
        if not student:
            flash("Student not found.", "danger")
            return redirect(url_for("dashboard.index"))

        # Teachers can only access their own students
        if current_user.is_teacher() and student.assigned_teacher_id != current_user.id:
            flash("You are not authorized to view this student's flashcards.", "danger")
            return redirect(url_for("dashboard.index"))

        flashcards = (
            db_session.query(Flashcard)
            .filter_by(user_id=student_id)
            .all()
        )
        return render_template("edit.html", flashcards=flashcards)

    # Fallback for unrecognized roles
    flash("Access denied.", "danger")
    return redirect(url_for("dashboard.index"))


@bp.route("/edit_card/<int:card_id>", methods=["POST"])
@login_required
def edit_card(card_id):
    flashcard = db_session.query(Flashcard).get(card_id)

    if not flashcard:
        flash("Flashcard not found.", "danger")
        return redirect(url_for('dashboard.index'))

    # Check ownership or teacher-student relationship
    is_owner = flashcard.user_id == current_user.id
    is_teacher_of_student = (
        current_user.is_teacher() and
        flashcard.user.assigned_teacher_id == current_user.id
    )

    if not (is_owner or is_teacher_of_student or current_user.is_admin()):
        flash("You're not authorized to edit this flashcard.", "danger")
        return redirect(url_for('dashboard.index'))

    form = FlashcardForm(obj=flashcard) # pre-fill for GET

    if form.validate_on_submit():
        flashcard.question = form.question.data
        flashcard.answer = form.answer.data
        db_session.commit()
        flash("Flashcard updated successfully!", "success")
        return redirect(url_for('dashboard.index'))









