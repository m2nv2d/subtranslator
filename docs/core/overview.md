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
└── stats.py             # In-memory statistics tracking
```

## Exposed Interface

### Configuration
- `Settings` class: Main application configuration model
- `get_settings()` function: Settings factory function

### Dependencies (FastAPI Dependency Injection)
- `get_application_settings()`: Cached settings provider
- `get_genai_client()`: AI client provider
- `get_translation_semaphore()`: Concurrency control provider
- `get_stats_store()`: Statistics store provider

### Error Handling
- `ErrorDetail` model: Standardized error response format
- `create_error_response()`: Error response factory

### Statistics
- `FileStats` model: Individual request statistics
- `TotalStats` model: Aggregated application statistics  
- `AppStatsStore` class: Thread-safe statistics management

## Design Pattern

The core package follows the **Dependency Injection** pattern using FastAPI's built-in DI system. This provides:

- **Centralized Configuration**: All settings managed through a single source of truth
- **Singleton Services**: Shared instances (AI client, semaphore, stats store) across requests
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
- AI client initialization and management
- Environment variable configuration loading
- Logging configuration based on settings

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
# Correct way to access configuration
@router.post("/translate")
async def translate_srt(
    settings: Annotated[Settings, Depends(get_application_settings)],
    client: Annotated[genai.client.Client | None, Depends(get_genai_client)],
    # ... other dependencies
):
    # Use settings and client in route logic
```

## Performance Considerations

### Caching Strategy
- Settings are cached using `@lru_cache` for performance
- AI client is initialized once and reused across requests
- Statistics store is a singleton to maintain consistent state

### Thread Safety
- Statistics store uses async locks for concurrent access
- Semaphore provides global concurrency control
- Settings are immutable after initialization

### Resource Management
- Dependencies are managed by FastAPI's lifecycle
- Proper cleanup is handled automatically
- Memory usage is optimized through singleton patterns

## Error Scenarios

### Configuration Errors
- Missing required environment variables (AI_API_KEY)
- Invalid configuration values (negative numbers, invalid log levels)
- AI client initialization failures

### Runtime Errors  
- Statistics store corruption (handled gracefully)
- Semaphore exhaustion (controlled by configuration)
- Dependency injection failures (proper error responses)

## Monitoring and Observability

### Available Metrics
- Total files processed across application lifetime
- Individual file processing statistics
- Error rates and failure patterns
- Processing times and resource utilization

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