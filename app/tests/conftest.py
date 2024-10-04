from typing import AsyncGenerator

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker

from db.engine import engine as app_engine
from db.uow import UnitOfWork
from settings import settings
from tests.utils import (
    get_test_name_db,
    get_test_db_url,
    get_test_engine,
    create_test_database,
    drop_test_database,
    create_test_tables,
    drop_test_tables,
)


@pytest_asyncio.fixture(name="db_uow")
async def db_uow() -> AsyncGenerator[UnitOfWork, None]:
    """Fixture UnitOfWork."""
    test_db_name = get_test_name_db()
    test_db_url = get_test_db_url(
        host=settings.postgres_host,
        port=settings.postgres_port,
        user=settings.postgres_user,
        password=settings.postgres_password,
        db_name=test_db_name,
    )
    test_engine = get_test_engine(test_db_url)

    app_engine_autocommit = app_engine.execution_options(isolation_level="AUTOCOMMIT")

    await create_test_database(app_engine_autocommit, test_db_name)

    await create_test_tables(test_engine)

    uow = UnitOfWork()

    uow.session_factory = async_sessionmaker(bind=test_engine, expire_on_commit=False)

    yield uow

    await drop_test_tables(test_engine)
    await drop_test_database(app_engine_autocommit, test_db_name)

    await test_engine.dispose()
    await app_engine_autocommit.dispose()
