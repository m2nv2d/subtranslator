# Rate Limiter Test Documentation

## Purpose

This test file validates the session-based rate limiting functionality introduced to prevent file upload abuse. It covers the `RateLimiter` class, dependency injection functions, and FastAPI integration for session-based upload restrictions.

## Scope

**Test Type**: Unit tests for rate limiting components  
**Test Framework**: pytest with unittest.mock for dependency mocking  
**Coverage Focus**: Core rate limiting logic, session management, and error conditions

## File Location

`tests/manual/test_rate_limiter.py`

## Test Structure

### TestRateLimiter Class

Tests for the core `RateLimiter` class functionality.

#### `test_rate_limiter_initialization`

**Scenario**: Verify RateLimiter correctly initializes with configuration settings.

**Inputs**: 
- Mock Settings object with `SESSION_FILE_LIMIT = 25`

**Expected Pass**: 
- RateLimiter instance created successfully
- `file_limit` property set to configured value (25)
- `session_counts` dictionary initialized as empty

**Expected Fail**: 
- Invalid settings object
- Missing SESSION_FILE_LIMIT configuration

#### `test_check_limit_new_session`

**Scenario**: Test rate limiting behavior for sessions not yet tracked.

**Inputs**: 
- RateLimiter with limit of 50
- New session ID not in tracking dictionary

**Expected Pass**: 
- `check_limit()` completes without raising exceptions
- Session count initialized to 1 after first call
- Session tracking entry created in dictionary

**Expected Fail**: 
- Session ID format validation issues

#### `test_check_limit_under_limit`

**Scenario**: Verify rate limiting allows uploads when under configured limit.

**Inputs**: 
- RateLimiter with limit of 50
- Existing session with 25 uploads

**Expected Pass**: 
- `check_limit()` completes without exceptions
- Session count incremented to 26
- No HTTPException raised

**Expected Fail**: 
- Unexpected session count modifications

#### `test_check_limit_at_limit`

**Scenario**: Test rate limiting enforcement when session reaches configured limit.

**Inputs**: 
- RateLimiter with limit of 50
- Session already at 50 uploads

**Expected Pass**: 
- `check_limit()` raises HTTPException with status 429
- Error message indicates "Session file upload limit exceeded"
- Session count remains at 50 (not incremented)

**Expected Fail**: 
- Exception not raised when at limit
- Wrong HTTP status code
- Session count incorrectly modified

#### `test_check_limit_over_limit`

**Scenario**: Verify behavior when session count exceeds limit (edge case).

**Inputs**: 
- RateLimiter with limit of 50
- Session artificially set to 55 uploads

**Expected Pass**: 
- `check_limit()` raises HTTPException with status 429
- Appropriate error message displayed
- Session count unchanged (remains 55)

**Expected Fail**: 
- Limit enforcement bypassed for over-limit sessions

#### `test_get_session_count_existing`

**Scenario**: Test retrieval of upload count for tracked sessions.

**Inputs**: 
- RateLimiter instance
- Session with established count of 25

**Expected Pass**: 
- `get_session_count()` returns 25
- No side effects on session state

**Expected Fail**: 
- Incorrect count returned
- Session state modified during retrieval

#### `test_get_session_count_new`

**Scenario**: Test count retrieval for untracked sessions.

**Inputs**: 
- RateLimiter instance
- Session ID not in tracking dictionary

**Expected Pass**: 
- `get_session_count()` returns 0
- No new session entry created

**Expected Fail**: 
- Non-zero count returned for new session
- Unintended session initialization

#### `test_reset_session`

**Scenario**: Verify session reset functionality for count clearing.

**Inputs**: 
- RateLimiter instance
- Session with count of 25

**Expected Pass**: 
- `reset_session()` sets count to 0
- Session remains in tracking dictionary
- Reset operation logged appropriately

**Expected Fail**: 
- Session count not properly reset
- Session removed from tracking

### TestCheckSessionFileLimit Class

Tests for FastAPI dependency integration and request processing.

#### `test_check_session_file_limit_no_session`

**Scenario**: Test behavior when request lacks session data.

**Inputs**: 
- Mock Request object with empty session dictionary
- Mock RateLimiter instance

**Expected Pass**: 
- `check_session_file_limit()` raises HTTPException with status 400
- Error message indicates "Session not found"
- No rate limiter methods called

**Expected Fail**: 
- Function completes without error for missing session
- Wrong HTTP status code

#### `test_check_session_file_limit_with_session`

**Scenario**: Verify successful rate limiting check with valid session.

**Inputs**: 
- Mock Request with session containing valid session_id
- Mock RateLimiter instance

**Expected Pass**: 
- `check_session_file_limit()` calls `rate_limiter.check_limit()` with session ID
- Function completes without exceptions
- Correct session ID passed to rate limiter

**Expected Fail**: 
- Rate limiter not called appropriately
- Wrong session ID passed

#### `test_check_session_file_limit_rate_limit_exceeded`

**Scenario**: Test error propagation when rate limit is exceeded.

**Inputs**: 
- Mock Request with valid session
- Mock RateLimiter configured to raise HTTPException(429)

**Expected Pass**: 
- HTTPException(429) propagated from rate limiter
- Original error message preserved
- Rate limiting logic executed

**Expected Fail**: 
- Exception not properly propagated
- Error message modified during propagation

### TestGetRateLimiter Class

Tests for singleton rate limiter management.

#### `test_get_rate_limiter_initialization`

**Scenario**: Verify rate limiter factory creates instances correctly.

**Inputs**: 
- Mock Settings with SESSION_FILE_LIMIT = 25

**Expected Pass**: 
- `get_rate_limiter()` returns RateLimiter instance
- Instance configured with correct file limit
- Type validation passes

**Expected Fail**: 
- Wrong instance type returned
- Configuration not applied correctly

#### `test_get_rate_limiter_singleton`

**Scenario**: Test singleton behavior across multiple factory calls.

**Inputs**: 
- Two different Settings objects with different limits

**Expected Pass**: 
- First call creates new instance
- Second call returns same instance (singleton behavior)
- Settings from first call remain effective

**Expected Fail**: 
- New instance created on second call
- Settings incorrectly updated from second call

## Test Coverage Analysis

### Core Functionality Coverage
- ✅ Rate limiter initialization and configuration
- ✅ Session tracking and count management
- ✅ Limit enforcement and exception handling
- ✅ Session reset and state management

### Error Condition Coverage
- ✅ Missing session scenarios
- ✅ Limit exceeded scenarios  
- ✅ Edge cases (over-limit sessions)
- ✅ Configuration validation

### Integration Coverage
- ✅ FastAPI dependency integration
- ✅ Request processing integration
- ✅ Exception propagation
- ✅ Singleton pattern behavior

### Areas for Enhancement
- 🔄 Concurrent access testing (multiple sessions simultaneously)
- 🔄 Session ID validation testing
- 🔄 Memory usage testing for large session counts
- 🔄 Performance testing under load

## Mock Usage Patterns

The tests extensively use `unittest.mock` for isolating components:

```python
# Settings mocking for configuration testing
settings = Mock()
settings.SESSION_FILE_LIMIT = 50

# Request mocking for FastAPI integration
request = Mock()
request.session = {"session_id": "test_session_123"}

# RateLimiter mocking for dependency testing
rate_limiter = Mock()
rate_limiter.check_limit.side_effect = HTTPException(429, "Limit exceeded")
```

## Expected Behavior Verification

### Rate Limiting Logic
- Session counts accurately track file uploads
- Limits are enforced consistently across requests
- Error responses provide appropriate user feedback

### Session Management
- Sessions are properly initialized and tracked
- Session state persists across requests within application lifecycle
- Session reset functionality works correctly

### FastAPI Integration
- Dependencies inject correctly into route handlers
- HTTP exceptions propagate with correct status codes
- Request session data is properly accessed and validated

### Singleton Behavior
- Rate limiter instances are reused across dependency injections
- Configuration remains consistent throughout application lifecycle
- Memory usage is optimized through instance reuse

## Test Execution Notes

- Tests use manual execution pattern rather than automated test runner
- Mocking enables isolated testing without external dependencies
- Error conditions are explicitly tested for robustness validation
- Both positive and negative test cases are covered comprehensively

This test suite ensures the rate limiting feature works correctly across all expected usage patterns and error conditions, providing confidence in the session-based upload restriction functionality.