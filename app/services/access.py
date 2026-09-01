from datetime import timedelta

from app.database import db_session
from app.models import Subscription
from app.utils.time import SP_TZ, now_sp, utcnow


TRIAL_DAYS = 7


def is_trial_active(user) -> bool:
    if user.billing_mode != "internal":
        return False

    if not user.join_date:
        return False

    today = now_sp().date()
    trial_end_date = (
        user.join_date
        + timedelta(days=TRIAL_DAYS)
    )

    return today < trial_end_date


def get_active_subscription(user):
    """
    Return a currently active and unexpired subscription
    for this user.

    Access must depend on the subscription's actual state,
    not on whichever subscription was created most recently.
    """
    return (
        db_session.query(Subscription)
        .filter(
            Subscription.user_id == user.id,
            Subscription.status == "active",
            Subscription.current_period_end.isnot(None),
            Subscription.current_period_end > utcnow(),
        )
        .order_by(
            Subscription.current_period_end.desc()
        )
        .first()
    )


def has_active_subscription(user) -> bool:
    return get_active_subscription(user) is not None


def sync_internal_access(user) -> None:
    """
    For internal users, paid-content access depends
    only on having an active subscription.
    """
    if user.billing_mode != "internal":
        return

    user.active = has_active_subscription(user)


def trial_days_left(user):
    if user.billing_mode != "internal":
        return None

    if not user.join_date:
        return None

    today = now_sp().date()
    trial_end_date = (
        user.join_date
        + timedelta(days=TRIAL_DAYS)
    )

    days_left = (
        trial_end_date - today
    ).days

    return max(days_left, 0)


def subscription_days_left(user):
    subscription = get_active_subscription(user)

    if not subscription:
        return None

    # Convert UTC → São Paulo date for user-facing logic
    today = now_sp().date()

    end_date = (
        subscription.current_period_end
        .astimezone(SP_TZ)
        .date()
    )

    days_left = (
        end_date - today
    ).days

    return max(days_left, 0)