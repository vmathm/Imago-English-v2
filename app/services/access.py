from datetime import timedelta
from app.utils.time import now_sp, utcnow
from app.database import db_session
from app.models import Subscription


TRIAL_DAYS = 7


def is_trial_active(user) -> bool:
    if user.billing_mode != "internal":
        return False

    if not user.join_date:
        return False

    today = now_sp().date()
    trial_end_date = user.join_date + timedelta(days=TRIAL_DAYS)

    return today < trial_end_date


def has_active_subscription(user) -> bool:
    subscription = (
        db_session.query(Subscription)
        .filter_by(user_id=user.id)
        .order_by(Subscription.created_at.desc())
        .first()
    )

    if not subscription:
        return False

    if subscription.status != "active":
        return False

    if not subscription.current_period_end:
        return False

    return subscription.current_period_end > utcnow()


def sync_internal_access(user) -> None:
    """
    For internal users, active is automatic:
    active=True if trial or subscription is valid.
    active=False otherwise.
    """
    if user.billing_mode != "internal":
        return

    user.active = is_trial_active(user) or has_active_subscription(user)



def trial_days_left(user):
    if user.billing_mode != "internal":
        return None

    if not user.join_date:
        return None

    today = now_sp().date()
    trial_end_date = user.join_date + timedelta(days=TRIAL_DAYS)

    days_left = (trial_end_date - today).days

    return max(days_left, 0)


from app.utils.time import now_sp


def subscription_days_left(user):
    subscription = (
        db_session.query(Subscription)
        .filter_by(user_id=user.id)
        .order_by(Subscription.created_at.desc())
        .first()
    )

    if not subscription:
        return None

    if subscription.status != "active":
        return None

    if not subscription.current_period_end:
        return None

    # Convert UTC → São Paulo date for user-facing logic
    today = now_sp().date()
    end_date = subscription.current_period_end.astimezone(SP_TZ).date()

    days_left = (end_date - today).days

    return max(days_left, 0)