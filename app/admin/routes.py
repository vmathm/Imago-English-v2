from flask import Blueprint, current_app, render_template, request, redirect, url_for, abort, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import User, Flashcard, Book, Chapter
from app.database import db_session
from functools import wraps
from pathlib import Path
from uuid import uuid4
from google.cloud import storage
from sqlalchemy.exc import IntegrityError
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

@bp.route("/chapters/create", methods=["GET", "POST"])
@admin_required
def create_chapter():
    form = ChapterForm()

    books = (
        db_session.query(Book)
        .order_by(Book.title.asc())
        .all()
    )

    if not books:
        flash(
            "Create a book before uploading a chapter.",
            "warning",
        )
        return redirect(url_for("admin.create_book"))

    form.book_id.choices = [
        (book.id, f"{book.title} ({book.level})")
        for book in books
    ]

    selected_book_id = request.args.get(
        "book_id",
        type=int,
    )

    if request.method == "GET" and selected_book_id:
        valid_book_ids = {book.id for book in books}

        if selected_book_id in valid_book_ids:
            form.book_id.data = selected_book_id

    if form.validate_on_submit():
        book = db_session.get(Book, form.book_id.data)

        if not book:
            abort(404)

        title = form.title.data.strip()
        slug = form.slug.data.strip().lower()
        position = form.position.data
        text_file = form.text_file.data
        audio_file = form.audio_file.data

        try:
            text_bytes = text_file.read()
            text_content = text_bytes.decode("utf-8")
        except UnicodeDecodeError:
            flash(
                "The text file must use UTF-8 encoding.",
                "danger",
            )
            return render_template(
                "admin/create_chapter.html",
                form=form,
            )

        text_content = text_content.strip()

        if not text_content:
            flash("The text file is empty.", "danger")
            return render_template(
                "admin/create_chapter.html",
                form=form,
            )

        existing_slug = (
            db_session.query(Chapter)
            .filter_by(
                book_id=book.id,
                slug=slug,
            )
            .first()
        )

        if existing_slug:
            flash(
                "This book already has a chapter with that slug.",
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
                position=position,
            )
            .first()
        )

        if existing_position:
            flash(
                "This book already has a chapter in that position.",
                "danger",
            )
            return render_template(
                "admin/create_chapter.html",
                form=form,
            )

        audio_object_name = None

        try:
            audio_object_name = upload_chapter_audio(
                audio_file=audio_file,
                book_slug=book.slug,
                chapter_slug=slug,
            )

            chapter = Chapter(
                book_id=book.id,
                title=title,
                slug=slug,
                position=position,
                text_content=text_content,
                audio_object_name=audio_object_name,
                is_free=form.is_free.data,
            )

            db_session.add(chapter)
            db_session.commit()

        except IntegrityError:
            db_session.rollback()

            flash(
                "A chapter with this slug or position already exists.",
                "danger",
            )

            return render_template(
                "admin/create_chapter.html",
                form=form,
            )

        except Exception:
            db_session.rollback()

            if audio_object_name:
                try:
                    client = storage.Client()
                    bucket = client.bucket(
                        current_app.config["GCS_AUDIOBOOK_BUCKET"]
                    )
                    bucket.blob(audio_object_name).delete()
                except Exception:
                    current_app.logger.exception(
                        "Could not delete orphaned chapter audio."
                    )

            current_app.logger.exception(
                "Chapter upload failed."
            )

            flash(
                "The chapter could not be uploaded.",
                "danger",
            )

            return render_template(
                "admin/create_chapter.html",
                form=form,
            )

        flash(
            f'Chapter "{chapter.title}" added to "{book.title}".',
            "success",
        )

        return redirect(
            url_for(
                "admin.book_details",
                book_id=book.id,
            )
        )

    return render_template(
        "admin/create_chapter.html",
        form=form,
    )

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

    chapters = (
        db_session.query(Chapter)
        .filter_by(book_id=book.id)
        .order_by(Chapter.position.asc())
        .all()
    )

    return render_template(
        "admin/book_details.html",
        book=book,
        chapters=chapters,
    )