# Test Documentation: test_translate_api.sh

## Test File Purpose
- **What is being tested**: HTTP API endpoint for file upload and translation
- **Type of tests**: Manual API integration test using shell script
- **Scope and coverage**: Tests the web API translation endpoint with real file uploads and HTTP requests

## Test Cases

### API Translation Test
- **Test Name/Function**: Shell script execution
- **Scenario**: Tests HTTP POST endpoint for subtitle file translation using curl
- **Inputs**: 
  - Command line arguments: SRT size (short/medium/long), target language (default: Vietnamese)
  - Sample SRT files from tests/samples directory
  - HTTP form data: file upload, target language, speed mode
  - Local development server running on port 5100
- **Expected Pass**: 
  - Successfully uploads SRT file via HTTP POST
  - Server accepts multipart form data with file and parameters
  - Translation process completes successfully
  - Receives translated SRT file as HTTP response
  - Output file is saved with proper naming convention
  - Translated content is valid SRT format
- **Expected Fail**: 
  - Server not running on expected port (5100)
  - Invalid SRT file size parameter
  - File upload errors or HTTP 400/500 responses
  - Translation service errors
  - Network connectivity issues
  - Output file corruption or invalid format
- **Coverage**: 
  - HTTP API endpoint testing
  - Multipart file upload functionality
  - Form parameter handling (target_lang, speed_mode)
  - Server response validation
  - File output and naming conventions
  - API error handling and HTTP status codes

## Test Patterns
- **Testing frameworks and tools used**: 
  - Bash shell scripting for HTTP testing
  - curl for HTTP client operations
  - Shell parameter validation and error handling
- **Mock strategies**: 
  - No mocking - tests against running development server
  - Real HTTP requests to validate API functionality
- **Setup and teardown patterns**: 
  - Parameter validation with regular expressions
  - Default values for optional parameters
  - File path construction and validation
  - HTTP request configuration with proper headers
- **Data fixtures used**: 
  - Sample SRT files: short.srt, medium.srt, long.srt
  - Configurable target languages
  - Standard HTTP form data format
  - Expected output file naming patterns