from datetime import datetime, timezone


def utcnow():
    # Substitui datetime.utcnow (obsoleto); sem fuso, como o SQLite já guarda as datas
    return datetime.now(timezone.utc).replace(tzinfo=None)
