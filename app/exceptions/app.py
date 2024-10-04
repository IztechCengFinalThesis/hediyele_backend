from typing import Any


class AppExc(Exception):
    """Base exceptions app."""

    status_code: int
    message = ""
    code = None
    payload: Any = None

    def __init__(self) -> None:
        self.code = self.__class__.__name__


class ConflictExc(AppExc):
    """Conflict exceptions app."""

    status_code = 409


class NotFoundExc(AppExc):
    """Not Found exceptions app."""

    status_code = 404


class BadGatewayExc(AppExc):
    """Bad Gateway exceptions app."""

    status_code = 502


class ForbiddenExc(AppExc):
    """Forbidden exceptions app."""

    status_code = 403
