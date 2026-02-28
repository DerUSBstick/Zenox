# Staging Dockerfile — uses uv for fast installs, includes all dependencies
FROM python:3.12-slim

WORKDIR /app

# Install uv via official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends git netcat-openbsd && rm -rf /var/lib/apt/lists/*

# Install dependencies first
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy source
COPY . .

ENV PYTHONUNBUFFERED=1

CMD until nc -z zenox-mongo-staging 27017; do echo 'waiting for mongodb...'; sleep 2; done && uv run python main.py --schedule
