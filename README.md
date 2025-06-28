# Subtranslator

Subtranslator is a FastAPI app built to translate subtitle files using LLMs. It provides a web interface for uploading subtitle files and translating them to different languages using various AI models.


## Installation

1. Install dependencies with uv:
   ```bash
   uv sync
   ```

2. Create environment file from example:
   ```bash
   cp .env.example .env
   ```

## Development Server

Run the FastAPI development server:
```bash
# Using Makefile
make dev

# Or directly
uv run --env-file=.env uvicorn --app-dir ./src --reload --host 0.0.0.0 --port 5100 main:app
```

Or use docker-compose:
```bash
# Using Makefile
make docker-dev

# Or directly
docker-compose up --build
```

## Production Server

For production deployment:
```bash
# Using Makefile
make prod

# Or directly
uv run --env-file=.env gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5100 --chdir ./src main:app
```

## Docker

Build and run with Docker:

```bash
# Using Makefile
make docker-build
make docker-run

# Or directly
docker build -t subtranslator .
docker run -d -p 5100:5100 --env-file .env subtranslator
```

Or use docker-compose:

```yaml
version: '3.8'
services:
  subtranslator:
    build: .
    ports:
      - "5100:5100"
    env_file:
      - .env
```
