from flask import Blueprint, request, redirect, url_for, flash, render_template, jsonify, abort
from flask_login import current_user, login_required
from app.database import db_session
from app.decorators import active_required
from app.flashcard.form import FlashcardForm
from app.models import Flashcard, User
from sqlalchemy import func, or_, asc
import math
from app.extensions import csrf
from decimal import Decimal, ROUND_HALF_UP
from app.utils.time import utcnow, now_sp, sp_midnight_as_utc, sp_midnight_utc_days_from_now
from datetime import timedelta


bp = Blueprint("flashcard", __name__, url_prefix="/flashcard")




# ----------------------------
# Decimal helper
# ----------------------------
def normalize_ease(value):
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


# ----------------------------
# Routes
# ----------------------------
@bp.route("/flashcards", methods=["GET"])
@login_required
def flashcards():
    total_flashcards = (
        db_session.query(func.count(Flashcard.id))
        .filter(Flashcard.user_id == current_user.id)
        .scalar()
        or 0
    )

    due_count = (
        db_session.query(func.count(Flashcard.id))
        .filter(
            Flashcard.user_id == current_user.id,
            or_(
                Flashcard.next_review.is_(None),
                Flashcard.next_review <= utcnow(),
            ),
        )
        .scalar()
        or 0
    )

    has_cards = due_count > 0
    return render_template(
        "flashcards/index_cards.html",
        form=FlashcardForm(),
        has_cards=has_cards,
        due_count=due_count,
        total_flashcards=total_flashcards,
    )


@bp.route("/addcards", methods=["POST"])
@active_required
def addcards():
    form = FlashcardForm()
    if not form.validate_on_submit():
        return jsonify({"status": "error", "message": "Something went wrong. Please check your input."})

    question = form.question.data
    answer = form.answer.data
    student_id = form.student_id.data

    # Decide card owner
    if student_id:
        if not (current_user.is_teacher() or current_user.is_admin()):
            return jsonify({"status": "error", "message": "Unauthorized."}), 403

        student = db_session.query(User).filter_by(id=student_id).first()
        if not student:
            return jsonify({"status": "error", "message": "Student not found."}), 404

        if current_user.is_teacher() and student.assigned_teacher_id != current_user.id:
            return jsonify({"status": "error", "message": "You cannot add cards for this student."}), 403

        flashcard_owner_id = student.id
    else:
        flashcard_owner_id = current_user.id

    # Prevent duplicates (same question per user)
    existing = (
        db_session.query(Flashcard)
        .filter_by(question=question, user_id=flashcard_owner_id)
        .first()
    )
    if existing:
        return jsonify({"status": "error", "message": "Flashcard already exists!"})

    # Unreviewed limit
    unreviewed_count = (
        db_session.query(Flashcard)
        .filter_by(user_id=flashcard_owner_id, reviewed_by_tc=False)
        .count()
    )
    if unreviewed_count >= 5:
        return jsonify({"status": "error", "message": "Você não pode ter mais de 5 cartões não revisados."})

    new_flashcard = Flashcard(
        question=question,
        answer=answer,
        user_id=flashcard_owner_id,
        reviewed_by_tc=True if current_user.is_teacher() else False,
        created_at=utcnow(),
    )

    db_session.add(new_flashcard)
    db_session.commit()

    return jsonify({"status": "success", "message": "Flashcard added successfully!"})


@bp.route("/edit_cards", methods=["GET"])
@active_required
def edit_cards():
    if current_user.is_student():
        flashcards = db_session.query(Flashcard).filter_by(user_id=current_user.id).all()
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

        flashcards = db_session.query(Flashcard).filter_by(user_id=student_id).all()
        return render_template("edit.html", flashcards=flashcards)

    flash("Access denied.", "danger")
    return redirect(url_for("dashboard.index"))


@bp.route("/edit_card/<int:card_id>", methods=["POST"])
@active_required
def edit_card(card_id):
    flashcard = db_session.get(Flashcard, card_id)
    if not flashcard:
        return jsonify({"status": "error", "message": "Flashcard not found."}), 404

    is_owner = flashcard.user_id == current_user.id
    is_teacher_of_student = (
        current_user.is_teacher()
        and getattr(flashcard.user, "assigned_teacher_id", None) == current_user.id
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
        return jsonify(
            {
                "status": "success",
                "message": "Marked as reviewed by teacher.",
                "card_id": flashcard.id,
                "reviewed_by_tc": True,
            }
        )

    if not form.validate_on_submit():
        return jsonify({"status": "error", "message": "Form validation failed."}), 400

    if action == "edit":
        flashcard.question = form.question.data
        flashcard.answer = form.answer.data

        # Make it due again immediately (UTC now)
        flashcard.next_review = utcnow()
        flashcard.ease = normalize_ease(1.3)
        flashcard.interval = 1

        flashcard.reviewed_by_tc = True if (is_teacher_of_student or current_user.is_admin()) else False

        db_session.commit()
        return jsonify(
            {
                "status": "success",
                "message": "Flashcard updated!",
                "card_id": flashcard.id,
                "reviewed_by_tc": flashcard.reviewed_by_tc,
            }
        )

    if action == "delete":
        db_session.delete(flashcard)
        db_session.commit()
        return jsonify({"status": "success", "message": "Flashcard deleted!"})

    return jsonify({"status": "error", "message": "Unknown action."}), 400


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
        if not student:
            abort(403)

        if current_user.is_teacher() and student.assigned_teacher_id != current_user.id:
            abort(403)

        target_user_id = student.id

    due_cards = (
        db_session.query(Flashcard.id, Flashcard.question, Flashcard.answer, Flashcard.level)
        .filter(
            Flashcard.user_id == target_user_id,
            or_(
                Flashcard.next_review.is_(None),
                Flashcard.next_review <= utcnow(),
            ),
        )
        .all()
    )

    cards_data = [{"id": c.id, "question": c.question, "answer": c.answer, "level": c.level} for c in due_cards]

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
    data = request.get_json(silent=True) or {}
    card_id = data.get("card_id")
    rating_raw = data.get("rating")

    if not card_id or rating_raw is None:
        return jsonify({"status": "error", "message": "Missing card_id or rating."}), 400

    try:
        rating = int(rating_raw)
    except (TypeError, ValueError):
        return jsonify({"status": "error", "message": "Invalid rating."}), 400

    if rating not in (1, 2, 3):
        return jsonify({"status": "error", "message": "Rating must be 1, 2, or 3."}), 400

    flashcard = db_session.get(Flashcard, int(card_id))
    if not flashcard:
        return jsonify({"status": "error", "message": "Flashcard not found."}), 404

    MIN_INTERVAL, MAX_INTERVAL = 1, 365
    now = utcnow()

    def award_points(user, pts: int):
        user.points = (user.points or 0) + int(pts)

    def get_recipient():
        # Teacher reviewing their own cards -> teacher gets points
        if current_user.role == "teacher" and flashcard.user_id == current_user.id:
            return current_user

        # Teacher/Admin reviewing a student's cards -> student gets points
        if current_user.role in ("teacher", "@dmin!") and flashcard.user_id != current_user.id:
            return db_session.query(User).filter(User.id == flashcard.user_id).first()

        # Student studying
        return current_user

    recipient = get_recipient()
    if not recipient:
        return jsonify({"status": "error", "message": "Recipient user not found."}), 500

    # Always count studied cards
    recipient.flashcards_studied = (recipient.flashcards_studied or 0) + 1

    if rating == 1:
        flashcard.level += 1
        flashcard.ease = normalize_ease(1.3)
        flashcard.interval = MIN_INTERVAL
        flashcard.last_review = now

        # keep it "in-session" quickly, still stored as UTC
        flashcard.next_review = now 

    elif rating == 2:
        award_points(recipient, 2)

        flashcard.level += 1
        flashcard.ease = normalize_ease(1.3)
        flashcard.interval = MIN_INTERVAL
        flashcard.last_review = now

        # Tomorrow at São Paulo midnight, stored in UTC
        flashcard.next_review = sp_midnight_utc_days_from_now(1)

    else:  # rating == 3
        recipient.rate_three_count = (recipient.rate_three_count or 0) + 1

        flashcard.level += 1

        new_ease = (
            flashcard.ease
            + Decimal("0.5")
            - Decimal(5 - rating) * (Decimal("0.08") + Decimal(5 - rating) * Decimal("0.02"))
        ) / Decimal("2")
        flashcard.ease = normalize_ease(max(new_ease, Decimal("1.3")))

        new_interval = int(math.ceil(float(flashcard.interval) * float(flashcard.ease)))
        flashcard.interval = min(MAX_INTERVAL, max(MIN_INTERVAL, new_interval))

        award_points(recipient, max(int(flashcard.interval / 2), 1))

        flashcard.last_review = now

        # Interval days later at São Paulo midnight, stored in UTC
        target_date = now_sp().date() + timedelta(days=flashcard.interval)
        flashcard.next_review = sp_midnight_as_utc(target_date)

    db_session.commit()

    # Re-check due using REAL UTC now (not the São Paulo hack)
    due_left = (
        db_session.query(Flashcard)
        .filter(
            Flashcard.user_id == flashcard.user_id,
            or_(
                Flashcard.next_review.is_(None),
                Flashcard.next_review <= utcnow(),
            ),
        )
        .count()
    )

    if due_left == 0:
        update_study_streak(recipient)
        db_session.commit()

    return jsonify({"status": "success"})


def update_study_streak(user: User):
    """
    Streak rules (based on São Paulo local dates):
    - If last == yesterday -> streak += 1
    - If last != today and last != yesterday -> reset to 1
    - If last == today -> unchanged
    """
    today_sp = now_sp().date()
    yesterday_sp = today_sp - timedelta(days=1)

    last = user.streak_last_date  # should be a DATE column ideally

    if last == yesterday_sp:
        user.study_streak = (user.study_streak or 0) + 1
        user.streak_last_date = today_sp

    elif last != today_sp:
        # Includes last is None, or older than yesterday
        user.study_streak = 1
        user.streak_last_date = today_sp

    # Track max streak
    if (user.study_streak or 0) > (user.max_study_streak or 0):
        user.max_study_streak = user.study_streak

    # Your chosen formula: points × max_study_streak
    user.max_points = (user.points or 0) * (user.max_study_streak or 0)


@bp.route("/manage/<student_id>", methods=["GET"])
@active_required
def manage_student(student_id):
    if not (current_user.is_teacher() or current_user.is_admin()):
        abort(403)

    student = db_session.query(User).filter_by(id=student_id).first()
    if not student:
        abort(403)

    if current_user.is_teacher() and student.assigned_teacher_id != current_user.id:
        abort(403)

    form = FlashcardForm()
    form.student_id.data = student.id

    flashcards = (
        db_session.query(Flashcard)
        .filter_by(user_id=student_id)
        .order_by(
            asc(Flashcard.reviewed_by_tc),
            Flashcard.next_review.is_(None),
            Flashcard.next_review.asc(),
        )
        .all()
    )

    due_flashcards = (
        db_session.query(func.count(Flashcard.id))
        .filter(
            Flashcard.user_id == student_id,
            or_(
                Flashcard.next_review.is_(None),
                Flashcard.next_review <= utcnow(),
            ),
        )
        .scalar()
        or 0
    )

    forms = {c.id: FlashcardForm(obj=c) for c in flashcards}

    return render_template(
        "flashcards/manage_student_cards.html",
        student=student,
        form=form,
        flashcards=flashcards,
        forms=forms,
        due_flashcards=due_flashcards,
    )


@bp.route("/flag_card", methods=["POST"])
@csrf.exempt
@login_required
def flag_card():
    """
    Let the user mark a flashcard as problematic during study mode.
    """
    data = request.get_json(silent=True) or {}
    card_id = data.get("card_id")
    reason_key = data.get("reason")

    if not card_id or not reason_key:
        return jsonify({"status": "error", "message": "Missing card_id or reason."}), 400

    flashcard = db_session.get(Flashcard, int(card_id))
    if not flashcard:
        return jsonify({"status": "error", "message": "Flashcard not found."}), 404

    if flashcard.user_id != current_user.id:
        return jsonify({"status": "error", "message": "Not authorized."}), 403

    REASON_LABELS = {
        "dont_understand": "I don't understand this flashcard",
        "talk_next_class": "I want to talk about this flashcard in my next class",
        "has_mistake": "I think this flashcard has a mistake",
    }
    reason_text = REASON_LABELS.get(reason_key, "Flagged for review")

    note = f"[NOTE] {reason_text}"
    if note not in (flashcard.question or ""):
        base = (flashcard.question or "").strip()
        flashcard.question = f"{base} ({note})" if base else note

    # 7 days later, São Paulo midnight -> UTC
    flashcard.next_review = sp_midnight_utc_days_from_now(7)
    flashcard.reviewed_by_tc = False

    db_session.commit()

    due_left = (
        db_session.query(Flashcard)
        .filter(
            Flashcard.user_id == current_user.id,
            or_(
                Flashcard.next_review.is_(None),
                Flashcard.next_review <= utcnow(),
            ),
        )
        .count()
    )

    if due_left == 0:
        update_study_streak(current_user)
    db_session.commit() 

    return jsonify(
        {
            "status": "success",
            "message": "Seu professor foi notificado.",
            "card_id": flashcard.id,
            "reason": reason_key,
        }
    )
