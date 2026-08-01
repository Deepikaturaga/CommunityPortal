from __future__ import annotations


class AppError(Exception):
    def __init__(self, detail: str, status_code: int = 400) -> None:
        self.detail = detail
        self.status_code = status_code
        super().__init__(detail)


class NotFoundError(AppError):
    def __init__(self, detail: str = "Not found") -> None:
        super().__init__(detail, 404)


class ConflictError(AppError):
    def __init__(self, detail: str = "Conflict") -> None:
        super().__init__(detail, 409)


class ForbiddenError(AppError):
    def __init__(self, detail: str = "Forbidden") -> None:
        super().__init__(detail, 403)


class UnprocessableError(AppError):
    def __init__(self, detail: str = "Unprocessable") -> None:
        super().__init__(detail, 422)
