FROM python:3.11-slim as base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip install poetry==1.7.1 && \
    poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock* ./

FROM base as dev

RUN poetry install --no-interaction --no-ansi --no-root
RUN pip install debugpy

COPY . .

EXPOSE 8086 5678

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8086", "--reload"]

FROM base as prod

RUN poetry install --no-dev --no-interaction --no-ansi --no-root

COPY . .

RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8086

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8086/health || exit 1

CMD ["sh", "-c", "poetry run alembic upgrade head && poetry run uvicorn app.main:app --host 0.0.0.0 --port 8086 --workers 4"]
