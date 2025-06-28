.PHONY: dev prod test install clean docker-build docker-run

# Development server with hot reload
dev:
	uv run uvicorn --app-dir ./src --reload --host 0.0.0.0 --port 5100 main:app

# Production server with gunicorn + uvicorn workers
prod:
	uv run gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5100 --chdir ./src main:app

# Run tests
test:
	uv run pytest tests/automated/

# Install dependencies
install:
	uv sync

# Clean cache and temp files
clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Build Docker image
docker-build:
	docker build -t subtranslator .

# Run Docker container
docker-run:
	docker run -d -p 5100:5100 --env-file .env subtranslator