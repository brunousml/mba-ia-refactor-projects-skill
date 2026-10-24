import os

from config import settings
from models import sistema_model


def status_banco():
    contagens = sistema_model.contagens()
    return {
        "status": "ok",
        "database": "connected",
        "counts": contagens,
        "versao": "1.0.0",
        "ambiente": "producao",
        "db_path": os.path.basename(settings.DB_PATH),
        "debug": settings.DEBUG,
    }
