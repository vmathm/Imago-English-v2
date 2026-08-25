from flask import Blueprint, current_app, render_template, request, redirect, url_for, abort, flash, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.gcs_utils import delete_file_from_gcs_by_url, upload_file_to_gcs
from app.models import User, Flashcard, Book, Chapter, SuggestedFlashcard
from app.database import db_session
from functools import wraps
from pathlib import Path
from uuid import uuid4
from google.cloud import storage
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from app.admin.forms import (
    AssignStudentForm, 
    UnassignStudentForm, 
    ChangeRoleForm, 
    DeleteUserForm, 
    ToggleActiveStatusForm, 
    ChangeStudentLevelForm,
    UpdateLearningLanguageForm,
    BookForm,
    ChapterForm,
    EditChapterForm,
    EditBookForm
)


bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapped(*args, **kwargs):
        if not current_user.is_admin():
            abort(403)
        return fn(*args, **kwargs)
    return wrapped



@bp.route('/assign_student', methods=['POST'])
@admin_required
def assign_student():
    form = AssignStudentForm()
    form.student_id.choices = [(s.id, s.name) for s in db_session.query(User).filter_by(role='student').all()]
    form.teacher_id.choices = [(t.id, t.name) for t in db_session.query(User).filter_by(role='teacher').all()]

    if form.validate_on_submit():
        student = db_session.query(User).filter_by(id=form.student_id.data, role='student').first()
        teacher = db_session.query(User).filter_by(id=form.teacher_id.data, role='teacher').first()
        if not student or not teacher:
            flash('Invalid selection', 'danger')
            return redirect(url_for('dashboard.index'))

        student.assigned_teacher_id = teacher.id
        student.active = True 
        student.billing_mode='external'
        db_session.commit()
        flash(f'{student.name} assigned to {teacher.name}', 'success')
    else:
        flash('Invalid form submission', 'danger')

    return redirect(url_for('dashboard.index'))


@bp.route('/unassign_student', methods=['POST'])
@admin_required
def unassign_student():
    form = UnassignStudentForm()
    form.student_id.choices = [(s.id, s.name) for s in db_session.query(User).filter_by(role='student').all()]

    if form.validate_on_submit():
        student = db_session.query(User).filter_by(id=form.student_id.data, role='student').first()
        if not student:
            flash('Invalid student', 'danger')
            return redirect(url_for('dashboard.index'))

        student.assigned_teacher_id = None
        student.active = False
        db_session.commit()
        flash(f'{student.name} unassigned', 'success')
    else:
        flash('Invalid form submission', 'danger')

    return redirect(url_for('dashboard.index'))




@bp.route('/change_role', methods=['POST'])
@admin_required
def change_role():
    from app.models.billing import Tenant  # 👈 import here to avoid circular issues

    form = ChangeRoleForm()
    form.user_id.choices = [(u.id, u.name) for u in db_session.query(User).all()]
    form.role.choices = [('student', 'Student'), ('teacher', 'Teacher'), ('@dmin!', 'Admin')]

    if form.validate_on_submit():
        user = db_session.query(User).filter_by(id=form.user_id.data).first()

        if not user or user.id == current_user.id:
            flash('User not found / cannot change your own role.', 'danger')
            return redirect(url_for('dashboard.index'))

        new_role = form.role.data

        # 🔥 CRITICAL FIX: block teacher → student if tenant exists
        if user.role == 'teacher' and new_role == 'student':
            tenant = db_session.query(Tenant).filter_by(owner_user_id=user.id).first()
            if tenant:
                flash(
                    "This user owns a billing tenant. Delete or transfer the tenant before changing role.",
                    'danger'
                )
                return redirect(url_for('dashboard.index'))

        # ✅ apply role change
        user.role = new_role

        # Optional: your existing logic
        if user.role == 'student':
            user.active = False

        db_session.commit()
        flash(f"{user.name}'s role updated to {new_role}", 'success')

    else:
        flash('Invalid form submission', 'danger')

    return redirect(url_for('dashboard.index'))


@bp.route('/delete_user', methods=['POST'])
@admin_required
def delete_user():
    form = DeleteUserForm()
    form.user_id.choices = [(u.id, u.name) for u in db_session.query(User).all()]

    if form.validate_on_submit():
        user = db_session.query(User).filter_by(id=form.user_id.data).first()

        if user and user.role != '@dmin!' and user.id != current_user.id and user.role != 'teacher':
    
            db_session.delete(user)
            db_session.commit()
            flash(f"User {user.name} and their flashcards have been deleted", 'success')
        else:
            flash("User not found", 'danger')
    else:
        flash("Invalid form submission", 'danger')

    return redirect(url_for('dashboard.index'))

@bp.route('/toggle_active_status', methods=['POST'])
@admin_required
def toggle_active_status():
    form = ToggleActiveStatusForm()
    form.user_id.choices = [(u.id, u.name) for u in db_session.query(User).all()]

    if form.validate_on_submit():
        user = db_session.query(User).filter_by(id=form.user_id.data).first()
        if user and user.role != '@dmin!':
            user.active = not user.active
            db_session.commit()

            status = "activated" if user.active else "deactivated"
            flash(f"User {user.name} has been {status}.", 'success')
        else:
            flash("User not found", 'danger')
    else:
        flash("Invalid form submission", 'danger')

    return redirect(url_for('dashboard.index'))


@bp.route("/update_student_level", methods=["POST"])
@login_required
def update_student_level():
    form = ChangeStudentLevelForm()
    if not (current_user.is_teacher() or current_user.is_admin()):
        abort(403)

    if form.validate_on_submit():
        student = db_session.query(User).filter_by(id=form.student_id.data, role='student').first()
        if not student:
            flash("Student not found.", "danger")
        elif current_user.is_teacher() and student.assigned_teacher_id != current_user.id:
            abort(403)
        else:
            student.level = form.level.data
            db_session.commit()
            flash(f"{student.name}'s level updated to {form.level.data}", "success")
    else:
        flash("Invalid form submission.", "danger")

    return redirect(url_for("dashboard.index"))


@bp.route("/set_language/<student_id>", methods=["POST"])
@login_required
def set_language(student_id):
    form = UpdateLearningLanguageForm()

    # Only teachers and admins can change student language
    if not (current_user.is_teacher() or current_user.is_admin()):
        abort(403)

    if form.validate_on_submit():
        # Look up the student
        student = (
            db_session.query(User)
            .filter_by(id=student_id, role="student")
            .first()
        )
        if not student:
            flash("Student not found.", "danger")
            return redirect(url_for("dashboard.index"))

        # Optional: ensure teacher owns this student
        if current_user.is_teacher() and getattr(student, "assigned_teacher_id", None) != current_user.id:
            abort(403)

        # ✅ Update the student's language, not current_user
        student.learning_language = form.learning_language.data
        db_session.commit()

        flash(f"{student.name}'s learning language updated!", "success")
    else:
        print("set_language errors:", form.errors)
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, "danger")

    return redirect(url_for("dashboard.index"))


@bp.route("/books/create", methods=["GET", "POST"])
@admin_required
def create_book():
    form = BookForm()

    if form.validate_on_submit():
        title = form.title.data.strip()
        slug = form.slug.data.strip().lower()
        author = (
            form.author.data.strip()
            if form.author.data
            else None
        )
        description = (
            form.description.data.strip()
            if form.description.data
            else None
        )
        cover_object_name = (
            form.cover_object_name.data.strip()
            if form.cover_object_name.data
            else None
        )

        existing_slug = (
            db_session.query(Book)
            .filter_by(slug=slug)
            .first()
        )

        if existing_slug:
            flash(
                "A book with this slug already exists.",
                "danger",
            )
            return render_template(
                "admin/create_book.html",
                form=form,
            )

        book = Book(
            title=title,
            slug=slug,
            author=author,
            description=description,
            level=form.level.data,
            cover_object_name=cover_object_name,
        )

        db_session.add(book)
        db_session.commit()

        flash(
            f'Book "{book.title}" created successfully.',
            "success",
        )

        return redirect(
            url_for(
                "admin.create_book",
            )
        )

    return render_template(
        "admin/create_book.html",
        form=form,
    )






def upload_chapter_audio(audio_file, book_slug, chapter_slug):
    bucket_name = current_app.config.get("GCS_AUDIOBOOK_BUCKET")

    if not bucket_name:
        raise RuntimeError("GCS_AUDIOBOOK_BUCKET is not configured.")

    original_name = secure_filename(audio_file.filename)
    extension = Path(original_name).suffix.lower()

    object_name = (
        f"books/{book_slug}/chapters/"
        f"{chapter_slug}-{uuid4().hex}{extension}"
    )

    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(object_name)

    audio_file.stream.seek(0)

    blob.upload_from_file(
        audio_file.stream,
        content_type=audio_file.mimetype,
        rewind=True,
    )

    return object_name


@bp.route("/books")
@admin_required
def books():
    books = (
        db_session.query(Book)
        .order_by(Book.title.asc())
        .all()
    )

    return render_template(
        "admin/books.html",
        books=books,
    )


@bp.route("/books/<int:book_id>")
@admin_required
def book_details(book_id):
    book = db_session.get(Book, book_id)

    if not book:
        abort(404)

    return redirect(
        url_for(
            "audiobook.book_details",
            book_slug=book.slug,
        )
    )



@bp.route("/create/chapter", methods=["GET", "POST"])
@admin_required
def create_chapter():
    books = (
        db_session.query(Book)
        .order_by(Book.title.asc())
        .all()
    )

    if not books:
        flash(
            "Create a book before adding chapters.",
            "warning",
        )
        return redirect(
            url_for("admin.create_book")
        )

    form = ChapterForm()

    form.book_id.choices = [
        (
            book.id,
            f"{book.title} — {book.author or 'Unknown author'}",
        )
        for book in books
    ]

    selected_book_id = request.args.get(
        "book_id",
        type=int,
    )

    if request.method == "GET" and selected_book_id:
        valid_book_ids = {
            book.id
            for book in books
        }

        if selected_book_id in valid_book_ids:
            form.book_id.data = selected_book_id

    if form.validate_on_submit():
        book = db_session.get(
            Book,
            form.book_id.data,
        )

        if not book:
            flash(
                "Book not found.",
                "danger",
            )
            return redirect(
                url_for("admin.create_chapter")
            )

        chapter_slug = (
            form.slug.data
            .strip()
        )

        existing_slug = (
            db_session.query(Chapter)
            .filter_by(
                book_id=book.id,
                slug=chapter_slug,
            )
            .first()
        )

        if existing_slug:
            flash(
                "A chapter with this slug already exists for this book.",
                "danger",
            )

            return render_template(
                "admin/create_chapter.html",
                form=form,
            )

        existing_position = (
            db_session.query(Chapter)
            .filter_by(
                book_id=book.id,
                position=form.position.data,
            )
            .first()
        )

        if existing_position:
            flash(
                "A chapter already uses this position in this book.",
                "danger",
            )

            return render_template(
                "admin/create_chapter.html",
                form=form,
            )

        # Files are optional.
        text_path = None
        audio_path = None

        if form.text_file.data:
            text_file = form.text_file.data

            text_path = upload_file_to_gcs(
                text_file.stream,
                prefix=(
                    f"library/{book.slug}/"
                    f"{chapter_slug}/text"
                ),
                content_type=(
                    text_file.mimetype
                    or "text/plain"
                ),
            )

        if form.audio_file.data:
            audio_file = form.audio_file.data

            audio_path = upload_file_to_gcs(
                audio_file.stream,
                prefix=(
                    f"library/{book.slug}/"
                    f"{chapter_slug}/audio"
                ),
                content_type=(
                    audio_file.mimetype
                    or "audio/mpeg"
                ),
            )

        chapter = Chapter(
            book_id=book.id,
            title=form.title.data.strip(),
            slug=chapter_slug,
            position=form.position.data,
            text_path=text_path,
            audio_path=audio_path,
            is_free=bool(form.is_free.data),
        )

        db_session.add(chapter)
        db_session.commit()

        flash(
            f'Chapter "{chapter.title}" added to "{book.title}".',
            "success",
        )

        return redirect(
            url_for(
                "admin.create_chapter",
                book_id=book.id,
            )
        )

    return render_template(
        "admin/create_chapter.html",
        form=form,
    )



@bp.route("/chapters/<int:chapter_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_chapter(chapter_id):
    chapter = db_session.get(Chapter, chapter_id)

    if not chapter:
        abort(404)

    books = (
        db_session.query(Book)
        .order_by(Book.title.asc())
        .all()
    )

    form = EditChapterForm(obj=chapter)

    form.book_id.choices = [
        (book.id, f"{book.title} ({book.level})")
        for book in books
    ]

    if request.method == "GET":
        form.book_id.data = chapter.book_id

    if form.validate_on_submit():
        new_book = db_session.get(Book, form.book_id.data)

        if not new_book:
            abort(404)

        title = form.title.data.strip()
        slug = form.slug.data.strip().lower()
        position = form.position.data

        # Check slug uniqueness, excluding this chapter.
        existing_slug = (
            db_session.query(Chapter)
            .filter(
                Chapter.book_id == new_book.id,
                Chapter.slug == slug,
                Chapter.id != chapter.id,
            )
            .first()
        )

        if existing_slug:
            flash(
                "This book already has a chapter with that slug.",
                "danger",
            )
            return render_template(
                "admin/edit_chapter.html",
                form=form,
                chapter=chapter,
            )

        # Check position uniqueness, excluding this chapter.
        existing_position = (
            db_session.query(Chapter)
            .filter(
                Chapter.book_id == new_book.id,
                Chapter.position == position,
                Chapter.id != chapter.id,
            )
            .first()
        )

        if existing_position:
            flash(
                "This book already has a chapter in that position.",
                "danger",
            )
            return render_template(
                "admin/edit_chapter.html",
                form=form,
                chapter=chapter,
            )

        old_text_path = chapter.text_path
        old_audio_path = chapter.audio_path

        new_text_path = None
        new_audio_path = None

        try:
            # Upload replacement text only if one was provided.
            if form.text_file.data:
                text_file = form.text_file.data

                new_text_path = upload_file_to_gcs(
                    text_file.stream,
                    prefix=f"library/{new_book.slug}/{slug}/text",
                    content_type=text_file.mimetype or "text/plain",
                )

            # Upload replacement audio only if one was provided.
            if form.audio_file.data:
                audio_file = form.audio_file.data

                new_audio_path = upload_file_to_gcs(
                    audio_file.stream,
                    prefix=f"library/{new_book.slug}/{slug}/audio",
                    content_type=audio_file.mimetype or "audio/mpeg",
                )

            # Update metadata.
            chapter.book_id = new_book.id
            chapter.title = title
            chapter.slug = slug
            chapter.position = position
            chapter.is_free = form.is_free.data

            # Replace paths only when new files were uploaded.
            if new_text_path:
                chapter.text_path = new_text_path

            if new_audio_path:
                chapter.audio_path = new_audio_path

            db_session.commit()

        except IntegrityError:
            db_session.rollback()

            # New files were uploaded but never became the
            # committed chapter files, so clean them up.
            if new_text_path:
                delete_file_from_gcs_by_url(new_text_path)

            if new_audio_path:
                delete_file_from_gcs_by_url(new_audio_path)

            flash(
                "A chapter with this slug or position already exists.",
                "danger",
            )

            return render_template(
                "admin/edit_chapter.html",
                form=form,
                chapter=chapter,
            )

        except Exception:
            db_session.rollback()

            # Avoid leaving orphaned replacement files in GCS.
            if new_text_path:
                delete_file_from_gcs_by_url(new_text_path)

            if new_audio_path:
                delete_file_from_gcs_by_url(new_audio_path)

            current_app.logger.exception(
                "Chapter update failed."
            )

            flash(
                "The chapter could not be updated.",
                "danger",
            )

            return render_template(
                "admin/edit_chapter.html",
                form=form,
                chapter=chapter,
            )

        # DB commit succeeded. We can now safely remove
        # the files that were replaced.
        if new_text_path and old_text_path != new_text_path:
            delete_file_from_gcs_by_url(old_text_path)

        if new_audio_path and old_audio_path != new_audio_path:
            delete_file_from_gcs_by_url(old_audio_path)

        flash(
            f'Chapter "{chapter.title}" updated successfully.',
            "success",
        )

        return redirect(
            url_for("audiobook.library")
        )

    return render_template(
        "admin/edit_chapter.html",
        form=form,
        chapter=chapter,
    )




@bp.route("/chapters/<int:chapter_id>/delete", methods=["POST"])
@admin_required
def delete_chapter(chapter_id):
    chapter = db_session.get(Chapter, chapter_id)

    if not chapter:
        abort(404)

    book_id = chapter.book_id
    chapter_title = chapter.title

    text_path = chapter.text_path
    audio_path = chapter.audio_path

    try:
        db_session.delete(chapter)
        db_session.commit()

    except Exception:
        db_session.rollback()

        current_app.logger.exception(
            "Could not delete chapter from database."
        )

        flash(
            "The chapter could not be deleted.",
            "danger",
        )

        return redirect(
            url_for(
                "admin.book_details",
                book_id=book_id,
            )
        )

    # DB deletion succeeded.
    # Now clean up the files in GCS.
    if text_path:
        delete_file_from_gcs_by_url(text_path)

    if audio_path:
        delete_file_from_gcs_by_url(audio_path)

    flash(
        f'Chapter "{chapter_title}" deleted successfully.',
        "success",
    )

    return redirect(
        url_for(
            "admin.book_details",
            book_id=book_id,
        )
    )

@bp.route("/books/<int:book_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_book(book_id):
    book = db_session.get(Book, book_id)

    if not book:
        abort(404)

    form = EditBookForm(obj=book)

    if form.validate_on_submit():
        title = form.title.data.strip()
        slug = form.slug.data.strip().lower()

        existing_slug = (
            db_session.query(Book)
            .filter(
                Book.slug == slug,
                Book.id != book.id,
            )
            .first()
        )

        if existing_slug:
            flash(
                "Another book already uses this slug.",
                "danger",
            )

            return render_template(
                "admin/edit_book.html",
                form=form,
                book=book,
            )

        book.title = title
        book.slug = slug
        book.author = (
            form.author.data.strip()
            if form.author.data
            else None
        )
        book.description = (
            form.description.data.strip()
            if form.description.data
            else None
        )
        book.level = form.level.data

        db_session.commit()

        flash(
            f'Book "{book.title}" updated successfully.',
            "success",
        )

        return redirect(
            url_for(
                "audiobook.book_details",
                book_slug=book.slug,
            )
        )

    return render_template(
        "admin/edit_book.html",
        form=form,
        book=book,
    )



@bp.route("/books/<int:book_id>/delete", methods=["POST"])
@admin_required
def delete_book(book_id):
    book = db_session.get(Book, book_id)

    if not book:
        abort(404)

    book_title = book.title

    chapters = (
        db_session.query(Chapter)
        .filter_by(book_id=book.id)
        .all()
    )

    chapter_files = [
        {
            "text_path": chapter.text_path,
            "audio_path": chapter.audio_path,
        }
        for chapter in chapters
    ]

    try:
        db_session.delete(book)
        db_session.commit()

    except Exception:
        db_session.rollback()

        current_app.logger.exception(
            "Could not delete library book from database."
        )

        flash(
            "The book could not be deleted.",
            "danger",
        )

        return redirect(
            url_for(
                "audiobook.book_details",
                book_slug=book.slug,
            )
        )

    # Database deletion succeeded.
    # Now clean up chapter files in GCS.
    for files in chapter_files:

        if files["text_path"]:
            delete_file_from_gcs_by_url(
                files["text_path"]
            )

        if files["audio_path"]:
            delete_file_from_gcs_by_url(
                files["audio_path"]
            )

    flash(
        f'Book "{book_title}" deleted successfully.',
        "success",
    )

    return redirect(
        url_for("audiobook.library")
    )




@bp.route(
    "/chapter/<int:chapter_id>/enable-activity",
    methods=["POST"],
)
@admin_required
def enable_activity(chapter_id):
    chapter = db_session.get(Chapter, chapter_id)

    if not chapter:
        abort(404)

    chapter.activity_enabled = True
    db_session.commit()

    flash("Reading activity created.", "success")

    return redirect(request.referrer or url_for("dashboard.index"))




@bp.route(
    "/chapter/<int:chapter_id>/suggested-flashcards",
    methods=["POST"],
)
@admin_required
def add_suggested_flashcard(chapter_id):
    chapter = db_session.get(Chapter, chapter_id)

    if not chapter:
        abort(404)

    if not chapter.activity_enabled:
        return jsonify({
            "status": "error",
            "message": "Enable the reading activity first.",
        }), 400

    data = request.get_json() or {}

    question = (data.get("question") or "").strip()
    answer = (data.get("answer") or "").strip()

    if not question or not answer:
        return jsonify({
            "status": "error",
            "message": "Question and answer are required.",
        }), 400

    existing = (
        db_session.query(SuggestedFlashcard)
        .filter_by(
            chapter_id=chapter.id,
            question=question,
        )
        .first()
    )

    if existing:
        return jsonify({
            "status": "error",
            "message": "This suggested flashcard already exists.",
        }), 409

    max_position = (
        db_session.query(func.max(SuggestedFlashcard.position))
        .filter_by(chapter_id=chapter.id)
        .scalar()
    )

    new_suggestion = SuggestedFlashcard(
        chapter_id=chapter.id,
        question=question,
        answer=answer,
        position=(max_position or 0) + 1,
    )

    db_session.add(new_suggestion)
    db_session.commit()

    return jsonify({
        "status": "success",
        "message": "Suggested flashcard added.",
        "suggested_flashcard": {
            "id": new_suggestion.id,
            "question": new_suggestion.question,
            "answer": new_suggestion.answer,
            "position": new_suggestion.position,
        },
    })



@bp.route(
    "/suggested-flashcards/<int:card_id>/delete",
    methods=["POST"],
)
@admin_required
def delete_suggested_flashcard(card_id):
    card = db_session.get(SuggestedFlashcard, card_id)

    if not card:
        abort(404)

    chapter_id = card.chapter_id
    deleted_position = card.position

    db_session.delete(card)
    db_session.flush()

    remaining = (
        db_session.query(SuggestedFlashcard)
        .filter_by(chapter_id=chapter_id)
        .order_by(SuggestedFlashcard.position)
        .all()
    )

    for index, suggestion in enumerate(remaining, start=1):
        suggestion.position = index

    db_session.commit()

    return jsonify({
        "status": "success",
        "message": "Suggested flashcard deleted.",
        "card_id": card_id,
    })