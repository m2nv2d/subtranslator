# Rate Limiter Module

## Overview

The rate limiter module provides session-based file upload limiting to prevent abuse and ensure fair resource usage across user sessions. It implements a singleton pattern for global rate limiting with per-session tracking.

## Key Components

### RateLimiter Class

A session-based rate limiter that tracks file upload counts per session and enforces configurable limits.

**Key Features:**
- Session-based tracking using session IDs
- Configurable file upload limits via `SESSION_FILE_LIMIT` setting
- Thread-safe singleton pattern
- Automatic session count management

**Methods:**
- `check_limit(session_id: str)` - Validates and increments session file count
- `get_session_count(session_id: str)` - Returns current file count for session
- `reset_session(session_id: str)` - Resets file count for a session

### FastAPI Dependencies

- `check_session_file_limit()` - FastAPI dependency that validates session and enforces limits
- `get_application_rate_limiter()` - Provider for the global rate limiter instance

## Configuration

Rate limiting behavior is controlled through application settings:

```python
SESSION_FILE_LIMIT: int = 50  # Maximum files per session
SESSION_SECRET_KEY: str = "your-secret-key-change-in-production"  # Session middleware key
```

## Usage

### Basic Integration

The rate limiter is automatically applied to file upload endpoints through dependency injection:

```python
@router.post("/translate")
async def translate_srt(
    request: Request,
    _: None = Depends(check_session_file_limit),  # Rate limiting dependency
    file: UploadFile = File(...),
    # ... other parameters
):
    # Translation logic here
```

### Session Management

Sessions are automatically managed through middleware that assigns unique session IDs:

```python
@app.middleware("http")
async def ensure_session_id(request: Request, call_next):
    if "session_id" not in request.session:
        request.session["session_id"] = str(uuid.uuid4())
    
    response = await call_next(request)
    return response
```

## Error Handling

When file limits are exceeded, the rate limiter raises an HTTP 429 (Too Many Requests) exception:

```json
{
  "status_code": 429,
  "detail": "Session file upload limit exceeded. Maximum 50 files per session."
}
```

Missing or invalid sessions result in HTTP 400 (Bad Request):

```json
{
  "status_code": 400,
  "detail": "Session not found. Please refresh the page and try again."
}
```

## Implementation Details

### Session Storage

The rate limiter uses in-memory session tracking with a simple dictionary structure:

```python
session_counts: Dict[str, int] = {}
```

### Singleton Pattern

The global rate limiter instance is managed through a module-level variable and factory function:

```python
_rate_limiter = None

def get_rate_limiter(settings: Settings) -> RateLimiter:
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(settings)
    return _rate_limiter
```

## Testing

The module includes comprehensive unit tests covering:

- Rate limiter initialization and configuration
- Limit checking for new and existing sessions
- Error conditions (limit exceeded, missing sessions)
- Session count management and reset functionality
- FastAPI dependency integration

Test file: `tests/manual/test_rate_limiter.py`

## Security Considerations

- Session IDs are generated using UUID4 for uniqueness and unpredictability
- Session secret key should be changed in production environments
- In-memory storage means session counts are reset on application restart
- Consider implementing persistent storage for production deployments with multiple instances

## Related Components

- **Session Middleware**: Manages session creation and persistence
- **Config Module**: Provides rate limiting configuration settings
- **Dependencies Module**: Integrates rate limiter with FastAPI dependency injection
- **Translation Router**: Primary consumer of rate limiting functionality