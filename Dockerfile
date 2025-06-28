FROM ghcr.io/astral-sh/uv:python3.11-alpine AS base

WORKDIR /app

COPY pyproject.toml uv.lock ./

FROM base AS development
RUN uv sync --locked
COPY src/ ./src/
EXPOSE 5100
CMD ["uv", "run", "uvicorn", "--app-dir", "./src", "--reload", "--host", "0.0.0.0", "--port", "5100", "main:app"]

FROM base AS production
RUN uv sync --locked --no-dev
COPY src/ ./src/
EXPOSE 5100
CMD ["uv", "run", "gunicorn", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:5100", "--chdir", "./src", "main:app"]