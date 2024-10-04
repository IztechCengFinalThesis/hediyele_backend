from contextlib import asynccontextmanager
from typing import List, AsyncIterator

import sentry_sdk
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi_pagination import add_pagination
from saq.web.starlette import saq_web

from api import all_routers
from saq_tasks.main import saq_queue
from settings import settings


def create_routers(main_app: FastAPI, routers: List[APIRouter]) -> None:
    """
    Creates all the routers.

    :param main_app: instance FastAPI
    :param routers: list APIRouter
    """
    for router in routers:
        main_app.include_router(router)


def get_list_cors_origins() -> List[str]:
    """
    Gets list of CORS origins.

    :return: list cors
    """
    cors_origins = settings.cors_origins
    if cors_origins is None:
        cors_origins = ["*"]

    return cors_origins


def init_sentry_sdk() -> None:
    """Initializes Sentry SDK."""
    sentry_dsn = settings.sentry_dsn

    if sentry_dsn is not None:
        init_data = {"dsn": sentry_dsn, "traces_sample_rate": 1.0}
        sentry_environment = settings.sentry_environment
        if sentry_environment:
            init_data["environment"] = sentry_environment

        sentry_sdk.init(**init_data)  # type: ignore


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Lifespan."""
    init_sentry_sdk()
    yield


def create_app() -> FastAPI:
    """
    Creates FastAPI application.

    :return: fastapi application
    """
    app_fastapi = FastAPI(lifespan=lifespan)
    create_routers(app_fastapi, all_routers)
    add_pagination(app_fastapi)

    app_fastapi.add_middleware(
        CORSMiddleware,
        allow_origins=get_list_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app_fastapi.mount("/saq_monitor", saq_web("/saq_monitor", queues=[saq_queue]))
    return app_fastapi


app = create_app()
