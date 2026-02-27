# Staging Dockerfile — uses uv for fast installs, includes all dependencies
FROM python:3.12-slim

WORKDIR /app

# Install uv via official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Install dependencies first
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy source
COPY . .

ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "python", "main.py", "--schedule"]
