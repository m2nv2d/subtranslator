# Task 8: Add Dependency Health Check

## Project Context
The application relies on the external Google Gemini API for its core translation functionality. Currently, there's no explicit health check to verify if the API is reachable and operational *before* accepting translation requests, other than the check during client initialization.

## Goal
Implement a basic health check mechanism, potentially exposed via a `/health` endpoint, that verifies connectivity and basic functionality of the configured Gemini API.

## Prerequisites
- Access to `src/main.py`, `src/core/dependencies.py`, `src/core/config.py`.
- The `google-genai` client instance (`genai_client`).
- FastAPI application structure.

## Subtask 1: Design Health Check Logic
- Determine a simple, low-cost way to check the Gemini API status. Options:
    - **Option A (List Models):** Use `genai_client.models.list()` or `genai_client.aio.models.list()`. This verifies authentication and basic connectivity without consuming significant quota.
    - **Option B (Minimal Generate Call):** Make a very small, non-streaming `generate_content` call with a trivial prompt. This is a more thorough check but uses quota.
- Choose Option A (List Models) as it's generally sufficient for a basic health check and avoids unnecessary API usage.

## Subtask 2: Implement Health Check Function
- Create a new asynchronous function (e.g., `check_gemini_health`) potentially in `src/core/dependencies.py` or a new `src/core/health.py`.
- This function should:
    - Accept the `genai_client` and `settings` as arguments (or retrieve them via dependency injection if creating a dedicated endpoint function).
    - Check if `settings.AI_PROVIDER` is `google-gemini`. If not, the dependency is considered healthy (or N/A).
    - If `genai_client` is `None` (initialization failed), report unhealthy.
    - Call `await genai_client.aio.models.list()`.
    - Handle potential exceptions during the API call (e.g., `google.api_core.exceptions.GoogleAPIError`, network errors via `httpx` if relevant, `google.auth.exceptions.RefreshError`).
    - Return a status (e.g., boolean `True` for healthy, `False` for unhealthy) and optionally a descriptive message.

*Example (`src/core/health.py`):*
```python
import logging
from typing import Tuple, Optional

from google import genai
from google.api_core import exceptions as google_exceptions
from google.auth import exceptions as auth_exceptions

from core.config import Settings

logger = logging.getLogger(__name__)

async def check_gemini_health(
    client: Optional[genai.client.Client],
    settings: Settings
) -> Tuple[bool, str]:
    """Checks the health of the configured Gemini client."""
    if settings.AI_PROVIDER != "google-gemini":
        return True, "Health check N/A: AI provider is not Google Gemini."
        
    if client is None:
        return False, "Gemini client failed to initialize."
        
    try:
        # Simple check: list available models
        await client.aio.models.list()
        logger.debug("Gemini health check successful (list models).")
        return True, "Gemini API connection successful."
    except (google_exceptions.GoogleAPIError, auth_exceptions.RefreshError) as e:
        logger.error(f"Gemini health check failed: {e}", exc_info=True)
        return False, f"Gemini API error: {type(e).__name__}"
    except Exception as e:
        # Catch potential network or other unexpected errors
        logger.error(f"Gemini health check failed with unexpected error: {e}", exc_info=True)
        return False, f"Unexpected error during Gemini health check: {type(e).__name__}"
```

## Subtask 3: Create `/health` Endpoint
- In `src/main.py` or a new router (e.g., `src/routers/health.py`):
    - Create a new FastAPI route `GET /health`.
    - This route should depend on `get_application_settings` and `get_genai_client`.
    - Call the `check_gemini_health` function.
    - Return a JSON response indicating the overall application status and dependency status.
        - If healthy, return HTTP 200 OK.
        - If unhealthy, return HTTP 503 Service Unavailable.

*Example (`src/routers/health.py`):*
```python
from typing import Annotated
from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel

from google import genai

from core.config import Settings
from core.dependencies import get_application_settings, get_genai_client
from core.health import check_gemini_health # Assuming health check is in core.health

router = APIRouter()

class HealthStatus(BaseModel):
    status: str
    dependencies: dict

@router.get("/health", response_model=HealthStatus, tags=["Health"])
async def health_check(
    response: Response,
    settings: Annotated[Settings, Depends(get_application_settings)],
    genai_client: Annotated[genai.client.Client | None, Depends(get_genai_client)],
):
    gemini_healthy, gemini_message = await check_gemini_health(genai_client, settings)
    
    overall_status = "ok" if gemini_healthy else "error"
    dependencies = {
        "gemini_api": {
            "status": "ok" if gemini_healthy else "error",
            "message": gemini_message
        }
    }
    
    if not gemini_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        
    return HealthStatus(status=overall_status, dependencies=dependencies)

# Remember to include this router in main.py
# from routers.health import router as health_router
# app.include_router(health_router)
```

## Testing
- Run the application.
- Access the `/health` endpoint.
    - With valid API key: Verify HTTP 200 and status "ok".
    - With invalid API key (or network blocked): Verify HTTP 503 and status "error" with appropriate message.
    - If `AI_PROVIDER` is not `google-gemini`: Verify HTTP 200 and status "ok" with "N/A" message for Gemini.
- Automated tests can call the `/health` endpoint and assert the status code and response body based on mocked dependency states (healthy/unhealthy Gemini client). 