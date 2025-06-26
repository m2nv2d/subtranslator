# Test Documentation: test_context_detector.py

## Test File Purpose
- **What is being tested**: Context detection functionality from subtitle content
- **Type of tests**: Manual integration test for AI-powered context detection
- **Scope and coverage**: Tests the context detection pipeline including SRT parsing, GenAI client initialization, and context analysis

## Test Cases

### Main Context Detection Test
- **Test Name/Function**: `main()`
- **Scenario**: Tests context detection from different sample subtitle files using various speed modes
- **Inputs**: 
  - Command line arguments: sample file name (short/medium/long), speed mode (mock/fast/normal), log level
  - SRT sample files with different content lengths and complexity
  - Configuration settings for AI models and API access
- **Expected Pass**: 
  - Successfully loads configuration from settings
  - Initializes GenAI client for non-mock modes
  - Parses SRT file into subtitle chunks
  - Detects meaningful context from subtitle content
  - Returns context string suitable for translation prompts
- **Expected Fail**: 
  - Sample file not found at expected path
  - Configuration loading errors
  - GenAI client initialization failures
  - SRT parsing errors (ParsingError, ValidationError)
  - Context detection failures (ContextDetectionError)
  - API communication errors or timeouts
- **Coverage**: 
  - Configuration loading and validation
  - GenAI client initialization with error handling
  - SRT file parsing with chunk size limits
  - Context detection with different speed modes
  - Error handling for multiple exception types
  - File existence validation
  - Logging and debugging output

## Test Patterns
- **Testing frameworks and tools used**: 
  - Python asyncio for asynchronous testing
  - argparse for command-line parameter handling
  - Python logging with configurable levels
  - Custom exception types for specific error conditions
- **Mock strategies**: 
  - Mock mode bypasses actual AI API calls
  - Configurable speed modes for different testing scenarios
  - Optional GenAI client initialization based on mode
- **Setup and teardown patterns**: 
  - Dynamic project root and source path resolution
  - Logging configuration with package-specific filtering
  - Graceful error handling with specific exception catching
  - System exit codes for different failure modes
- **Data fixtures used**: 
  - Sample SRT files with varying content complexity
  - Environment-based configuration
  - Configurable chunk sizes for different parsing scenarios