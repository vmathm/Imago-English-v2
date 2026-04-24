from datetime import timedelta
from app.utils.time import now_sp



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
    """
    Placeholder for now.
    Later this should check the user's Subscription.current_period_end/status.
    """
    return False


def sync_internal_access(user) -> None:
    """
    For internal users, active is automatic:
    active=True if trial or subscription is valid.
    active=False otherwise.
    """
    if user.billing_mode != "internal":
        return

    user.active = is_trial_active(user) or has_active_subscription(user)