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
uv run uvicorn --app-dir ./src --reload --host 0.0.0.0 --port 5100 main:app
```

## Production Server

For production deployment:
```bash
uv run gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5100 --chdir ./src main:app
```
