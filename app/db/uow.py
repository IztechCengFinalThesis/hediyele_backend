from types import TracebackType
from typing import Optional, Type

from db.engine import async_session_maker
from db.repositories.simple import SimpleRepository


class UnitOfWork:
    """Context manager for working with databases."""

    def __init__(self) -> None:
        self.session_factory = async_session_maker

    async def __aenter__(self) -> None:
        """Initializing repositories. Create session."""
        self._session = self.session_factory()
        self.simple_table = SimpleRepository(self._session)

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exn_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Ending a session."""
        if exc_type:
            await self._session.rollback()
        else:
            await self._session.commit()

        await self._session.close()

    async def commit(self) -> None:
        """Commit."""
        await self._session.commit()

    async def rollback(self) -> None:
        """Rollback."""
        await self._session.rollback()


def get_uow() -> UnitOfWork:
    """
    Get uow.

    :return: UnitOfWork
    """
    return UnitOfWork()
