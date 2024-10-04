import pytest

from db.uow import UnitOfWork
from exceptions.simple import SimpleAlreadyExistExc
from services import get_simple_service
from tests.factories.simple import SimpleFactory


class TestCreateSimple:
    """Create simple test."""

    async def test_success(self, db_uow: UnitOfWork) -> None:
        """Success create simple test."""
        s_service = get_simple_service(db_uow)
        simple1 = await s_service.create("test")
        async with db_uow:
            simple1_in_db = await db_uow.simple_table.get_one(id=simple1.id)
        assert simple1_in_db.name == simple1.name

        simple2 = await s_service.create("test_2")
        async with db_uow:
            simple2_in_db = await db_uow.simple_table.get_one(id=simple2.id)
        assert simple2_in_db.name == simple2.name

    async def test_failure(self, db_uow: UnitOfWork) -> None:
        """Failure create simple test."""
        s_service = get_simple_service(db_uow)
        simple_obj = await SimpleFactory().create(db_uow)

        with pytest.raises(SimpleAlreadyExistExc):
            await s_service.create(simple_obj.name)
