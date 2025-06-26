# Test Documentation: test_reassembly_flow.py

## Test File Purpose
- **What is being tested**: Complete end-to-end subtitle translation and reassembly workflow
- **Type of tests**: Manual integration test for full translation pipeline
- **Scope and coverage**: Tests the entire workflow from SRT parsing through translation to final reassembled output file

## Test Cases

### Main Reassembly Flow Test
- **Test Name/Function**: `main()`
- **Scenario**: Tests complete translation pipeline including parsing, context detection, translation, and reassembly to output file
- **Inputs**: 
  - Command line arguments: sample file name (short/medium/long), speed mode (mock/fast/normal), log level
  - SRT sample files from tests/samples directory
  - Configuration settings for translation parameters
- **Expected Pass**: 
  - Successfully loads configuration and initializes services
  - Parses SRT file into subtitle chunks
  - Detects context from subtitle content
  - Translates all chunks using specified speed mode
  - Reassembles translated content into valid SRT format
  - Writes output file with "_translated.srt" suffix
  - Creates valid output file readable by subtitle players
- **Expected Fail**: 
  - Configuration or GenAI client initialization errors
  - SRT file parsing failures
  - Context detection failures
  - Translation errors (ChunkTranslationError)
  - Reassembly errors or format validation issues
  - File system errors during output writing
  - Network or API communication failures
- **Coverage**: 
  - Complete workflow integration testing
  - SRT parsing with chunking
  - Context detection functionality
  - Asynchronous translation with concurrency control
  - SRT reassembly and format validation
  - File output operations
  - Error propagation throughout pipeline
  - Resource cleanup and error recovery

## Test Patterns
- **Testing frameworks and tools used**: 
  - Python asyncio for asynchronous workflow testing
  - argparse for command-line interface
  - Python logging with configurable levels
  - File I/O operations for output validation
- **Mock strategies**: 
  - Mock mode for translation testing without API calls
  - Configurable speed modes for different test scenarios
  - Optional GenAI client based on testing mode
- **Setup and teardown patterns**: 
  - Project root and source path resolution
  - Logging configuration with package filtering
  - Manual semaphore creation for concurrency control
  - Output file cleanup and validation
  - Exception propagation with workflow termination
- **Data fixtures used**: 
  - Sample SRT files with different complexity levels
  - Environment-based configuration
  - Output directory for translated files
  - Expected file naming conventions