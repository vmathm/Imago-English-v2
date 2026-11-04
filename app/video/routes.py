from urllib.parse import urlparse, parse_qs

from flask import Blueprint, abort, render_template, current_app, flash, request
import requests
from app.database import db_session
from app.models import Video
from flask_login import current_user
from app.services.guest_session import get_or_create_guest_user


bp = Blueprint(
    "video",
    __name__,
    url_prefix="/videos",
)


def get_youtube_embed_url(url):
    parsed = urlparse(url)

    # youtube.com/watch?v=VIDEO_ID
    if parsed.hostname in (
        "www.youtube.com",
        "youtube.com",
    ):
        if parsed.path == "/watch":
            video_id = parse_qs(
                parsed.query
            ).get("v", [None])[0]

            if video_id:
                return (
                    f"https://www.youtube.com/embed/"
                    f"{video_id}"
                )

        # youtube.com/shorts/VIDEO_ID
        if parsed.path.startswith("/shorts/"):
            video_id = parsed.path.split("/")[2]

            if video_id:
                return (
                    f"https://www.youtube.com/embed/"
                    f"{video_id}"
                )

    # youtu.be/VIDEO_ID
    if parsed.hostname == "youtu.be":
        video_id = parsed.path.strip("/")

        if video_id:
            return (
                f"https://www.youtube.com/embed/"
                f"{video_id}"
            )

    return None



@bp.route("/")
def videos():
    if not current_user.is_authenticated:
        get_or_create_guest_user()

    valid_levels = {"A1", "A2", "B1", "B2", "C1", "C2"}

    selected_level = request.args.get("level", "").strip().upper()

    if selected_level not in valid_levels:
        selected_level = None

    query = db_session.query(Video)

    if selected_level:
        query = query.filter(Video.level == selected_level)

    videos = (
        query
        .order_by(Video.id.desc())
        .all()
    )

    return render_template(
        "videos.html",
        videos=videos,
        selected_level=selected_level,
    )


@bp.route("/<int:video_id>")
def video_details(video_id):
    video = db_session.get(Video, video_id)

    if not video:
        abort(404)

    if not current_user.is_authenticated:
        get_or_create_guest_user()

    embed_url = get_youtube_embed_url(
        video.video_url
    )
    
    # --------------------------------------------------
    # Fetch optional lesson text from GCS
    # --------------------------------------------------
    text_content = None

    if video.text_path:
        try:
            response = requests.get(
                video.text_path,
                timeout=10,
            )
            response.raise_for_status()
            text_content = response.text

        except requests.RequestException:
            current_app.logger.exception(
                "Failed to fetch video text from GCS."
            )

            flash(
                "The lesson text could not be loaded.",
                "danger",
            )

    return render_template(
        "video_details.html",
        video=video,
        embed_url=embed_url,
        text_content=text_content,
    )