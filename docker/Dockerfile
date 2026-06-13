FROM python:3.12-slim

# System deps kept minimal (smaller attack surface).
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install dependencies first for layer caching.
COPY pyproject.toml ./
RUN pip install --upgrade pip && pip install ".[dev]"

# Source is bind-mounted in compose for dev; copy for standalone builds too.
COPY src ./src
COPY db ./db
COPY alembic.ini ./alembic.ini

# Run as a non-root user (least privilege).
RUN useradd --create-home --uid 10001 aegis && chown -R aegis:aegis /app
USER aegis

ENV PYTHONPATH=/app/src
