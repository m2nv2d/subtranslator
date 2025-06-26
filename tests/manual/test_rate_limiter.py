import pytest
from unittest.mock import Mock, patch
from fastapi import HTTPException, Request
from starlette.middleware.sessions import SessionMiddleware
from starlette.testclient import TestClient

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src'))

from core.rate_limiter import RateLimiter, get_rate_limiter, check_session_file_limit
from core.config import Settings


class TestRateLimiter:
    
    def test_rate_limiter_initialization(self):
        settings = Mock()
        settings.SESSION_FILE_LIMIT = 25
        
        rate_limiter = RateLimiter(settings)
        
        assert rate_limiter.file_limit == 25
        assert rate_limiter.session_counts == {}
    
    def test_check_limit_new_session(self):
        settings = Mock()
        settings.SESSION_FILE_LIMIT = 50
        rate_limiter = RateLimiter(settings)
        
        session_id = "new_session_123"
        
        # Should not raise exception for new session
        rate_limiter.check_limit(session_id)
        
        # Session should be initialized with count of 1
        assert rate_limiter.session_counts[session_id] == 1
    
    def test_check_limit_under_limit(self):
        settings = Mock()
        settings.SESSION_FILE_LIMIT = 50
        rate_limiter = RateLimiter(settings)
        
        session_id = "test_session"
        rate_limiter.session_counts[session_id] = 25
        
        # Should not raise exception when under limit
        rate_limiter.check_limit(session_id)
        
        # Count should increment
        assert rate_limiter.session_counts[session_id] == 26
    
    def test_check_limit_at_limit(self):
        settings = Mock()
        settings.SESSION_FILE_LIMIT = 50
        rate_limiter = RateLimiter(settings)
        
        session_id = "test_session"
        rate_limiter.session_counts[session_id] = 50
        
        # Should raise exception when at limit
        with pytest.raises(HTTPException) as exc_info:
            rate_limiter.check_limit(session_id)
        
        assert exc_info.value.status_code == 429
        assert "Session file upload limit exceeded" in str(exc_info.value.detail)
        
        # Count should not increment
        assert rate_limiter.session_counts[session_id] == 50
    
    def test_check_limit_over_limit(self):
        settings = Mock()
        settings.SESSION_FILE_LIMIT = 50
        rate_limiter = RateLimiter(settings)
        
        session_id = "test_session"
        rate_limiter.session_counts[session_id] = 55  # Already over limit
        
        # Should raise exception when over limit
        with pytest.raises(HTTPException) as exc_info:
            rate_limiter.check_limit(session_id)
        
        assert exc_info.value.status_code == 429
        assert "Session file upload limit exceeded" in str(exc_info.value.detail)
        
        # Count should not increment
        assert rate_limiter.session_counts[session_id] == 55
    
    def test_get_session_count_existing(self):
        settings = Mock()
        settings.SESSION_FILE_LIMIT = 50
        rate_limiter = RateLimiter(settings)
        
        session_id = "test_session"
        rate_limiter.session_counts[session_id] = 25
        
        count = rate_limiter.get_session_count(session_id)
        assert count == 25
    
    def test_get_session_count_new(self):
        settings = Mock()
        settings.SESSION_FILE_LIMIT = 50
        rate_limiter = RateLimiter(settings)
        
        session_id = "new_session"
        
        count = rate_limiter.get_session_count(session_id)
        assert count == 0
    
    def test_reset_session(self):
        settings = Mock()
        settings.SESSION_FILE_LIMIT = 50
        rate_limiter = RateLimiter(settings)
        
        session_id = "test_session"
        rate_limiter.session_counts[session_id] = 25
        
        rate_limiter.reset_session(session_id)
        
        assert rate_limiter.session_counts[session_id] == 0


class TestCheckSessionFileLimit:
    
    def test_check_session_file_limit_no_session(self):
        request = Mock()
        request.session = {}
        
        rate_limiter = Mock()
        
        # Should raise exception when no session ID
        with pytest.raises(HTTPException) as exc_info:
            check_session_file_limit(request, rate_limiter)
        
        assert exc_info.value.status_code == 400
        assert "Session not found" in str(exc_info.value.detail)
    
    def test_check_session_file_limit_with_session(self):
        request = Mock()
        request.session = {"session_id": "test_session_123"}
        
        rate_limiter = Mock()
        
        # Should call rate_limiter.check_limit with session ID
        check_session_file_limit(request, rate_limiter)
        
        rate_limiter.check_limit.assert_called_once_with("test_session_123")
    
    def test_check_session_file_limit_rate_limit_exceeded(self):
        request = Mock()
        request.session = {"session_id": "test_session_123"}
        
        rate_limiter = Mock()
        rate_limiter.check_limit.side_effect = HTTPException(
            status_code=429, 
            detail="Session file upload limit exceeded"
        )
        
        # Should propagate HTTPException from rate_limiter
        with pytest.raises(HTTPException) as exc_info:
            check_session_file_limit(request, rate_limiter)
        
        assert exc_info.value.status_code == 429
        assert "Session file upload limit exceeded" in str(exc_info.value.detail)


class TestGetRateLimiter:
    
    @patch('core.rate_limiter._rate_limiter', None)
    def test_get_rate_limiter_initialization(self):
        settings = Mock()
        settings.SESSION_FILE_LIMIT = 25
        
        rate_limiter = get_rate_limiter(settings)
        
        assert isinstance(rate_limiter, RateLimiter)
        assert rate_limiter.file_limit == 25
    
    def test_get_rate_limiter_singleton(self):
        settings1 = Mock()
        settings1.SESSION_FILE_LIMIT = 25
        settings2 = Mock()
        settings2.SESSION_FILE_LIMIT = 30
        
        # First call should create new instance
        rate_limiter1 = get_rate_limiter(settings1)
        
        # Second call should return same instance (singleton)
        rate_limiter2 = get_rate_limiter(settings2)
        
        # Should return same instance regardless of settings
        assert rate_limiter1 is rate_limiter2