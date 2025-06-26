# Test Documentation: test_parser.py

## Test File Purpose
- **What is being tested**: SRT file parsing functionality and chunk creation
- **Type of tests**: Manual unit test for subtitle parsing
- **Scope and coverage**: Tests SRT file parsing, validation, and chunking with different file sizes and parameters

## Test Cases

### Main Parser Test
- **Test Name/Function**: `main()`
- **Scenario**: Tests SRT parser with different sample files and configurable chunk sizes
- **Inputs**: 
  - Command line arguments: sample file name (short/medium/long), max blocks per chunk
  - SRT sample files with different content volumes
  - Configurable chunk size limits (default: 100 blocks)
- **Expected Pass**: 
  - Successfully locates and reads SRT sample file
  - Parses SRT content into subtitle blocks with proper timing
  - Creates appropriate number of chunks based on max blocks setting
  - Displays parsed content with index, timing, and text preview
  - Handles content formatting and display (newline replacement, truncation)
- **Expected Fail**: 
  - Sample file not found at expected path
  - SRT file format validation errors (ValidationError)
  - Parsing errors for malformed SRT content (ParsingError)
  - Empty or invalid SRT files
  - File system access issues
- **Coverage**: 
  - SRT file format parsing and validation
  - Subtitle block creation with timing information
  - Chunk creation based on size limits
  - Content preview and formatting
  - Error handling for parsing failures
  - File existence validation
  - Content display and truncation logic

## Test Patterns
- **Testing frameworks and tools used**: 
  - Python asyncio for asynchronous file operations
  - argparse for command-line parameter handling
  - Custom exception types (ValidationError, ParsingError)
  - pathlib for file system operations
- **Mock strategies**: 
  - No mocking - tests against real SRT files
  - Direct file parsing to validate actual functionality
- **Setup and teardown patterns**: 
  - Project root path resolution
  - Sample file path construction
  - File existence validation before processing
  - Exception handling with stack trace for debugging
- **Data fixtures used**: 
  - Sample SRT files: short.srt, medium.srt, long.srt
  - Configurable chunk size parameters
  - Real subtitle content with timing and text data