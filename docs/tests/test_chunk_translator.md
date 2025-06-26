# Test Documentation: test_chunk_translator.py

## Test File Purpose
- **What is being tested**: Full end-to-end chunk translation functionality including parsing, context detection, and chunk translation
- **Type of tests**: Manual integration test
- **Scope and coverage**: Tests the complete chunk translation workflow from SRT file parsing through context detection to final translation of all chunks

## Test Cases

### Main Test Function
- **Test Name/Function**: `main()`
- **Scenario**: Tests the complete chunk translation pipeline with different sample files and speed modes
- **Inputs**: 
  - Command line arguments: sample file name (short/medium/long), speed mode (mock/fast/normal), log level
  - SRT sample files from tests/samples directory
  - Configuration settings from environment
- **Expected Pass**: 
  - Successfully loads configuration
  - Initializes GenAI client (for non-mock modes)
  - Parses SRT file into subtitle chunks
  - Detects context from subtitle content
  - Translates all chunks using the specified speed mode
  - Displays first 20 translated blocks with original and translated content
- **Expected Fail**: 
  - Configuration loading errors
  - GenAI client initialization failures (for real API calls)
  - SRT file not found or parsing errors
  - Context detection failures
  - Translation API errors or timeout issues
  - ChunkTranslationError exceptions
- **Coverage**: 
  - Configuration loading and validation
  - GenAI client initialization
  - SRT file parsing with chunking
  - Context detection functionality
  - Asynchronous chunk translation with semaphore control
  - Error handling for translation failures
  - Result display and validation

## Test Patterns
- **Testing frameworks and tools used**: 
  - Native Python asyncio for async testing
  - argparse for command-line interface
  - Python logging for test output and debugging
- **Mock strategies**: 
  - Speed mode "mock" bypasses actual API calls
  - Configurable speed modes allow testing with/without real API integration
- **Setup and teardown patterns**: 
  - Dynamic path resolution to project root
  - Logging configuration with adjustable levels
  - Manual semaphore creation for concurrency control
  - Graceful error handling with specific exception types
- **Data fixtures used**: 
  - Sample SRT files: short.srt, medium.srt, long.srt
  - Environment-based configuration via .env files
  - Configurable chunk sizes and translation limits