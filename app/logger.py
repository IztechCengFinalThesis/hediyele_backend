import logging

logger_app = logging.getLogger()
logger_app.handlers.clear()
logger_app.setLevel(logging.INFO)
stream_handler = logging.StreamHandler()
formatter = logging.Formatter(
    "%(levelname)s: %(asctime)s %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M"
)
stream_handler.setFormatter(formatter)
logger_app.addHandler(stream_handler)
