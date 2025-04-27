#!/bin/bash
set -e

# Start the FastAPI server in the background
echo "Starting FastAPI server..."
PYTHONPATH=src uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 5000