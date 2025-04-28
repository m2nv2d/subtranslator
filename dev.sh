#!/bin/bash
set -e

# Parse command line arguments
PORT=5100
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --log-level) log_level="$2"; shift ;;
        --port) PORT="$2"; shift ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

# Set log config based on log level
case $log_level in
    "debug") LOG_CONFIG="log_config_debug.json" ;;
    "info") LOG_CONFIG="log_config_info.json" ;;
    *) echo "Invalid log level. Using default (info)"; 
esac

# Check if the port is already in use
if lsof -i:$PORT; then
  echo "Port $PORT is already in use. Please free it up before running the script."
  exit 1
fi

# Start the FastAPI server in the background
echo "Starting FastAPI server..."
if [ -n "$LOG_CONFIG" ]; then
    uv run uvicorn --app-dir ./src --reload --reload-dir ./src --host 0.0.0.0 --port $PORT --log-config $LOG_CONFIG main:app
else
    uv run uvicorn --app-dir ./src  --reload --reload-dir ./src --host 0.0.0.0 --port $PORT main:app
fi