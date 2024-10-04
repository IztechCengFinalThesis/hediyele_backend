import abc
from typing import Any, Dict, List

from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession


class PsqlRepository(abc.ABC):
    """Base class for PSQL repositories."""

    _session: AsyncSession
    _model: Any

    @abc.abstractmethod
    def __init__(self) -> None:
        """Initialize _session and _model."""
        raise NotImplementedError

    async def get_one(self, **filter_data: Any) -> Any:
        """
        Get one record from database.

        :param filter_data: kwargs params for filter in db
        :return: One record from database
        """
        result = await self._session.execute(
            select(self._model).filter_by(**filter_data),
        )
        return result.scalars().first()

    async def add_one(self, model: Any) -> None:
        """
        Add one record to database.

        :param model: instance model
        """
        self._session.add(model)

    async def add_all(self, list_model: List[Any]) -> None:
        """
        Add all record to database.

        :param list_model: list instance model
        """
        self._session.add_all(list_model)

    async def update(self, update_data: Dict[str, Any], **filter_data: Any) -> None:
        """
        Update record from database.

        :param update_data: Dict with new data
        :param filter_data: kwargs params for filter in db
        """
        await self._session.execute(
            update(self._model)
            .filter_by(
                **filter_data,
            )
            .values(
                **update_data,
            )
            .execution_options(synchronize_session=False),
        )

    async def pagintion(
        self,
        **filter_data: Any,
    ) -> Any:
        """
        Get paginated records from database.

        :param filter_data: kwargs params for filter in db
        :return: paginated records from database
        """
        query = select(self._model).filter_by(**filter_data)
        return await paginate(self._session, query)

    async def delete(self, **filter_data: Any) -> None:
        """
        Delete record from database.

        :param filter_data: kwargs params for filter in db
        """
        await self._session.execute(delete(self._model).filter_by(**filter_data))
