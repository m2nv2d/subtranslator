.PHONY: dev prod test install clean docker-build docker-run docker-dev

# Development server with hot reload
dev:
	@echo "Starting development server..."
	@echo "Environment variables will be loaded from .env file."
	@echo ""
	uv run --env-file=.env uvicorn --app-dir ./src --reload --host 0.0.0.0 --port 5100 main:app

# Production server with gunicorn + uvicorn workers
prod:
	@echo "Starting production server..."
	@echo "Environment variables will be loaded from .env file."
	@echo ""
	uv run --env-file=.env gunicorn -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:5100 --chdir ./src main:app

# Run tests
test:
	@echo "Running tests..."
	uv run pytest tests/automated/

# Install dependencies
install:
	@echo "Installing dependencies..."
	uv sync --frozen --no-dev

# Clean cache and temp files
clean:
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Build Docker image
docker-build:
	@echo "Building Docker image..."
	docker build -t subtranslator .

# Run Docker container
docker-run:
	@echo "Running Docker container..."
	@echo "Environment variables will be loaded from .env file."
	@echo ""
	docker run -d -p 5100:5100 --env-file .env subtranslator

# Development with Docker (instant code reflection)
docker-dev:
	@echo "Starting development environment with Docker..."
	@echo "Code changes will be reflected instantly via volume mounting."
	@echo ""
	docker-compose up --build