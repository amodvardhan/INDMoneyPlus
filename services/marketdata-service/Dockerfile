# Multi-stage Dockerfile for marketdata-service

FROM python:3.11-slim as base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry && \
    poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock* /app/

FROM base as dev

RUN poetry install --no-interaction --no-ansi --no-root
RUN pip install debugpy

COPY . /app

EXPOSE 8081 5678

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081", "--reload"]

FROM base as prod

RUN poetry install --no-dev --no-interaction --no-ansi

COPY . /app

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8081

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8081", "--workers", "4"]
