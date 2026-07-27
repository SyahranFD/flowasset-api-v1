from datetime import datetime, timedelta


def wib_now() -> datetime:
    """Return current time in WIB (UTC+7), naive datetime."""
    return datetime.utcnow() + timedelta(hours=7)
