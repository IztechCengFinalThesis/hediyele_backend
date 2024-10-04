from typing import Any
from uuid import UUID

from services import get_simple_service
from logger import logger_app
from exceptions.app import NotFoundExc


async def get_one_simple_task(ctx: Any) -> None:
    """Get one simple task."""
    simple_service = get_simple_service()
    simple_id = UUID("1f3a64c1-08af-4c78-b304-b861fd8ceb25")
    try:
        simple_obj = await simple_service.get_one(simple_id)
        logger_app.info(f"Simple task found {simple_obj.name}")
    except NotFoundExc:
        logger_app.info(f"Simple task not found! id - {simple_id}")
