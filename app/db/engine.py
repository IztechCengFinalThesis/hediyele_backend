from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from settings import settings

engine = create_async_engine(
    url=str(settings.db_url),
    echo=settings.postgres_echo,
    future=True,
    max_overflow=settings.postgres_max_overflow,
    pool_size=settings.postgres_pool_size,
)

async_session_maker = async_sessionmaker(bind=engine, expire_on_commit=False)
