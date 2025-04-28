import sys
import unittest
from pathlib import Path

# Add project root to sys.path to enable absolute imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))

from core.errors import ErrorDetail, create_error_response


class TestErrorModels(unittest.TestCase):
    """Test cases for the error response models"""
    
    def test_error_detail_model(self):
        """Test that ErrorDetail model works as expected"""
        # Test with just an error message
        error = ErrorDetail(error="Test error message")
        self.assertEqual(error.error, "Test error message")
        self.assertIsNone(error.detail)
        
        # Test with error and detail
        error = ErrorDetail(error="Test error message", detail="Additional details")
        self.assertEqual(error.error, "Test error message")
        self.assertEqual(error.detail, "Additional details")
        
        # Test conversion to dict
        error_dict = error.model_dump()
        self.assertEqual(error_dict, {
            "error": "Test error message",
            "detail": "Additional details"
        })
    
    def test_create_error_response(self):
        """Test the create_error_response helper function"""
        # Test with just an error message
        response = create_error_response("Test error message")
        self.assertEqual(response, {
            "error": "Test error message",
            "detail": None
        })
        
        # Test with error and detail
        response = create_error_response("Test error message", "Additional details")
        self.assertEqual(response, {
            "error": "Test error message",
            "detail": "Additional details"
        })


if __name__ == "__main__":
    unittest.main() 