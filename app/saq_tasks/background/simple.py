from typing import Any

from exceptions.simple import SimpleAlreadyExistExc
from logger import logger_app
from services import get_simple_service


async def create_simple_task(ctx: Any, simple_name: str) -> None:
    """
    Create a simple task background.

    :param ctx: _
    :param simple_name: name
    """
    simple_service = get_simple_service()
    try:
        await simple_service.create(name=simple_name)
        logger_app.info(f"Created success - {simple_name}")
    except SimpleAlreadyExistExc:
        logger_app.error(f"Created fail - {simple_name}")
