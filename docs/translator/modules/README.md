# Translator Modules Documentation

This directory contains comprehensive documentation for all modules in the subtitle translation system. Each module is documented with detailed API references, integration patterns, and practical examples.

## Module Overview

The translator system consists of seven core modules that work together to provide a robust, scalable subtitle translation pipeline:

### 🔧 Foundation Modules

- **[exceptions.py](./exceptions.md)** - Custom exception hierarchy for domain-specific error handling
- **[models.py](./models.md)** - Core data structures and type definitions
- **[gemini_helper.py](./gemini_helper.md)** - AI client initialization and management

### 🔄 Processing Pipeline Modules

- **[parser.py](./parser.md)** - SRT file parsing, validation, and chunking
- **[context_detector.py](./context_detector.md)** - AI-powered context detection for enhanced translation quality
- **[chunk_translator.py](./chunk_translator.md)** - Concurrent chunk translation with retry logic and statistics
- **[reassembler.py](./reassembler.md)** - SRT file reconstruction and output generation

## Translation Pipeline Flow

```
📁 SRT File Input
    ↓
📋 parser.py → SubtitleBlock chunks
    ↓
🔍 context_detector.py → Media context analysis
    ↓
🚀 chunk_translator.py → Parallel AI translation
    ↓
🔧 reassembler.py → Final SRT output
    ↓
📁 Translated SRT File
```

## Key Design Patterns

### 1. **Async/Await Pattern**
- Used throughout for non-blocking I/O operations
- Enables high-performance concurrent processing
- Supports scalable web application architecture

### 2. **Retry Pattern with Statistics**
- Configurable retry logic with exponential backoff
- Comprehensive failure tracking and statistics
- Graceful degradation on partial failures

### 3. **Semaphore-Based Concurrency Control**
- Rate limiting for AI service requests
- Resource management and backpressure handling
- Prevents overwhelming external services

### 4. **Domain-Specific Exception Hierarchy**
- Clear error categorization and handling
- Enhanced debugging and monitoring capabilities
- Consistent error propagation patterns

### 5. **Strategy Pattern for Processing Modes**
- Multiple processing modes (mock, fast, normal)
- Runtime mode selection based on requirements
- Flexible quality vs. performance tradeoffs

## Integration Architecture

### Data Flow Integration
```python
# Core data model flows through entire pipeline
SubtitleBlock → Chunks → AI Processing → Reassembly → Output
```

### Error Handling Integration
```python
# Consistent error handling across all modules
try:
    result = await process_function()
except TranslatorError as e:
    # Domain-specific error handling
    logger.error(f"Translation failed: {e}")
```

### Configuration Integration
```python
# Centralized configuration through Settings
settings = Settings()
retry_attempts = settings.RETRY_MAX_ATTEMPTS
ai_model = settings.FAST_MODEL if fast_mode else settings.NORMAL_MODEL
```

## Performance Characteristics

### Concurrency and Scalability
- **Parallel Processing**: Chunks processed concurrently for optimal throughput
- **Rate Limiting**: Semaphore-based control prevents service overload
- **Memory Efficiency**: Streaming processing and minimal memory footprint
- **Resource Management**: Proper cleanup and resource lifecycle management

### Error Resilience
- **Partial Failure Handling**: Individual chunk failures don't stop overall processing
- **Retry Logic**: Automatic retry with configurable attempts and backoff
- **Fallback Strategies**: Graceful degradation to original content when translation fails
- **Statistics Tracking**: Detailed metrics for monitoring and debugging

### Quality Assurance
- **Schema Validation**: AI responses validated against strict schemas
- **Content Integrity**: Original timing and structure preserved
- **Type Safety**: Strong typing throughout the pipeline
- **Format Compliance**: Standards-compliant SRT output generation

## Usage Examples

### Basic Translation Pipeline
```python
import asyncio
from translator import *

async def translate_subtitle_file():
    # 1. Parse SRT file
    chunks = await parse_srt("input.srt", chunk_max_blocks=10)
    
    # 2. Initialize AI client
    client = init_genai_client(settings)
    
    # 3. Detect context
    context = await detect_context(chunks, "normal", client, settings)
    
    # 4. Translate chunks
    semaphore = asyncio.Semaphore(5)
    retries, failures = await translate_all_chunks(
        context, chunks, "Spanish", "normal", client, settings, semaphore
    )
    
    # 5. Reassemble output
    output = reassemble_srt(chunks)
    
    # 6. Save result
    with open("output.srt", "wb") as f:
        f.write(output)
    
    return retries, failures

# Run translation
retries, failures = asyncio.run(translate_subtitle_file())
```

### Error Handling Example
```python
from translator.exceptions import *

try:
    chunks = await parse_srt(file_path, chunk_size)
except ValidationError as e:
    return {"error": "Invalid file", "details": str(e)}
except ParsingError as e:
    return {"error": "Parsing failed", "details": str(e)}
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return {"error": "Internal error"}
```

### Statistics and Monitoring
```python
# Translation provides detailed statistics
total_retries, failed_chunks = await translate_all_chunks(...)

# Calculate success metrics
total_chunks = len(chunks)
success_rate = (total_chunks - failed_chunks) / total_chunks * 100
average_retries = total_retries / total_chunks

logger.info(f"Translation completed: {success_rate:.1f}% success rate")
logger.info(f"Average retries per chunk: {average_retries:.1f}")
```

## Testing and Development

### Mock Mode Support
All modules support mock mode for testing and development:

```python
# Use mock mode for testing without AI service dependencies
context = await detect_context(chunks, "mock", None, settings)
retries, failures = await translate_all_chunks(
    context, chunks, "Spanish", "mock", None, settings, semaphore
)
```

### Configuration Testing
```python
# Test with different retry configurations
test_settings = Settings(RETRY_MAX_ATTEMPTS=3, FAST_MODEL="gemini-1.5-flash")
```

## Performance Monitoring

### Key Metrics to Track
- **Success Rate**: Percentage of successfully translated chunks
- **Retry Rate**: Average number of retries per chunk
- **Processing Time**: Time per chunk and total pipeline duration
- **Memory Usage**: Peak memory consumption during processing
- **Concurrency Utilization**: Semaphore slot usage patterns

### Logging Integration
All modules provide comprehensive logging:
- **Debug Level**: Detailed operation traces
- **Info Level**: Major milestone completion
- **Warning Level**: Retry attempts and recoverable errors
- **Error Level**: Failures and exception details

## Best Practices

### 1. **Semaphore Configuration**
```python
# Balance concurrency with service limits
semaphore = asyncio.Semaphore(5)  # Adjust based on API rate limits
```

### 2. **Chunk Size Optimization**
```python
# Balance memory usage with processing efficiency
chunk_max_blocks = 10  # Optimal for most use cases
```

### 3. **Error Handling**
```python
# Always handle domain-specific exceptions
try:
    result = await translation_operation()
except ChunkTranslationError as e:
    # Handle translation-specific failures
except GenAIRequestError as e:
    # Handle AI service issues
```

### 4. **Resource Management**
```python
# Proper async context management
async with aiofiles.open(file_path) as f:
    content = await f.read()
```

This comprehensive module documentation provides the foundation for understanding, maintaining, and extending the subtitle translation system. Each module is designed to work independently while integrating seamlessly with the overall pipeline architecture.