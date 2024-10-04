FROM python:3.12.4-slim-bullseye

RUN pip3 install --upgrade pip setuptools wheel poetry==1.8.3  \
    && poetry config virtualenvs.create false  \
    && rm -rf /root/.cache/pip

ENV POETRY_CACHE_DIR=/tmp/poetry_cache

WORKDIR /usr/src/app

COPY pyproject.toml poetry.lock /usr/src/app/

RUN --mount=type=cache,target=$POETRY_CACHE_DIR poetry install --no-root

COPY . /usr/src/app/


CMD ["uvicorn", "main:app", "--reload", "--workers", "1", "--host", "0.0.0.0", "--port", "8000"]
