from faker import Faker
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from yarl import URL

from db.models.base import BaseModel


def get_faker() -> Faker:
    """Get faker."""
    return Faker()


def get_test_name_db() -> str:
    """
    Get test name db.

    :return: name db
    """
    return get_faker().pystr(min_chars=4, max_chars=8, prefix="test_").lower()


def get_test_db_url(
    host: str, port: int, user: str, password: str, db_name: str
) -> str:
    """
    Get test db url.

    :param host: host
    :param port: port
    :param user: user
    :param password: password
    :param db_name: db_name
    :return: test db url
    """
    db_url = URL.build(
        scheme="postgresql+asyncpg",
        host=host,
        port=port,
        user=user,
        password=password,
        path=f"/{db_name}",
    )
    return str(db_url)


def get_test_engine(test_db_url: str) -> AsyncEngine:
    """
    Get test engine.

    :param test_db_url: db url
    :return: Async Engine
    """
    return create_async_engine(
        url=test_db_url,
        echo=False,
        future=True,
        max_overflow=20,
        pool_size=10,
    )


async def create_test_database(engine_obj: AsyncEngine, db_name: str) -> None:
    """
    Create current database.

    :param engine_obj: engine
    :param db_name: db name
    """
    async with engine_obj.connect() as conn:
        database_existance = await conn.execute(
            text(
                f"SELECT 1 FROM pg_database WHERE datname='{db_name}'",  # noqa: E501, S608
            ),
        )
        database_exists = database_existance.scalar() == 1

    if database_exists:
        await drop_test_database(engine_obj, db_name)

    async with engine_obj.connect() as conn:
        await conn.execute(
            text(
                f'CREATE DATABASE "{db_name}" ENCODING "utf8" TEMPLATE template1',  # noqa: E501
            ),
        )


async def drop_test_database(
    engine_obj: AsyncEngine, db_name: str
) -> None:  # noqa: S608
    """
    Drop current database.

    :param engine_obj: engine
    :param db_name: db name
    """
    async with engine_obj.connect() as conn:
        disc_users = (
            "SELECT pg_terminate_backend(pg_stat_activity.pid) "  # noqa: S608
            "FROM pg_stat_activity "
            f"WHERE pg_stat_activity.datname = '{db_name}' "
            "AND pid <> pg_backend_pid();"
        )
        await conn.execute(text(disc_users))
        await conn.execute(text(f'DROP DATABASE "{db_name}"'))


async def create_test_tables(test_engine: AsyncEngine) -> None:
    """
    Create test tables.

    :param test_engine: engine
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)


async def drop_test_tables(test_engine: AsyncEngine) -> None:
    """
    Drop test tables.

    :param test_engine: engine
    """
    async with test_engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.drop_all)
