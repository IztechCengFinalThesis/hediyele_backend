from typing import Any

from saq import Queue, CronJob

from logger import logger_app
from saq_tasks.background.simple import create_simple_task
from saq_tasks.periodic.simple import get_one_simple_task
from settings import settings


async def startup(ctx: Any) -> None:
    """
    Start up saq app.

    :param ctx: _
    """
    logger_app.info("Starting up SAQ service")


async def shutdown(ctx: Any) -> None:
    """
    Shut down saq app.

    :param ctx: _
    """
    logger_app.info("Shutdown up SAQ service")


saq_queue = Queue.from_url(settings.redis_dsn)


settings = {  # type: ignore
    "queue": saq_queue,
    "functions": [create_simple_task],
    "concurrency": 10,
    "cron_jobs": [CronJob(get_one_simple_task, cron="* * * * * */5")],
    "startup": startup,
    "shutdown": shutdown,
}
