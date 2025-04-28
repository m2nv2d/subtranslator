#!/usr/bin/env python3
"""
Manual test script to verify error responses from the API.

This script simulates various error conditions and prints the expected 
HTTP response that would be sent by the API.

Usage:
    Run with: uv run tests/manual/test_error_responses.py
"""

import sys
import json
from pathlib import Path

# Add project root to sys.path to enable absolute imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root / "src"))

from translator.exceptions import (
    ValidationError,
    ParsingError,
    ContextDetectionError,
    ChunkTranslationError
)
from core.errors import create_error_response


def simulate_error_response(exception, status_code):
    """Simulate an API error response for a given exception"""
    response = create_error_response(str(exception))
    print(f"\nHTTP {status_code} Response:")
    print(f"Status Code: {status_code}")
    print(f"Content: {json.dumps(response, indent=4)}")
    return response


def main():
    print("Testing Error Response Models\n")
    print("This script simulates different error conditions and shows")
    print("how they would be formatted in HTTP responses.\n")

    # Validation Error (HTTP 400)
    print("=== 1. Validation Error (HTTP 400) ===")
    validation_error = ValidationError("Invalid file type. Please upload an SRT file.")
    simulate_error_response(validation_error, 400)

    # Parsing Error (HTTP 422)
    print("\n=== 2. Parsing Error (HTTP 422) ===")
    parsing_error = ParsingError("Failed to parse SRT file: Invalid format at line 45")
    simulate_error_response(parsing_error, 422)

    # Context Detection Error (HTTP 500)
    print("\n=== 3. Context Detection Error (HTTP 500) ===")
    context_error = ContextDetectionError("Failed to generate context from subtitle content")
    simulate_error_response(context_error, 500)

    # Chunk Translation Error (HTTP 500)
    print("\n=== 4. Chunk Translation Error (HTTP 500) ===")
    translation_error = ChunkTranslationError("Translation failed for chunk 3")
    simulate_error_response(translation_error, 500)

    # Generic Error (HTTP 500)
    print("\n=== 5. Generic Error (HTTP 500) ===")
    response = create_error_response("An unexpected internal server error occurred.")
    print(f"HTTP 500 Response:")
    print(f"Status Code: 500")
    print(f"Content: {json.dumps(response, indent=4)}")

    # HTTP Exception (HTTP 503)
    print("\n=== 6. HTTP Exception (HTTP 503) ===")
    response = create_error_response("Service Unavailable: Translation backend not ready")
    print(f"HTTP 503 Response:")
    print(f"Status Code: 503")
    print(f"Content: {json.dumps(response, indent=4)}")

    print("\nAll error responses use the standardized ErrorDetail format.")
    print("This ensures consistent error handling in the frontend.")


if __name__ == "__main__":
    main() 