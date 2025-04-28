import os
import sys
import unittest
from pathlib import Path

# Add project root to sys.path to enable absolute imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))

import pytest
from pydantic import ValidationError

from src.core.config import Settings


class TestPydanticSettings(unittest.TestCase):
    """Test cases for the Pydantic Settings model"""
    
    def setUp(self):
        """Clear environment variables that might affect tests"""
        # Clear environment variables that might affect tests
        for key in list(os.environ.keys()):
            if key in ["AI_PROVIDER", "AI_API_KEY", "FAST_MODEL", "NORMAL_MODEL", 
                      "TARGET_LANGUAGES", "CHUNK_MAX_BLOCKS", "RETRY_MAX_ATTEMPTS", 
                      "LOG_LEVEL"]:
                del os.environ[key]
                
        # Configure Settings to not look for a .env file during tests
        Settings.model_config["env_file"] = None
    
    def test_required_fields(self):
        """Test that required fields must be present"""
        # AI_API_KEY is required
        with pytest.raises(ValidationError):
            Settings()
        
        # With API key provided, it should work
        os.environ["AI_API_KEY"] = "test-api-key"
        settings = Settings()
        self.assertEqual(settings.AI_API_KEY, "test-api-key")
        
    def test_default_values(self):
        """Test that default values are applied correctly"""
        os.environ["AI_API_KEY"] = "test-api-key"
        settings = Settings()
        
        # Check defaults
        self.assertEqual(settings.AI_PROVIDER, "google-gemini")
        self.assertEqual(settings.FAST_MODEL, "gemini-2.5-flash-preview-04-17")
        self.assertEqual(settings.NORMAL_MODEL, "gemini-2.5-pro-preview-03-25")
        self.assertEqual(settings.TARGET_LANGUAGES, ["Vietnamese", "French"])
        self.assertEqual(settings.CHUNK_MAX_BLOCKS, 100)
        self.assertEqual(settings.RETRY_MAX_ATTEMPTS, 6)
        self.assertEqual(settings.LOG_LEVEL, "INFO")
    
    def test_custom_values(self):
        """Test that custom values override defaults"""
        # Use comma-separated string for TARGET_LANGUAGES
        os.environ.update({
            "AI_API_KEY": "custom-api-key",
            "AI_PROVIDER": "custom-provider",
            "FAST_MODEL": "custom-fast-model",
            "NORMAL_MODEL": "custom-normal-model",
            "TARGET_LANGUAGES": "Spanish,German,Italian",
            "CHUNK_MAX_BLOCKS": "50",
            "RETRY_MAX_ATTEMPTS": "3",
            "LOG_LEVEL": "DEBUG"
        })
        
        settings = Settings()
        self.assertEqual(settings.AI_API_KEY, "custom-api-key")
        self.assertEqual(settings.AI_PROVIDER, "custom-provider")
        self.assertEqual(settings.FAST_MODEL, "custom-fast-model")
        self.assertEqual(settings.NORMAL_MODEL, "custom-normal-model")
        self.assertEqual(settings.TARGET_LANGUAGES, ["Spanish", "German", "Italian"])
        self.assertEqual(settings.CHUNK_MAX_BLOCKS, 50)
        self.assertEqual(settings.RETRY_MAX_ATTEMPTS, 3)
        self.assertEqual(settings.LOG_LEVEL, "DEBUG")
    
    def test_validation_rules(self):
        """Test that validation rules are enforced"""
        os.environ["AI_API_KEY"] = "test-api-key"
        
        # Test CHUNK_MAX_BLOCKS validation (must be positive)
        os.environ["CHUNK_MAX_BLOCKS"] = "0"
        with pytest.raises(ValidationError):
            Settings()
        
        os.environ["CHUNK_MAX_BLOCKS"] = "-10"
        with pytest.raises(ValidationError):
            Settings()
        
        # Test valid CHUNK_MAX_BLOCKS
        os.environ["CHUNK_MAX_BLOCKS"] = "10"
        settings = Settings()
        self.assertEqual(settings.CHUNK_MAX_BLOCKS, 10)
        
        # Test LOG_LEVEL validation
        os.environ["LOG_LEVEL"] = "INVALID_LEVEL"
        settings = Settings()
        # Should default to INFO when invalid
        self.assertEqual(settings.LOG_LEVEL, "INFO")
        
        # Test TARGET_LANGUAGES validation with empty string
        os.environ["TARGET_LANGUAGES"] = ""
        settings = Settings()
        # Should use default when empty
        self.assertEqual(settings.TARGET_LANGUAGES, ["Vietnamese", "French"])
        
        # Test TARGET_LANGUAGES with spaces
        os.environ["TARGET_LANGUAGES"] = "Spanish, German,  Italian"
        settings = Settings()
        self.assertEqual(settings.TARGET_LANGUAGES, ["Spanish", "German", "Italian"])


if __name__ == "__main__":
    unittest.main() 