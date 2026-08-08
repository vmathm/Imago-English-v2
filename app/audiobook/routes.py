import os
from flask import Blueprint, flash, redirect, render_template, jsonify, request, url_for, abort
from flask_login import current_user, login_required
from app.decorators import active_required
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
from app.audiobook.forms import UserAudiobookForm   
from app.gcs_utils import delete_file_from_gcs_by_url, upload_file_to_gcs
from app.models.user_audiobook import UserAudiobook
from werkzeug.exceptions import Forbidden   
from app.models import User   
from app.utils.time import utcnow

bp = Blueprint('audiobook', __name__, url_prefix='/audiobook')

@bp.route('/audiobooks')
@login_required
def audiobooks():
    from app.models import User, UserAudiobook  # adjust import path if needed

    # Default: current user
    target_user = current_user
    student = None

    
    student_id = request.args.get("user_id", type=str)

    if student_id and student_id != str(current_user.id):
        
        if not (current_user.is_teacher() or current_user.is_admin()):
            abort(403)

        student = db_session.query(User).get(student_id)
        if not student or student.role != "student":
            abort(404)

        # If it's a teacher (not admin), enforce assignment
        if current_user.is_teacher() and not current_user.is_admin():
            if getattr(student, "assigned_teacher_id", None) != current_user.id:
                abort(403)

        target_user = student

    # Fetch audiobook for the resolved target user
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
            current_app.logger.exception("Failed to fetch audiobook text from GCS")

    return render_template(
        "audiobooks.html",
        audiobook=audiobook,
        text_content=text_content,
        student=student,          # None if it's the current_user
        target_user=target_user,  # whoever we're showing
    )



@bp.route("/translate", methods=["POST"])
@login_required
def translate_route():
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "Missing 'text' in request"}), 400

    translation = translate_text(data["text"])
    return jsonify({"translation": translation})




@bp.route("/assign_audiobook/<string:user_id>", methods=["POST"])
@login_required
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


@bp.route("/read/<string:book_slug>/<string:chapter_slug>")
def read_chapter(book_slug, chapter_slug):
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

    # Ensure anonymous visitors have a GuestUser workspace.
    if not current_user.is_authenticated:
        get_or_create_guest_user()

    bucket_name = current_app.config.get(
        "GCS_AUDIOBOOK_BUCKET"
    )

    if not bucket_name:
        current_app.logger.error(
            "GCS_AUDIOBOOK_BUCKET is not configured."
        )
        abort(500)

    audio_url = (
        f"https://storage.googleapis.com/"
        f"{bucket_name}/"
        f"{chapter.audio_object_name}"
    )

    previous_chapter = (
        db_session.query(Chapter)
        .filter(
            Chapter.book_id == book.id,
            Chapter.position < chapter.position,
        )
        .order_by(Chapter.position.desc())
        .first()
    )

    next_chapter = (
        db_session.query(Chapter)
        .filter(
            Chapter.book_id == book.id,
            Chapter.position > chapter.position,
        )
        .order_by(Chapter.position.asc())
        .first()
    )

    if current_user.is_authenticated:
        progress = (
            db_session.query(UserChapterProgress)
            .filter_by(
                user_id=current_user.id,
                chapter_id=chapter.id,
            )
            .first()
        )
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




    return render_template(
        "audiobooks.html",
        audiobook={
            "title": f"{book.title} — {chapter.title}",
            "audio_url": audio_url,
        },
        text_content=chapter.text_content,
        book=book,
        chapter=chapter,
        progress=progress,
        previous_chapter=previous_chapter,
        next_chapter=next_chapter,
        library_mode=True,
        guest_mode=not current_user.is_authenticated,
    )



@bp.route(
    "/read/<string:book_slug>/<string:chapter_slug>/mark-read",
    methods=["POST"],
)
@active_required
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