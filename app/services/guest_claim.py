from app.database import db_session
from app.models import (
    Flashcard,
    GuestFlashcard,
    GuestUser,
    GuestChapterProgress,
    UserChapterProgress,
)
from app.utils.time import utcnow


def _latest_datetime(first, second):
    values = [
        value
        for value in (first, second)
        if value is not None
    ]

    return max(values) if values else None


def claim_guest_workspace(user, guest_id):
    """
    Transfer the anonymous guest workspace to a registered user.

    This function does NOT commit. The caller is responsible for
    committing the transaction and clearing the guest session only
    after the commit succeeds.
    """

    if not guest_id:
        return {
            "claimed": False,
            "flashcards_added": 0,
            "flashcards_skipped": 0,
            "progress_merged": 0,
        }

    guest_user = db_session.get(GuestUser, guest_id)

    if not guest_user:
        return {
            "claimed": False,
            "flashcards_added": 0,
            "flashcards_skipped": 0,
            "progress_merged": 0,
        }

    # Never allow an already-claimed workspace to be claimed again.
    if guest_user.is_claimed:
        return {
            "claimed": False,
            "flashcards_added": 0,
            "flashcards_skipped": 0,
            "progress_merged": 0,
        }

    # --------------------------------------------------
    # Level
    # --------------------------------------------------

    if not user.level and guest_user.level:
        user.level = guest_user.level

    # --------------------------------------------------
    # Flashcards
    # --------------------------------------------------

    guest_flashcards = list(guest_user.flashcards)

    existing_questions = {
        question
        for (question,) in (
            db_session.query(Flashcard.question)
            .filter(Flashcard.user_id == user.id)
            .all()
        )
    }

    flashcards_added = 0
    flashcards_skipped = 0

    for guest_card in guest_flashcards:

        if guest_card.question in existing_questions:
            flashcards_skipped += 1
            db_session.delete(guest_card)
            continue

        flashcard = Flashcard(
            user_id=user.id,
            question=guest_card.question,
            answer=guest_card.answer,
            level=guest_card.level,
            ease=guest_card.ease,
            interval=guest_card.interval,
            last_review=guest_card.last_review,
            next_review=guest_card.next_review,
            show_answer=guest_card.show_answer,
            reviewed_by_tc=guest_card.reviewed_by_tc,
            add_by_tc=guest_card.add_by_tc,
            add_by_user=guest_card.add_by_user,
            created_at=guest_card.created_at,
        )

        db_session.add(flashcard)

        existing_questions.add(
            guest_card.question
        )

        flashcards_added += 1

        db_session.delete(guest_card)

    # --------------------------------------------------
    # Chapter progress
    # --------------------------------------------------

    guest_progress_rows = list(
        guest_user.chapter_progress
    )

    progress_merged = 0

    for guest_progress in guest_progress_rows:

        user_progress = (
            db_session.query(UserChapterProgress)
            .filter_by(
                user_id=user.id,
                chapter_id=guest_progress.chapter_id,
            )
            .first()
        )

        if user_progress is None:
            user_progress = UserChapterProgress(
                user_id=user.id,
                chapter_id=guest_progress.chapter_id,
                is_read=guest_progress.is_read,
                completed_at=guest_progress.completed_at,
                updated_at=guest_progress.updated_at,
            )

            db_session.add(user_progress)

        else:
            # A chapter already read by either identity remains read.
            user_progress.is_read = (
                bool(user_progress.is_read)
                or bool(guest_progress.is_read)
            )

            user_progress.completed_at = (
                _latest_datetime(
                    user_progress.completed_at,
                    guest_progress.completed_at,
                )
            )

            user_progress.updated_at = (
                _latest_datetime(
                    user_progress.updated_at,
                    guest_progress.updated_at,
                )
            )

        progress_merged += 1

        db_session.delete(guest_progress)

    # --------------------------------------------------
    # Guest study statistics
    # --------------------------------------------------

    user.points = (
        user.points or 0
    ) + (
        guest_user.points or 0
    )

    user.flashcards_studied = (
        user.flashcards_studied or 0
    ) + (
        guest_user.flashcards_studied or 0
    )

    user.rate_three_count = (
        user.rate_three_count or 0
    ) + (
        guest_user.rate_three_count or 0
    )

    user.max_study_streak = max(
        user.max_study_streak or 0,
        guest_user.max_study_streak or 0,
    )

    # Preserve whichever current streak was updated most recently.
    guest_last = guest_user.streak_last_date
    user_last = user.streak_last_date

    if guest_last and (
        not user_last
        or guest_last > user_last
    ):
        user.study_streak = (
            guest_user.study_streak or 0
        )

        user.streak_last_date = guest_last

    elif (
        guest_last
        and user_last
        and guest_last == user_last
    ):
        user.study_streak = max(
            user.study_streak or 0,
            guest_user.study_streak or 0,
        )

    # Your app defines max_points using points × max streak.
    user.max_points = (
        (user.points or 0)
        * (user.max_study_streak or 0)
    )

    # --------------------------------------------------
    # Mark workspace claimed
    # --------------------------------------------------

    guest_user.claimed_by_user_id = user.id
    guest_user.claimed_at = utcnow()

    return {
        "claimed": True,
        "flashcards_added": flashcards_added,
        "flashcards_skipped": flashcards_skipped,
        "progress_merged": progress_merged,
    }   