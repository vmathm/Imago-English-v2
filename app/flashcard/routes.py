from flask import Blueprint, request, redirect, url_for, flash, render_template, jsonify
from flask_login import current_user, login_required
from app.database import db_session
from app.decorators import active_required
from app.flashcard.form import FlashcardForm
from app.models import Flashcard, User
from datetime import datetime, timezone, timedelta
from sqlalchemy import func, or_, asc
import math
from app.extensions import csrf
from os import abort

bp = Blueprint('flashcard', __name__, url_prefix='/flashcard')


@bp.route("/flashcards", methods=["GET"])
@login_required
def flashcards():

    total_flashcards = db_session.query(func.count(Flashcard.id)).filter_by(user_id=current_user.id).scalar()
    due_count = (
            db_session.query(func.count(Flashcard.id))
            .filter(
                Flashcard.user_id == current_user.id,
                or_(
                    Flashcard.next_review.is_(None),
                    Flashcard.next_review <= datetime.now(timezone.utc),
                ),
            )
            .scalar()
        )

    has_cards = (due_count or 0) > 0
    return render_template("flashcards/index_cards.html", form=FlashcardForm(), has_cards=has_cards, due_count=due_count, total_flashcards=total_flashcards)

@bp.route("/addcards", methods=["POST"])
@active_required
def addcards():
    form = FlashcardForm()
    if form.validate_on_submit():
        question = form.question.data
        answer = form.answer.data

        student_id = form.student_id.data
        print(f"Student ID: {student_id}")
        if student_id:
            student = db_session.query(User).filter_by(id=student_id).first()
            
            if not student:
                flash("Student not found.", "danger")
                return redirect(url_for("dashboard.index"))

            if current_user.is_teacher():
                if student.assigned_teacher_id != current_user.id:
                    flash("You cannot add cards for this student.", "danger")
                    return redirect(url_for("dashboard.index"))
            elif not current_user.is_admin():
                flash("Unauthorized.", "danger")
                return redirect(url_for("dashboard.index"))

            flashcard_owner_id = student.id
        else:
            flashcard_owner_id = current_user.id

        
        existing = db_session.query(Flashcard).filter_by(
            question=question,
            user_id=flashcard_owner_id
        ).first()

        if existing:
            message = "Flashcard already exists!"
            return jsonify({"status": "error", "message": message})
        

        unreviewed_limit = True if db_session.query(Flashcard).filter_by(user_id=flashcard_owner_id, reviewed_by_tc=False).count() >= 5 else False
        if unreviewed_limit:
            message = "Você não pode ter mais de 5 cartões não revisados."
            return jsonify({"status": "error", "message": message})

       
        new_flashcard = Flashcard(
            question=question,
            answer=answer,
            user_id=flashcard_owner_id,
            reviewed_by_tc= True if current_user.is_teacher() else False,
            created_at=datetime.now(timezone.utc)
        )

        db_session.add(new_flashcard)
        db_session.commit()

        message = "Flashcard added successfully!"
        return jsonify({"status": "success", "message": message})
   

    message = "Something went wrong. Please check your input."
    return jsonify({"status": "error", "message": message})
   


        







@bp.route("/edit_cards", methods=["GET"])
@active_required
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

        
        student = db_session.query(User).filter_by(id=student_id).first()
        if not student:
            flash("Student not found.", "danger")
            return redirect(url_for("dashboard.index"))

        
        if current_user.is_teacher() and student.assigned_teacher_id != current_user.id:
            flash("You are not authorized to view this student's flashcards.", "danger")
            return redirect(url_for("dashboard.index"))

        flashcards = (
            db_session.query(Flashcard)
            .filter_by(user_id=student_id)
            .all()
        )
        return render_template("edit.html", flashcards=flashcards)   

    
    flash("Access denied.", "danger")
    return redirect(url_for("dashboard.index"))



@bp.route("/edit_card/<int:card_id>", methods=["POST"])
@active_required
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
    action = request.form.get("action")

    
    if action == "mark_reviewed_tc":
        if not (is_teacher_of_student or current_user.is_admin()):
            return jsonify({"status": "error", "message": "Not authorized."}), 403
       
       
        flashcard.reviewed_by_tc = True
        db_session.commit()
        return jsonify({
            "status": "success",
            "message": "Marked as reviewed by teacher.",
            "card_id": flashcard.id,
            "reviewed_by_tc": True
        })

    if form.validate_on_submit():
        if action == "edit":
            flashcard.question = form.question.data
            flashcard.answer  = form.answer.data

           
            if is_teacher_of_student or current_user.is_admin():
                flashcard.reviewed_by_tc = True
            else:
                flashcard.reviewed_by_tc = False

            db_session.commit()
            return jsonify({
                "status": "success",
                "message": "Flashcard updated!",
                "card_id": flashcard.id,
                "reviewed_by_tc": flashcard.reviewed_by_tc
            })

        elif action == "delete":
            db_session.delete(flashcard)
            db_session.commit()
            return jsonify({"status": "success", "message": "Flashcard deleted!"})

    return jsonify({"status": "error", "message": "Form validation failed."}), 400






@bp.route("/study")
@active_required
def study():
    """Show flashcards due for review."""
    student_id = request.args.get("student_id")
    target_user_id = current_user.id

    if student_id:
        if not (current_user.is_teacher() or current_user.is_admin()):
            abort(403)
        student = db_session.query(User).filter_by(id=student_id).first()
        if not student or (
            current_user.is_teacher() and student.assigned_teacher_id != current_user.id
        ):
            abort(403)
        target_user_id = student.id

    due_cards = (
        db_session.query(
            Flashcard.id,
            Flashcard.question,
            Flashcard.answer,
            Flashcard.level
        )
        .filter(
            Flashcard.user_id == target_user_id,
            or_(
                Flashcard.next_review == None,
                Flashcard.next_review <= datetime.now(timezone.utc)
            )
        )
        .all()
    )

    cards_data = [
        {"id": card.id, "question": card.question, "answer": card.answer, "level": card.level}
        for card in due_cards
    ]

    if not cards_data:
        flash("Você não tem flashcards para estudar.", "info")

    return render_template("flashcards/study.html", cards=cards_data, student_id=student_id)



@bp.route("/review_flashcard", methods=["POST"])
@active_required
def review_flashcard():
    """
    Update flashcard scheduling when a rating (1, 2, or 3) is submitted from study.js.
    Also update study streak if this was the last due flashcard of the day.
    """
    data = request.get_json() or {} 
    card_id = data.get("card_id")
    rating = int(data.get("rating"))

    MIN_INTERVAL, MAX_INTERVAL = 1, 365
    flashcard = db_session.query(Flashcard).get(str(card_id))
    if not flashcard:
        return jsonify({"status": "error", "message": "Flashcard not found."}), 404

    now = datetime.now(timezone.utc) - timedelta(hours=3)

    def award_points(user, pts):
        user.points = user.points + pts

    def get_recipient():
        if current_user.role == "teacher" and flashcard.user_id == current_user.id:
            return current_user
        if current_user.role in ("teacher", "@dmin!") and flashcard.user_id != current_user.id:
            return db_session.query(User).filter(User.id == flashcard.user_id).first()
        return current_user

    recipient = get_recipient()

    
    if rating == 1:
        flashcard.level += 1
        flashcard.ease = 1.3
        flashcard.interval = MIN_INTERVAL
        flashcard.last_review = now
        flashcard.next_review = now + timedelta(seconds=3)
        recipient.flashcards_studied = (recipient.flashcards_studied or 0) + 1

    elif rating == 2:
        award_points(recipient, 2)
        flashcard.level += 1
        flashcard.ease = 1.3
        flashcard.interval = MIN_INTERVAL
        flashcard.last_review = now
        next_review = now + timedelta(days=1)
        flashcard.next_review = next_review.replace(hour=0, minute=0, second=0, microsecond=0)
        recipient.flashcards_studied = (recipient.flashcards_studied or 0) + 1

    else:
        recipient.rate_three_count = (recipient.rate_three_count or 0) + 1
        recipient.flashcards_studied = (recipient.flashcards_studied or 0) + 1

        flashcard.level += 1
        new_ease = min(
            (flashcard.ease + 0.5 - (5 - rating) * (0.08 + (5 - rating) * 0.02)) / 2,
            2.5,
        )
        flashcard.ease = max(new_ease, 1.3)

        new_interval = int(math.ceil(flashcard.interval * flashcard.ease))
        flashcard.interval = min(MAX_INTERVAL, new_interval)

        award_points(recipient, max(int(flashcard.interval / 2), 1))

        flashcard.last_review = now
        next_review = now + timedelta(days=flashcard.interval)
        flashcard.next_review = next_review.replace(hour=0, minute=0, second=0, microsecond=0)

    db_session.commit()

    
    due_left = db_session.query(Flashcard).filter(
        Flashcard.user_id == flashcard.user_id,
        or_(
            Flashcard.next_review == None,
            Flashcard.next_review <= datetime.now(timezone.utc)
        )
    ).count()

    if due_left == 0:
        update_study_streak(recipient)
        db_session.commit()

    return jsonify({"status": "success"})

def update_study_streak(user):
    
    today = datetime.now(timezone.utc).date()
    yesterday = today - timedelta(days=1)

    if user.streak_last_date == yesterday:
        user.study_streak = (user.study_streak or 0) + 1
        user.streak_last_date = today
    elif user.streak_last_date not in (today, yesterday):
        user.study_streak = 1
        user.streak_last_date = today

    # Update max_study_streak
    if user.study_streak and user.study_streak > (user.max_study_streak or 0):
        user.max_study_streak = user.study_streak

    # Always recompute max_points as points × max_study_streak
    user.max_points = (user.points or 0) * (user.max_study_streak or 0)

@bp.route("/manage/<student_id>", methods=["GET"])
@active_required
def manage_student(student_id):
    if not current_user.is_teacher() and not current_user.is_admin():
        abort(403)

    student = db_session.query(User).filter_by(id=student_id).first()
    if not student or (
        current_user.is_teacher() and student.assigned_teacher_id != current_user.id
    ):
        abort(403)

    form = FlashcardForm()
    form.student_id.data = student.id
    flashcards = db_session.query(Flashcard).filter_by(user_id=student_id).order_by(asc(Flashcard.reviewed_by_tc)).all()
    forms = {c.id: FlashcardForm(obj=c) for c in flashcards}

    return render_template(
        "flashcards/manage_student_cards.html",
        student=student,
        form=form,
        flashcards=flashcards,
        forms=forms,
    )



