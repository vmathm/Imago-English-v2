import os
from flask import Blueprint, flash, redirect, render_template, jsonify, request, url_for, abort, g
from flask_login import current_user, login_required
from sqlalchemy.exc import IntegrityError
from app.admin.routes import admin_required
from app.decorators import active_required, user_or_guest_required
from app.flashcard.form import FlashcardForm
from app.models.book import Book
from app.models.chapter import Chapter
from app.models.chapter_progress import GuestChapterProgress, UserChapterProgress
from app.services.guest_session import get_or_create_guest_user
from app.services.translate import translate_text
from app.database import db_session
from app.models.user_audiobook import UserAudiobook
import requests
from flask import current_app
from app.audiobook.forms import EditChapterForm, UserAudiobookForm   
from app.gcs_utils import delete_file_from_gcs_by_url, upload_file_to_gcs
from werkzeug.exceptions import Forbidden   
from app.models import User, UserAudiobook 
from app.utils.time import utcnow

bp = Blueprint('audiobook', __name__, url_prefix='/audiobook')
@bp.route('/audiobooks')
@login_required
def audiobooks():

    if current_user.role == "student" and not current_user.assigned_teacher_id:
        abort(403)

    target_user = current_user
    student = None

    student_id = request.args.get("user_id", type=str)

    if student_id and student_id != str(current_user.id):

        if not (current_user.is_teacher() or current_user.is_admin()):
            abort(403)

        student = db_session.get(User, student_id)

        if not student or student.role != "student":
            abort(404)

        if current_user.is_teacher() and not current_user.is_admin():
            if student.assigned_teacher_id != current_user.id:
                abort(403)

        target_user = student

    audiobook = (
        db_session.query(UserAudiobook)
        .filter_by(user_id=target_user.id)
        .first()
    )

    text_content = None

    if audiobook and audiobook.text_url:
        try:
            resp = requests.get(audiobook.text_url, timeout=5)
            resp.raise_for_status()
            text_content = resp.text
        except Exception:
            current_app.logger.exception(
                "Failed to fetch audiobook text from GCS"
            )

    return render_template(
        "audiobooks.html",
        audiobook=audiobook,
        text_content=text_content,
        student=student,
        target_user=target_user,
    )


@bp.route("/translate", methods=["POST"])
@user_or_guest_required
def translate_route():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' in request"}), 400

    translation = translate_text(data["text"])
    return jsonify({"translation": translation})




@bp.route("/assign_audiobook/<string:user_id>", methods=["POST"])
@user_or_guest_required
def assign_audiobook(user_id):
    if not (current_user.is_teacher() or current_user.is_admin()):
        raise Forbidden("You are not allowed to assign audiobooks.")

    form = UserAudiobookForm()
    if not form.validate_on_submit():
        flash("Erro ao enviar o audiobook. Verifique os arquivos e tente novamente.", "danger")
        return redirect(url_for("dashboard.index"))

    student = db_session.query(User).get(user_id)
    if not student or student.role != "student":
        abort(404)

    text_file = form.text_file.data
    audio_file = form.audio_file.data

    # Detect if new files were actually selected
    has_new_text = bool(text_file and getattr(text_file, "filename", "").strip())
    has_new_audio = bool(audio_file and getattr(audio_file, "filename", "").strip())

    ua = db_session.query(UserAudiobook).filter_by(user_id=student.id).first()

    # ✅ If no new files were selected, treat this as a "clear audiobook" action
    if not has_new_text and not has_new_audio:
        if ua:
            # Delete existing files from GCS (if any)
            if ua.text_url:
                delete_file_from_gcs_by_url(ua.text_url)
            if ua.audio_url:
                delete_file_from_gcs_by_url(ua.audio_url)

            # Delete the DB row
            db_session.delete(ua)
            db_session.commit()
            flash("Load audiobook button enabled for user.", "success")
        else:
            flash("Nenhum arquivo selecionado para upload.", "warning")

        return redirect(url_for("dashboard.index"))

    # From here on, we know at least one new file was uploaded
    if not ua:
        ua = UserAudiobook(user_id=student.id)

    # Title logic: use new filenames if any, else keep existing title
    raw_name = None
    if has_new_text:
        raw_name = text_file.filename
    elif has_new_audio:
        raw_name = audio_file.filename

    if raw_name:
        base_name = os.path.splitext(os.path.basename(raw_name))[0]
        ua.title = base_name.strip() or ua.title

    # Handle text file upload (only touch if new text provided)
    if has_new_text:
        if ua.text_url:
            delete_file_from_gcs_by_url(ua.text_url)

        ua.text_url = upload_file_to_gcs(
            text_file,
            prefix=f"user_{student.id}/audiobook_text.txt",
            content_type="text/plain",
        )

    # Handle audio file upload (only touch if new audio provided)
    if has_new_audio:
        if ua.audio_url:
            delete_file_from_gcs_by_url(ua.audio_url)

        ua.audio_url = upload_file_to_gcs(
            audio_file,
            prefix=f"user_{student.id}/audiobook_audio.mp3",
            content_type="audio/mpeg",
        )

    # Safety: if somehow we end up with no text or audio, remove the row
    if not (ua.text_url or ua.audio_url):
        db_session.delete(ua)
        db_session.commit()
        flash("Load audiobook button enabled for user.", "success")
        return redirect(url_for("dashboard.index"))

    db_session.add(ua)
    db_session.commit()

    flash(f"Audiobook enviado/atualizado para {student.user_name or student.name}.", "success")
    return redirect(url_for("dashboard.index"))




@bp.route(
    "/read/<string:book_slug>/<string:chapter_slug>/mark-read",
    methods=["POST"],
)
@user_or_guest_required
def mark_chapter_read(book_slug, chapter_slug):
    book = (
        db_session.query(Book)
        .filter_by(slug=book_slug)
        .first()
    )

    if not book:
        abort(404)

    chapter = (
        db_session.query(Chapter)
        .filter_by(
            book_id=book.id,
            slug=chapter_slug,
        )
        .first()
    )

    if not chapter:
        abort(404)

    now = utcnow()

    if current_user.is_authenticated:
        progress = (
            db_session.query(UserChapterProgress)
            .filter_by(
                user_id=current_user.id,
                chapter_id=chapter.id,
            )
            .first()
        )

        if progress is None:
            progress = UserChapterProgress(
                user_id=current_user.id,
                chapter_id=chapter.id,
            )
            db_session.add(progress)

    else:
        guest_user = get_or_create_guest_user()

        progress = (
            db_session.query(GuestChapterProgress)
            .filter_by(
                guest_user_id=guest_user.id,
                chapter_id=chapter.id,
            )
            .first()
        )

        if progress is None:
            progress = GuestChapterProgress(
                guest_user_id=guest_user.id,
                chapter_id=chapter.id,
            )
            db_session.add(progress)

    progress.is_read = True
    progress.completed_at = now
    progress.updated_at = now

    db_session.commit()

    flash(
        f'"{chapter.title}" marked as read.',
        "success",
    )

    return redirect(
        url_for(
            "audiobook.read_chapter",
            book_slug=book.slug,
            chapter_slug=chapter.slug,
        )
    )

@bp.route("/library")
@user_or_guest_required
def library():

    query = (
        db_session.query(Book)
        .filter(Book.chapters.any())
    )

    if current_user.is_authenticated:

        # Only students are level-restricted.
        if current_user.role == "student":
            if not current_user.level:
                abort(403)

            query = query.filter(
                Book.level == current_user.level
            )

    else:
        # Guests are also level-restricted.
        guest_user = g.guest_user

        if not guest_user or not guest_user.level:
            abort(403)

        query = query.filter(
            Book.level == guest_user.level
        )

    books = (
        query
        .order_by(Book.title.asc())
        .all()
    )

    return render_template(
        "library.html",
        books=books,
    )
@bp.route("/library/<string:book_slug>")
@user_or_guest_required
def book_details(book_slug):
    book = (
        db_session.query(Book)
        .filter_by(slug=book_slug)
        .first()
    )

    if not book:
        abort(404)

    chapters = (
        db_session.query(Chapter)
        .filter_by(book_id=book.id)
        .order_by(Chapter.position.asc())
        .all()
    )

    chapter_ids = [chapter.id for chapter in chapters]

    read_chapter_ids = set()

    if chapter_ids:

        # Registered user
        if current_user.is_authenticated:
            progress_rows = (
                db_session.query(UserChapterProgress)
                .filter(
                    UserChapterProgress.user_id == current_user.id,
                    UserChapterProgress.chapter_id.in_(chapter_ids),
                    UserChapterProgress.is_read.is_(True),
                )
                .all()
            )

        # Guest user
        else:
            guest_user = g.guest_user

            progress_rows = (
                db_session.query(GuestChapterProgress)
                .filter(
                    GuestChapterProgress.guest_user_id == guest_user.id,
                    GuestChapterProgress.chapter_id.in_(chapter_ids),
                    GuestChapterProgress.is_read.is_(True),
                )
                .all()
            )

        read_chapter_ids = {
            progress.chapter_id
            for progress in progress_rows
        }

        next_chapter = next(
            (
                chapter
                for chapter in chapters
                if chapter.id not in read_chapter_ids
            ),
            None,
        )


    return render_template(
        "book_details.html",
        book=book,
        chapters=chapters,
        read_chapter_ids=read_chapter_ids,
        read_count=len(read_chapter_ids),
        total_chapters=len(chapters),
        next_chapter=next_chapter
    )

@bp.route("/library/<string:book_slug>/<string:chapter_slug>")
@user_or_guest_required
def read_chapter(book_slug, chapter_slug):
    book = (
        db_session.query(Book)
        .filter_by(slug=book_slug)
        .first()
    )

    

    if not book:
        abort(404)

    chapters = (
        db_session.query(Chapter)
        .filter_by(book_id=book.id)
        .order_by(Chapter.position.asc())
        .all()
    )

    chapter = next(
        (c for c in chapters if c.slug == chapter_slug),
        None,
    )

    if not chapter:
        abort(404)

    # Fetch chapter text from GCS
    text_content = None

    try:
        response = requests.get(
            chapter.text_path,
            timeout=10,
        )
        response.raise_for_status()
        text_content = response.text

    except requests.RequestException:
        current_app.logger.exception(
            "Failed to fetch library chapter text from GCS."
        )

        flash(
            "The chapter text could not be loaded.",
            "danger",
        )

    # Previous / next chapter
    chapter_index = chapters.index(chapter)

    previous_chapter = (
        chapters[chapter_index - 1]
        if chapter_index > 0
        else None
    )

    next_chapter = (
        chapters[chapter_index + 1]
        if chapter_index < len(chapters) - 1
        else None
    )


    activity_mode = chapter.activity_enabled

    

    # Current reading progress
    if current_user.is_authenticated:
        progress = (
            db_session.query(UserChapterProgress)
            .filter_by(
                user_id=current_user.id,
                chapter_id=chapter.id,
            )
            .first()
        )

        guest_mode = False

    else:
        progress = (
            db_session.query(GuestChapterProgress)
            .filter_by(
                guest_user_id=g.guest_user.id,
                chapter_id=chapter.id,
            )
            .first()
        )

        guest_mode = True

    return render_template(
        "audiobooks.html",
        library_mode=True,
        guest_mode=guest_mode,
        book=book,
        chapter=chapter,
        text_content=text_content,
        progress=progress,
        previous_chapter=previous_chapter,
        next_chapter=next_chapter,

        # This route is not displaying a private UserAudiobook.
        audiobook=None,
        activity_mode=activity_mode,
    )



@bp.route("/join/chapter/<int:chapter_id>")
def join_chapter_activity(chapter_id):
    chapter = db_session.get(Chapter, chapter_id)

    if not chapter:
        abort(404)

    if not chapter.activity_enabled:
        abort(404)

    book = db_session.get(Book, chapter.book_id)

    if not book:
        abort(404)

    if not current_user.is_authenticated:
        guest_user = get_or_create_guest_user()

        guest_user.level = book.level
        db_session.commit()

    return redirect(
        url_for(
            "audiobook.read_chapter",
            book_slug=book.slug,
            chapter_slug=chapter.slug,
        )
    )