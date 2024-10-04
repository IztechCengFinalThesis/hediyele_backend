from typing import List
from uuid import UUID

from dependencies import UnitOfWorkDep
from db.models.simple import SimpleModel
from exceptions.app import NotFoundExc
from exceptions.simple import SimpleAlreadyExistExc


class SimpleService:
    """Simple service."""

    def __init__(self, uow: UnitOfWorkDep) -> None:
        self._uow = uow

    async def create(self, name: str) -> SimpleModel:
        """
        Create a simple model in db.

        :param name: Name simple.
        :return: Simple model.
        :raises: SimpleAlreadyExistExc,
        """
        async with self._uow:
            simple_obj = await self._uow.simple_table.get_one(name=name)

        if simple_obj is not None:
            raise SimpleAlreadyExistExc()

        simple_obj = SimpleModel(name=name)
        async with self._uow:
            await self._uow.simple_table.add_one(simple_obj)

        return simple_obj

    async def get_one(self, simple_id: UUID) -> SimpleModel:
        """
        Get a simple model.

        :param simple_id: id simple model.
        :return: Simple model.
        :raises: NotFoundExc,
        """
        async with self._uow:
            simple_obj = await self._uow.simple_table.get_one(id=simple_id)

        if simple_obj is None:
            raise NotFoundExc()

        return simple_obj

    async def get_all(self) -> List[SimpleModel]:
        """
        Get all simple model.

        :return: Paginate list of simple model.
        """
        async with self._uow:
            simple_objects = await self._uow.simple_table.pagintion()

        return simple_objects
