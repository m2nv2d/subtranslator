# Core Components Overview

## Purpose

The `core` package provides foundational components that support the entire Subtranslator application. These components handle cross-cutting concerns including configuration management, dependency injection, error handling, and application statistics.

## Internal Structure

```
src/core/
├── __init__.py          # Package initialization
├── config.py            # Pydantic Settings configuration management
├── dependencies.py      # FastAPI dependency providers
├── errors.py            # Error response utilities
├── providers.py         # AI provider abstraction layer
├── rate_limiter.py      # Session-based rate limiting
└── stats.py             # In-memory statistics tracking
```

## Exposed Interface

### Configuration
- `Settings` class: Main application configuration model
- `get_settings()` function: Settings factory function

### Dependencies (FastAPI Dependency Injection)
- `get_application_settings()`: Cached settings provider
- `get_ai_provider()`: AI provider factory and manager
- `get_translation_semaphore()`: Concurrency control provider
- `get_stats_store()`: Statistics store provider
- `get_application_rate_limiter()`: Rate limiter provider
- `check_session_file_limit()`: Session rate limiting dependency

### Error Handling
- `ErrorDetail` model: Standardized error response format
- `create_error_response()`: Error response factory

### Statistics
- `FileStats` model: Individual request statistics
- `TotalStats` model: Aggregated application statistics  
- `AppStatsStore` class: Thread-safe statistics management

### AI Providers
- `AIProvider` interface: Abstract base class for translation providers
- `MockProvider` class: Development and testing provider
- `GeminiProvider` class: Google Gemini integration provider
- `create_provider()` function: Provider factory

### Rate Limiting
- `RateLimiter` class: Session-based file upload limiting
- `get_rate_limiter()` function: Singleton rate limiter provider

## Design Pattern

The core package follows the **Dependency Injection** pattern using FastAPI's built-in DI system. This provides:

- **Centralized Configuration**: All settings managed through a single source of truth
- **Singleton Services**: Shared instances (AI providers, semaphores, stats store, rate limiters) across requests
- **Provider Abstraction**: AI services abstracted behind common interface for flexibility
- **Session Management**: UUID-based session tracking for rate limiting
- **Testability**: Easy mocking of dependencies for unit tests
- **Separation of Concerns**: Clear boundaries between configuration, services, and business logic

## Integration Points

### With FastAPI Application
- Dependencies are injected into route handlers via `Depends()`
- Exception handlers use error utilities for consistent responses
- Middleware components access settings through DI

### With Business Logic
- Translation modules receive configuration through dependency injection
- Statistics are updated throughout the translation pipeline
- Error handling provides domain-specific exception mapping

### With External Services
- AI provider abstraction and management
- Environment variable configuration loading
- Logging configuration based on settings
- Session management and rate limiting

## Best Practices

### Configuration Management
- Always use dependency injection to access settings
- Environment variables should be validated through Pydantic Settings
- Configuration is immutable after initialization (frozen models)

### Error Handling
- Use `create_error_response()` for consistent error formats
- Map domain exceptions to appropriate HTTP status codes
- Avoid exposing internal implementation details in error messages

### Statistics Tracking
- Initialize file entries before processing begins
- Update statistics at each major processing step
- Always complete requests (success or failure) for accurate totals

### Dependency Usage
```python
# Correct way to access configuration and services
@router.post("/translate")
async def translate_srt(
    request: Request,
    settings: Annotated[Settings, Depends(get_application_settings)],
    provider: Annotated[AIProvider, Depends(get_ai_provider)],
    semaphore: Annotated[asyncio.Semaphore, Depends(get_translation_semaphore)],
    stats_store: Annotated[AppStatsStore, Depends(get_stats_store)],
    _: None = Depends(check_session_file_limit),  # Rate limiting
    # ... other parameters
):
    # Use provider abstraction and other services
```

## Performance Considerations

### Caching Strategy
- Settings are cached using `@lru_cache` for performance
- AI providers are initialized once and reused across requests
- Statistics store is a singleton to maintain consistent state
- Rate limiter is a singleton for global session tracking

### Thread Safety
- Statistics store uses async locks for concurrent access
- Semaphore provides global concurrency control
- Settings are immutable after initialization
- Rate limiter uses in-memory dictionary with singleton pattern

### Resource Management
- Dependencies are managed by FastAPI's lifecycle
- Proper cleanup is handled automatically
- Memory usage is optimized through singleton patterns

## Error Scenarios

### Configuration Errors
- Missing required environment variables (AI_API_KEY for google-gemini provider)
- Invalid configuration values (negative numbers, invalid log levels)
- Invalid AI provider selection (must be google-gemini or mock)
- AI provider initialization failures

### Runtime Errors  
- Statistics store corruption (handled gracefully)
- Semaphore exhaustion (controlled by configuration)
- Dependency injection failures (proper error responses)
- Rate limiting errors (HTTP 429 when session limits exceeded)
- Session management failures (missing or invalid session IDs)

## Monitoring and Observability

### Available Metrics
- Total files processed across application lifetime
- Individual file processing statistics
- Error rates and failure patterns
- Processing times and resource utilization
- Session-based rate limiting statistics
- AI provider usage patterns

### Access Patterns
```python
# Get current statistics
stats_store = get_stats_store()
total_stats, file_stats = await stats_store.get_stats()

# Create new request tracking
request_id = await stats_store.create_file_entry(filename, size, mode)

# Update processing progress
await stats_store.update_parsing_stats(request_id, chunks, blocks)
await stats_store.update_translation_stats(request_id, failures, failed_chunks)
await stats_store.complete_request(request_id, status)
```