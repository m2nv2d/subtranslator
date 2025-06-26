# Translator Components Overview

## Purpose

The `translator` package contains the core business logic for subtitle translation. This package implements the complete translation pipeline from SRT file parsing through AI-powered translation to final file reassembly, following a clear separation of responsibilities.

## Internal Structure

```
src/translator/
├── __init__.py              # Package exports and public API
├── chunk_translator.py      # Concurrent translation processing
├── context_detector.py      # AI-powered context detection
├── exceptions.py            # Domain-specific exceptions
├── gemini_helper.py         # AI client initialization utilities
├── models.py                # Core data models (SubtitleBlock)
├── parser.py                # SRT file parsing and validation
└── reassembler.py           # Translation result reassembly
```

## Exposed Interface

### Public API Functions (exported in `__init__.py`)
- `parse_srt()`: Parse and validate SRT files into subtitle blocks
- `detect_context()`: Determine content context for improved translation
- `translate_all_chunks()`: Concurrent translation of subtitle chunks
- `reassemble_srt()`: Reconstruct translated subtitles into SRT format

### Data Models
- `SubtitleBlock`: Core data structure representing a single subtitle
- `TranslatedBlock`: Pydantic model for AI response validation
- `TranslatedChunk`: Type alias for chunk-level translation validation

### Exception Classes
- `ValidationError`: Input validation failures
- `ParsingError`: SRT file parsing issues
- `ContextDetectionError`: AI context detection failures
- `ChunkTranslationError`: Translation processing errors
- `GenAIClientInitError`: AI client initialization problems
- `GenAIRequestError`: AI service request failures
- `GenAIParsingError`: AI response parsing issues

## Design Pattern

The translator package follows a **Pipeline Architecture** with clear stages:

1. **Input Validation & Parsing**: Validate and parse SRT files
2. **Context Detection**: Analyze content for translation context
3. **Concurrent Translation**: Process chunks in parallel with semaphore control
4. **Response Validation**: Validate AI responses using Pydantic models
5. **Output Reassembly**: Reconstruct final SRT file from translated blocks

Each stage is implemented as a separate module with well-defined interfaces, enabling independent testing and maintenance.

## Integration Points

### With Core Components
- Receives configuration through dependency injection (`Settings`)
- Uses AI client provided by core dependencies (`genai.client.Client`)
- Reports statistics through core statistics store (`AppStatsStore`)
- Respects concurrency limits via semaphore from core dependencies

### With External Services
- **Google Gemini API**: For context detection and translation services
- **SRT Library**: For parsing and generating SubRip format files
- **File System**: For temporary file handling during processing

### With FastAPI Application
- Route handlers orchestrate the translation pipeline
- Exceptions are mapped to HTTP status codes
- Progress updates are integrated with request lifecycle

## Processing Pipeline

### Sequential Flow
```
SRT File → Validation → Parsing → Chunking → Context Detection
                                     ↓
Reassembly ← Response Validation ← Translation ← Concurrent Processing
```

### Concurrent Processing Detail
```
Chunks: [Chunk1, Chunk2, Chunk3, ..., ChunkN]
           ↓       ↓       ↓           ↓
        [Task1, Task2, Task3, ..., TaskN] (asyncio.TaskGroup)
           ↓       ↓       ↓           ↓
        [Result1, Result2, Result3, ..., ResultN]
```

## Key Features

### Concurrent Translation
- Uses `asyncio.TaskGroup` for parallel chunk processing
- Semaphore-based rate limiting to respect API constraints
- In-place modification of `SubtitleBlock` objects for memory efficiency
- Comprehensive error handling with retry logic

### Context-Aware Translation
- Analyzes sample content to determine context (e.g., "cooking tutorial", "drama")
- Context information is included in translation prompts
- Improves translation quality by providing domain-specific context

### Robust Error Handling
- Custom exception hierarchy for different failure types
- Configurable retry logic using Tenacity
- Graceful degradation when partial translations fail
- Detailed error reporting for debugging

### Validation and Type Safety
- Pydantic models ensure AI response validation
- Type hints throughout for compile-time checking
- Input validation at multiple pipeline stages
- Structured JSON schema enforcement for AI responses

## Best Practices

### File Processing
```python
# Correct usage pattern
chunks = await parse_srt(file_path, chunk_max_blocks)
context = await detect_context(chunks, speed_mode, client, settings)
failed_attempts, failed_chunks = await translate_all_chunks(
    context, chunks, target_lang, speed_mode, client, settings, semaphore
)
result = reassemble_srt(chunks)
```

### Error Handling
```python
# Proper exception handling
try:
    result = await translation_operation()
except (ParsingError, ContextDetectionError, ChunkTranslationError) as e:
    logger.error(f"Translation pipeline error: {e}")
    # Handle specific error types appropriately
```

### Resource Management
```python
# Semaphore usage for concurrency control
async with semaphore:
    # Perform AI translation request
    response = await client.agenerate_content(...)
```

## Performance Considerations

### Concurrency Management
- Global semaphore limits concurrent AI requests
- Configurable concurrency based on API rate limits
- TaskGroup ensures proper exception propagation in concurrent operations

### Memory Optimization
- In-place modification of subtitle blocks reduces memory usage
- Streaming file processing for large subtitle files
- Efficient chunking strategy balances memory and API efficiency

### API Efficiency
- Structured requests with proper JSON schemas
- Batch processing of subtitle chunks
- Retry logic with exponential backoff
- Context detection performed once per file

## Error Recovery

### Retry Mechanisms
- Configurable retry attempts with exponential backoff
- Per-chunk retry logic for granular error recovery
- Tenacity-based retry decorators for consistent behavior

### Partial Failure Handling
- Individual chunk failures don't abort entire translation
- Failed chunks retain original content as fallback
- Statistics tracking for failure analysis and monitoring

### Validation Fallbacks
- AI response validation with graceful degradation
- Default context used when context detection fails
- Original content preserved when translation fails

## Monitoring and Debugging

### Statistics Integration
- Track parsing results (chunks, blocks processed)
- Monitor translation attempts and failure rates
- Record processing times for performance analysis

### Logging Strategy
- Detailed logging at each pipeline stage
- Error context preservation for debugging
- Performance metrics logging for optimization

### Testing Support
- Mock modes for development and testing
- Configurable AI models for different speed/quality tradeoffs
- Comprehensive exception testing coverage