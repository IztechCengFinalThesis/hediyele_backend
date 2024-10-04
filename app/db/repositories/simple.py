from sqlalchemy.ext.asyncio import AsyncSession

from db.models.simple import SimpleModel
from db.repositories.base import PsqlRepository


class SimpleRepository(PsqlRepository):
    """Simple repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._model = SimpleModel
