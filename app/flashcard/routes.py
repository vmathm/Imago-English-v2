from flask import Blueprint, request, redirect, url_for, flash, render_template
from flask_login import current_user, login_required
from app.database import db_session
from app.flashcard.form import FlashcardForm
from app.models import Flashcard, User 
from flask import jsonify
from datetime import datetime, timezone
from sqlalchemy import or_


bp = Blueprint('flashcard', __name__, url_prefix='/flashcard')


@bp.route("/flashcards", methods=["GET"])
@login_required
def flashcards():
    return render_template("flashcards/index_cards.html", form=FlashcardForm())



@bp.route("/addcards", methods=["POST"])
@login_required
def addcards():
    form = FlashcardForm()
    if form.validate_on_submit():
        question = form.question.data
        answer = form.answer.data

        # Optional student ID for teachers/admins
        student_id = request.form.get("student_id")

        if student_id:
            if not current_user.is_admin and not current_user.is_teacher:
                flash("Unauthorized to add flashcards for other users.", "danger")
                return redirect(url_for("dashboard.index"))

            student = db_session.query(User).filter_by(id=student_id).first()
            if not student:
                flash("Student not found.", "danger")
                return redirect(url_for("dashboard.index"))

            flashcard_owner_id = student.id
        else:
            flashcard_owner_id = current_user.id

        # Check if this user already has a card with the same question
        existing = db_session.query(Flashcard).filter_by(
            question=question,
            user_id=flashcard_owner_id
        ).first()

        if existing:
            message = "Flashcard already exists!"
            return jsonify({"status": "error", "message": message})


        # Create the new flashcard
        new_flashcard = Flashcard(
            question=question,
            answer=answer,
            user_id=flashcard_owner_id
            
        )

        db_session.add(new_flashcard)
        db_session.commit()

        message = "Flashcard added successfully!"
        return jsonify({"status": "success", "message": message})
        flash(message, "success")
        return redirect(url_for("dashboard.index"))

    message = "Something went wrong. Please check your input."
    return jsonify({"status": "error", "message": message})
   


        







@bp.route("/edit_cards", methods=["GET"])
@login_required
def edit_cards():
    
    if current_user.is_student():
        flashcards = (
            db_session.query(Flashcard)
            .filter_by(user_id=current_user.id)
            .all()
        )
        forms = {card.id: FlashcardForm(obj=card) for card in flashcards} 
        return render_template("flashcards/edit_cards.html", flashcards=flashcards, forms=forms)

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
        return jsonify({"status": "error", "message": "Flashcard not found."}), 404

    is_owner = flashcard.user_id == current_user.id
    is_teacher_of_student = (
        current_user.is_teacher() and
        flashcard.user.assigned_teacher_id == current_user.id
    )

    if not (is_owner or is_teacher_of_student or current_user.is_admin()):
        return jsonify({"status": "error", "message": "Not authorized."}), 403

    form = FlashcardForm()

    if form.validate_on_submit():
        action = request.form.get("action")

        if action == "edit":
            flashcard.question = form.question.data
            flashcard.answer = form.answer.data
            db_session.commit()
            return jsonify({"status": "success", "message": "Flashcard updated!"})

        elif action == "delete":
            db_session.delete(flashcard)
            db_session.commit()
            return jsonify({"status": "success", "message": "Flashcard deleted!"})

    return jsonify({"status": "error", "message": "Form validation failed."}), 400






@bp.route("/study")
@login_required
def study():
    """Show flashcards due for review."""
    due_cards = (
        db_session.query(
            Flashcard.id,
            Flashcard.question,
            Flashcard.answer
        )
        .filter(
            Flashcard.user_id == current_user.id,
            or_(
                Flashcard.next_review == None,  
                Flashcard.next_review <= datetime.now(timezone.utc)
            )
        )
        .all()
    )

    # convert to dict so it can be JSON‑serialized
    cards_data = [
    {"id": card.id, "question": card.question, "answer": card.answer}
    for card in due_cards
    ]   
    if not cards_data:
        flash("Você não tem flashcards para estudar.", "info")
    return render_template("flashcards/study.html", cards=cards_data)

