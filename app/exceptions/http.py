from typing import Optional, Dict, Any

from fastapi import HTTPException

from exceptions.app import AppExc


class HTTPExc(HTTPException):
    """Http exception."""

    def __init__(
        self,
        exception: AppExc,
        headers: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Init.

        :param exception: Exception app
        :param headers: http headers
        """
        super().__init__(
            status_code=exception.status_code,
            detail={
                "code": exception.code,
                "message": exception.message,
                "payload": exception.payload,
            },
            headers=headers,
        )
