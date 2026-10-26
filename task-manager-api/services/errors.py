class DomainError(Exception):
    """Erro de regra de negócio com o status HTTP sugerido."""

    def __init__(self, message, status=400):
        super().__init__(message)
        self.status = status


class NotFoundError(DomainError):
    def __init__(self, message):
        super().__init__(message, 404)


class ConflictError(DomainError):
    def __init__(self, message):
        super().__init__(message, 409)
