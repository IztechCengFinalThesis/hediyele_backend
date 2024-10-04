from services.simple import SimpleService
from db.uow import get_uow, UnitOfWork


def get_simple_service(uow: UnitOfWork = get_uow()) -> SimpleService:
    """
    Get a simple service.

    :param uow: UnitOfWork
    :return: SimpleService
    """
    return SimpleService(uow)
