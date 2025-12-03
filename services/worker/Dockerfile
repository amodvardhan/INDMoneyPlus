FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock* /app/
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev --no-interaction --no-ansi

COPY . /app

# Run both FastAPI and Celery worker
CMD ["sh", "-c", "celery -A app.celery_app worker --loglevel=info & uvicorn app.main:app --host 0.0.0.0 --port 8009"]

