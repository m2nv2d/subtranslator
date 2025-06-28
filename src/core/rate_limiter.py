import logging
from typing import Dict
from fastapi import HTTPException, Request, Depends
from .config import Settings, get_settings as get_application_settings

logger = logging.getLogger(__name__)

# Global rate limiter instance
_rate_limiter = None

# Global request counter
_global_request_count = 0


class RateLimiter:
    """Session-based rate limiter for file uploads."""
    
    def __init__(self, settings: Settings):
        self.file_limit = settings.SESSION_FILE_LIMIT
        self.session_counts: Dict[str, int] = {}
        logger.info(f"Rate limiter initialized with file limit: {self.file_limit}")
    
    def check_limit(self, session_id: str) -> None:
        """
        Check if session has exceeded file upload limit.
        
        Args:
            session_id: The session identifier
            
        Raises:
            HTTPException: If limit is exceeded
        """
        current_count = self.session_counts.get(session_id, 0)
        
        if current_count >= self.file_limit:
            logger.warning(f"Session {session_id} exceeded file limit: {current_count}/{self.file_limit}")
            raise HTTPException(
                status_code=429,
                detail=f"Session file upload limit exceeded. Maximum {self.file_limit} files per session."
            )
        
        # Increment count
        self.session_counts[session_id] = current_count + 1
        logger.debug(f"Session {session_id} file count: {self.session_counts[session_id]}/{self.file_limit}")
    
    def get_session_count(self, session_id: str) -> int:
        """Get current file count for a session."""
        return self.session_counts.get(session_id, 0)
    
    def reset_session(self, session_id: str) -> None:
        """Reset file count for a session."""
        self.session_counts[session_id] = 0
        logger.info(f"Reset file count for session {session_id}")


def get_rate_limiter(settings: Settings) -> RateLimiter:
    """Get or create the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter(settings)
    return _rate_limiter


def check_session_file_limit(
    request: Request,
    settings: Settings = Depends(get_application_settings)
) -> None:
    """
    FastAPI dependency to check session file upload limit.
    
    Args:
        request: The FastAPI request object
        settings: The application settings
        
    Raises:
        HTTPException: If session not found or limit exceeded
    """
    session_id = request.session.get("session_id")
    if not session_id:
        logger.error("Session ID not found in request")
        raise HTTPException(
            status_code=400,
            detail="Session not found. Please refresh the page and try again."
        )
    
    rate_limiter = get_rate_limiter(settings)
    rate_limiter.check_limit(session_id)


def check_global_request_limit(
    settings: Settings = Depends(get_application_settings)
) -> None:
    """
    FastAPI dependency to check global request limit across all users.
    
    Args:
        settings: The application settings
        
    Raises:
        HTTPException: If global request limit exceeded
    """
    global _global_request_count
    
    # Check if limiting is enabled (0 means unlimited)
    if settings.MAX_TOTAL_REQUESTS == 0:
        return
    
    # Check if limit exceeded
    if _global_request_count >= settings.MAX_TOTAL_REQUESTS:
        logger.warning(f"Global request limit exceeded: {_global_request_count}/{settings.MAX_TOTAL_REQUESTS}")
        raise HTTPException(
            status_code=503,
            detail=f"Application request limit reached. Maximum {settings.MAX_TOTAL_REQUESTS} requests allowed since startup."
        )
    
    # Increment global counter
    _global_request_count += 1
    logger.debug(f"Global request count: {_global_request_count}/{settings.MAX_TOTAL_REQUESTS}")


def get_global_request_count() -> int:
    """Get current global request count."""
    return _global_request_count


def reset_global_request_count() -> None:
    """Reset global request count (for testing purposes)."""
    global _global_request_count
    _global_request_count = 0
    logger.info("Global request count reset to 0")