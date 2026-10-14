import logging

from sqlalchemy.exc import SQLAlchemyError

import database
from services.errors import AppError

logger = logging.getLogger(__name__)


def save(error_message):
    """Grava a transação; em falha do banco desfaz e lança erro de domínio 500."""
    try:
        database.commit()
    except SQLAlchemyError as exc:
        database.rollback()
        logger.exception(error_message)
        raise AppError(error_message, 500) from exc
