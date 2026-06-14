FROM python:3.12-slim

# System deps kept minimal (smaller attack surface).
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Copy project (source is also bind-mounted in compose; PYTHONPATH makes the live
# mount win at runtime). Needed here so setuptools can build the package.
COPY pyproject.toml alembic.ini ./
COPY src ./src
COPY db ./db
RUN pip install --upgrade pip && pip install ".[dev]"

# Run as a non-root user (least privilege).
RUN useradd --create-home --uid 10001 aegis && chown -R aegis:aegis /app
USER aegis

ENV PYTHONPATH=/app/src
