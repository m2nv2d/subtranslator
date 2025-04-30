# Task 4: Implement Structured Logging with `dictConfig`

## Project Context
The application currently uses basic logging configuration via `logging.basicConfig` in `main.py`. It also has `log_config_info.json` and `log_config_debug.json` files, suggesting an intent for more advanced configuration. This task involves switching to `logging.config.dictConfig` using one of these files and enhancing logs with contextual information like request IDs.

## Goal
1.  Configure Python's standard `logging` module using `logging.config.dictConfig` and one of the JSON configuration files (e.g., `log_config_info.json`).
2.  Integrate a request ID (correlation ID) into log messages for better traceability across different parts of a request lifecycle.
3.  Remove the basic `logging.basicConfig` call.

## Prerequisites
- Access to `src/main.py`, `log_config_info.json`, `log_config_debug.json`.
- Understanding of Python's `logging` configuration dictionaries.
- Middleware pattern in FastAPI.

## Subtask 1: Prepare Logging Configuration Dictionary
- **Review JSON Configs:** Examine `log_config_info.json` and `log_config_debug.json`. Ensure they define formatters, handlers (e.g., `console`), and loggers (e.g., root logger, specific loggers for `uvicorn`, `fastapi`, `translator`).
- **Choose Config:** Decide which config file to use by default (e.g., `log_config_info.json`). Consider adding logic (e.g., based on an environment variable `LOG_CONFIG_FILE`) to dynamically choose the file if needed, but start with a single default.
- **Add Request ID to Formatter:** Modify the chosen formatter string(s) in the JSON configuration to include a placeholder for the request ID. A common pattern is `%(request_id)s`.
    *Example Formatter Change:*
    ```json
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - [%(request_id)s] - %(message)s"
        }
    }
    ```

## Subtask 2: Load Configuration and Remove BasicConfig
- In `src/main.py` (or potentially a dedicated `src/core/logging_config.py` module imported early):
    - Remove the `logging.basicConfig(...)` call.
    - Add code to load the chosen JSON configuration file (e.g., `log_config_info.json`).
    - Use `logging.config.dictConfig(config_dict)` to apply the configuration.
    - Handle potential errors during loading (e.g., file not found, invalid JSON).

*Example Implementation (in `main.py` or `logging_config.py`):*
```python
import logging
import logging.config
import json
from pathlib import Path

def setup_logging():
    config_file = Path(__file__).parent.parent / "log_config_info.json" # Adjust path as needed
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        # Ensure request_id has a default value for logs outside requests
        logging.basicConfig() # Run basicConfig first to ensure root handler exists
        root_logger = logging.getLogger()
        for handler in root_logger.handlers:
            handler.addFilter(RequestIdLogFilter(default_request_id="-")) # Add filter later
            
        logging.config.dictConfig(config)
        logging.getLogger(__name__).info(f"Logging configured from {config_file}")
    except Exception as e:
        logging.basicConfig(level=logging.INFO) # Fallback
        logging.getLogger(__name__).error(f"Failed to load logging config from {config_file}: {e}. Falling back to basicConfig.")

# Call this early in application setup
# setup_logging() 
```
**Note:** Needs refinement regarding filter placement and interaction with `dictConfig`.

## Subtask 3: Implement Request ID Middleware
- Create a FastAPI middleware to generate/retrieve a request ID for each incoming request and store it in a context-local variable.
- Use `contextvars` for safely handling context across async tasks.

*Example Middleware (e.g., in `src/core/middleware.py`):*
```python
import logging
import time
import uuid
from contextvars import ContextVar

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

# Define context var
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Try to get X-Request-ID header, or generate a new UUID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Set context var
        token = request_id_var.set(request_id)
        
        start_time = time.time()
        try:
            response = await call_next(request)
            # Add request ID to response headers
            response.headers["X-Request-ID"] = request_id
        except Exception as e:
             logging.getLogger(__name__).exception("Unhandled exception during request")
             raise e
        finally:
            process_time = time.time() - start_time
            logging.getLogger("api.access").info(
                f'{request.client.host} - "{request.method} {request.url.path} HTTP/{request.scope["http_version"]}" {response.status_code} {process_time:.4f}s',
                extra={"request_id": request_id} # Pass explicitly if filter not used
            )
            # Reset context var
            request_id_var.reset(token)
            
        return response
```

## Subtask 4: Implement Logging Filter
- Create a custom `logging.Filter` that reads the request ID from the `contextvar` and adds it to the log record.

*Example Filter (e.g., in `src/core/logging_config.py`):*
```python
import logging
from .middleware import request_id_var # Assuming middleware is in core

class RequestIdLogFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_var.get()
        return True
```

## Subtask 5: Apply Middleware and Filter
- **Apply Middleware:** In `src/main.py`, add the `RequestIdMiddleware` to the FastAPI application instance.
  ```python
  from core.middleware import RequestIdMiddleware
  app.add_middleware(RequestIdMiddleware)
  ```
- **Apply Filter:** Modify the logging configuration (either in the JSON file or programmatically after loading it in `setup_logging`) to add the `RequestIdLogFilter` to the relevant handlers (e.g., the console handler).
  *If modifying JSON:* Add a `"filters": ["requestIdFilter"]` key to the handler config and define the filter in the top-level `"filters"` section.
  *If modifying programmatically:* Get the handler(s) after `dictConfig` and call `handler.addFilter(RequestIdLogFilter())`.

## Testing
- Start the application.
- Check startup logs to ensure the correct logging configuration is loaded and no errors occur.
- Make requests to the API (e.g., `/`, `/translate`).
- Observe the application logs (console output).
    - Verify that log messages include a request ID (e.g., `[<uuid>]`).
    - Verify that all log messages generated during a single request share the same request ID.
    - Verify logs generated outside a request context (e.g., startup logs) have the default request ID (e.g., `[-]`).
- Check response headers for the `X-Request-ID` header.
- Send a request with an `X-Request-ID` header and verify it's used in logs and the response. 