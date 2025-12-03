# Multi-stage Dockerfile for auth-service
# Supports both dev (hot-reload) and production builds

FROM python:3.11-slim as base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install poetry && \
    poetry config virtualenvs.create false

# Copy dependency files
COPY pyproject.toml poetry.lock* /app/

# Development stage
FROM base as dev

# Update lock file if needed and install all dependencies (including dev)
RUN poetry lock || poetry install --no-interaction --no-ansi --no-root || \
    (poetry lock && poetry install --no-interaction --no-ansi --no-root)

# Install debugpy for VS Code debugging
RUN pip install debugpy

# Copy application code
COPY . /app

# Expose debug port
EXPOSE 8080 5678

# Default command (can be overridden in docker-compose)
CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]

# Production stage
FROM base as prod

# Install only production dependencies
RUN poetry install --no-dev --no-interaction --no-ansi

# Copy application code
COPY . /app

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "4"]
