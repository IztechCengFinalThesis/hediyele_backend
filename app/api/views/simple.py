from uuid import UUID

from fastapi import APIRouter, status, Depends
from fastapi_pagination import Page

from api.schemas.simple import SimpleSchema, CreateSimpleSchema
from exceptions.app import NotFoundExc
from exceptions.http import HTTPExc
from saq_tasks.main import saq_queue
from services.simple import SimpleService

router_simple = APIRouter(prefix="/simple", tags=["simple"])


@router_simple.post(
    "/",
    status_code=status.HTTP_201_CREATED,
)
async def create_simple(
    request_data: CreateSimpleSchema,
):
    """Create simple using saq background task."""
    await saq_queue.enqueue("create_simple_task", simple_name=request_data.name)


@router_simple.get(
    "/",
    response_model=Page[SimpleSchema],
    status_code=status.HTTP_200_OK,
)
async def get_all_simple(
    task_service: SimpleService = Depends(SimpleService),
):
    """Get all simple."""
    return await task_service.get_all()


@router_simple.get(
    "/{simple_id}/",
    response_model=SimpleSchema,
    status_code=status.HTTP_200_OK,
)
async def get_one_simple(
    simple_id: UUID,
    task_service: SimpleService = Depends(SimpleService),
):
    """Get one simple."""
    try:
        simple_obj = await task_service.get_one(simple_id)
    except NotFoundExc as exc:
        raise HTTPExc(exc)

    return simple_obj
