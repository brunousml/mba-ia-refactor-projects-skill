from datetime import datetime, timezone


def utc_now():
    """UTC sem fuso: o SQLite guarda datetime naive, então a comparação continua naive."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
