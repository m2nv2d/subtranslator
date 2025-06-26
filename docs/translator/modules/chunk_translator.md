# chunk_translator.py - Concurrent Chunk Translation Module

## Module Overview

**Purpose and responsibilities**: Orchestrates the parallel translation of subtitle chunks using AI services. Implements sophisticated retry logic, concurrent processing with semaphore-based rate limiting, and comprehensive error handling and statistics tracking.

**Design pattern used**: Concurrent processing pattern with async/await, TaskGroup orchestration, and decorator-based retry logic. Implements producer-consumer pattern with semaphore-based flow control and structured error handling.

**Integration points**:
- Core translation engine for the subtitle translation pipeline
- Integrates with AI client from gemini_helper module
- Uses Pydantic models for request/response validation
- Provides detailed statistics for monitoring and debugging
- Coordinates with context detection results for enhanced translation quality

## 🔍 Abstraction-Level Reference

### TranslatedBlock (Pydantic Model)

**Name and signature**: 
```python
class TranslatedBlock(BaseModel):
    index: int
    translated_lines: list[str]
```

**Description and purpose**: Pydantic model representing a single translated subtitle block with structured line-by-line translation results.

**Parameters**:
- `index` (int): The original subtitle block index for proper ordering
- `translated_lines` (list[str]): List of translated text lines preserving original line breaks

**Returns**: TranslatedBlock instance with validation

**Behavior**:
- Validates index is an integer
- Ensures translated_lines is a list of strings
- Supports JSON serialization/deserialization
- Maintains line structure from original subtitles

---

### TranslatedChunk (Pydantic RootModel)

**Name and signature**: 
```python
TranslatedChunk = RootModel[list[TranslatedBlock]]
```

**Description and purpose**: Pydantic root model representing a complete translated chunk containing multiple TranslatedBlock instances.

**Returns**: Validated list of TranslatedBlock objects

**Behavior**:
- Validates entire chunk structure against schema
- Ensures all blocks have required fields
- Supports JSON schema validation
- Provides structured error messages for validation failures

---

### configurable_retry (Decorator)

**Name and signature**: 
```python
def configurable_retry(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        # Complex retry logic with statistics tracking
```

**Description and purpose**: Advanced retry decorator that provides configurable retry logic with detailed statistics tracking, logging, and graceful error handling. Returns retry statistics instead of just the function result.

**Parameters**:
- `f`: The async function to wrap with retry logic

**Returns**: 
- `Tuple[int, bool]`: (number_of_retries, failed_flag) instead of original function result

**Behavior**:
1. **Settings Extraction**: Finds settings and chunk_index from function arguments
2. **Retry Configuration**: Uses `settings.RETRY_MAX_ATTEMPTS` for max attempts
3. **Attempt Tracking**: Tracks current attempt number and logs progress
4. **Exception Handling**: Handles different exception types (CancelledError, general exceptions)
5. **Statistics Collection**: Returns retry count and failure status
6. **Logging Integration**: Comprehensive logging of retry attempts and outcomes

**Raises**:
- Re-raises `asyncio.CancelledError` to stop retries immediately
- Wraps other exceptions in retry logic

**Example usage**:
```python
@configurable_retry
async def translate_chunk(chunk_index, chunk, settings, **kwargs):
    # Translation logic here
    pass

# Usage returns statistics instead of translation result
retries, failed = await translate_chunk(0, chunk_data, settings)
```

**Tips/Notes**:
- **Statistics Focus**: Returns statistics rather than function result
- **Cancellation Aware**: Properly handles asyncio cancellation
- **Logging Integration**: Detailed logging at multiple levels
- **Settings Driven**: All retry behavior controlled by application settings

---

### _translate_single_chunk

**Name and signature**: 
```python
@configurable_retry
async def _translate_single_chunk(
    chunk_index: int,
    chunk: list[SubtitleBlock],
    system_prompt: str,
    response_schema: genai.types.Schema,
    speed_mode: str,
    genai_client: Optional[genai.client.Client],
    settings: Settings,
    semaphore: asyncio.Semaphore,
) -> None
```

**Description and purpose**: Core translation function that processes a single chunk of subtitle blocks. Handles both mock translation for testing and real AI translation with comprehensive error handling and validation.

**Parameters**:
- `chunk_index` (int): Index of the chunk being processed (for logging/debugging)
- `chunk` (list[SubtitleBlock]): List of subtitle blocks to translate
- `system_prompt` (str): AI system prompt with context and instructions
- `response_schema` (genai.types.Schema): JSON schema for validating AI responses
- `speed_mode` (str): Processing mode ('mock', 'fast', 'normal')
- `genai_client` (Optional[genai.client.Client]): AI client for translation requests
- `settings` (Settings): Application configuration
- `semaphore` (asyncio.Semaphore): Concurrency control mechanism

**Returns**: `None` (modifies chunk blocks in-place, statistics returned by decorator)

**Behavior**:
1. **Semaphore Acquisition**: Controls concurrent AI requests
2. **Mode Processing**: Handles mock mode vs. real AI translation
3. **Request Preparation**: Formats subtitle content for AI processing
4. **AI Request**: Makes structured AI request with proper configuration
5. **Response Validation**: Validates AI response against expected schema
6. **Content Assignment**: Updates subtitle blocks with translated content
7. **Error Handling**: Comprehensive error handling with specific exceptions

**Raises**:
- `ChunkTranslationError`: AI response validation failures, JSON parsing errors, invalid block indices
- `json.JSONDecodeError`: JSON parsing failures (wrapped in ChunkTranslationError)
- `IndexError`: Invalid block index access (wrapped in ChunkTranslationError)
- `KeyError`: Missing required fields in AI response (wrapped in ChunkTranslationError)

**Example usage**:
```python
# This function is typically called through translate_all_chunks
# but can be used directly for single chunk translation

semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent requests
chunk = [SubtitleBlock(...), SubtitleBlock(...)]

# The decorator returns statistics, not the translation result
retries, failed = await _translate_single_chunk(
    chunk_index=0,
    chunk=chunk,
    system_prompt="Translate to Spanish...",
    response_schema=translation_schema,
    speed_mode="normal",
    genai_client=ai_client,
    settings=app_settings,
    semaphore=semaphore
)

# Check if translation succeeded
if not failed:
    # Translation succeeded, check chunk[i].translated_content
    for block in chunk:
        print(f"Original: {block.content}")
        print(f"Translated: {block.translated_content}")
```

**Tips/Notes**:
- **In-Place Modification**: Updates SubtitleBlock.translated_content directly
- **Semaphore Control**: Prevents overwhelming AI service with concurrent requests
- **Mock Mode**: Provides testing capability without AI service dependencies
- **Schema Validation**: Ensures AI responses match expected structure
- **Error Context**: Includes chunk index in all error messages for debugging

---

### translate_all_chunks

**Name and signature**: 
```python
async def translate_all_chunks(
    context: str,
    sub: list[list[SubtitleBlock]],
    target_lang: str,
    speed_mode: str,
    client: Optional[genai.client.Client],
    settings: Settings,
    semaphore: asyncio.Semaphore,
) -> Tuple[int, int]
```

**Description and purpose**: Main orchestration function that coordinates the concurrent translation of all subtitle chunks using asyncio TaskGroup. Provides comprehensive statistics tracking and error handling for the entire translation job.

**Parameters**:
- `context` (str): Detected context from context_detector module
- `sub` (list[list[SubtitleBlock]]): All subtitle chunks to translate
- `target_lang` (str): Target language for translation
- `speed_mode` (str): Processing mode ('mock', 'fast', 'normal')
- `client` (Optional[genai.client.Client]): AI client for translation requests
- `settings` (Settings): Application configuration
- `semaphore` (asyncio.Semaphore): Concurrency control mechanism

**Returns**: 
- `Tuple[int, int]`: (total_failed_attempts, total_chunks_with_failures)

**Behavior**:
1. **Prompt Generation**: Creates context-aware system prompt for AI
2. **Schema Definition**: Defines JSON schema for AI response validation
3. **Task Creation**: Creates concurrent tasks for all chunks using TaskGroup
4. **Execution Monitoring**: Tracks task execution and handles exceptions
5. **Statistics Aggregation**: Collects retry and failure statistics from all tasks
6. **Error Recovery**: Handles both individual task failures and TaskGroup exceptions
7. **Result Processing**: Aggregates results and provides comprehensive statistics

**Raises**:
- Catches and logs `ExceptionGroup` from TaskGroup failures
- Individual task failures are handled gracefully and converted to statistics

**Example usage**:
```python
from translator.chunk_translator import translate_all_chunks
import asyncio

# Set up concurrency control
semaphore = asyncio.Semaphore(5)  # Allow 5 concurrent translations

# Translate all chunks
total_retries, failed_chunks = await translate_all_chunks(
    context="This is a subtitle for a movie about space exploration",
    sub=parsed_chunks,
    target_lang="Spanish",
    speed_mode="normal",
    client=ai_client,
    settings=app_settings,
    semaphore=semaphore
)

# Check results
print(f"Translation completed:")
print(f"Total failed attempts: {total_retries}")
print(f"Chunks with failures: {failed_chunks}")
print(f"Success rate: {(len(parsed_chunks) - failed_chunks) / len(parsed_chunks) * 100:.1f}%")

# Check translated content
for chunk_idx, chunk in enumerate(parsed_chunks):
    for block in chunk:
        if block.translated_content:
            print(f"Chunk {chunk_idx}, Block {block.index}: {block.translated_content}")
```

**Tips/Notes**:
- **TaskGroup Integration**: Uses modern asyncio TaskGroup for reliable concurrent execution
- **Statistics Focused**: Returns detailed statistics instead of simple success/failure
- **Error Resilience**: Individual chunk failures don't stop overall processing
- **Resource Management**: Proper semaphore usage prevents resource exhaustion
- **Logging Integration**: Comprehensive logging throughout the process

---

## AI Integration Architecture

### System Prompt Engineering

```python
system_prompt = f"""
You're a video subtitle translator. {context} I'll give you content of srt subtitle blocks, including its index. You should translate it into {target_lang}.

Make sure to return in structured JSON array [...]. Ignore timestamps if there are. The output JSON contains a list, where each item in the list is an object that contains two required properties: "index" and "translated_lines". The "index" property is the integer index as provided in the input. The "translated_lines" property is itself a list made up of text strings, one for each line in the translated subtitle block. Break up the lines just like the original blocks for readability. Don't merge two lines of the same blockinto one.
"""
```

**Design Principles**:
- **Context Integration**: Incorporates detected context for better translations
- **Structured Output**: Enforces JSON schema compliance
- **Line Preservation**: Maintains original line breaks and formatting
- **Index Mapping**: Ensures proper block order reconstruction

### Response Schema Definition

```python
response_schema = genai.types.Schema(
    type = genai.types.Type.ARRAY,
    items = genai.types.Schema(
        type = genai.types.Type.OBJECT,
        required = ["index", "translated_lines"],
        properties = {
            "index": genai.types.Schema(type = genai.types.Type.INTEGER),
            "translated_lines": genai.types.Schema(
                type = genai.types.Type.ARRAY,
                items = genai.types.Schema(type = genai.types.Type.STRING),
            ),
        },
    ),
)
```

**Schema Benefits**:
- **Structure Enforcement**: Guarantees consistent AI response format
- **Validation Support**: Enables automatic response validation
- **Error Prevention**: Catches malformed responses early
- **Type Safety**: Ensures correct data types in responses

### Model Configuration Strategy

```python
# Base configuration
config_params = {
    'response_mime_type': 'application/json',
    'response_schema': response_schema,
    'system_instruction': [types.Part.from_text(text=system_prompt)],
}

# Fast mode optimization
if speed_mode == "fast":
    config_params['thinking_config'] = types.ThinkingConfig(thinking_budget=0)

# Dynamic model selection
model_to_use = settings.FAST_MODEL if speed_mode == "fast" else settings.NORMAL_MODEL
```

**Configuration Features**:
- **Mode-Specific Optimization**: Different configurations for fast vs. normal mode
- **Schema Enforcement**: JSON schema validation at AI service level
- **Thinking Budget**: Controls AI reasoning complexity for speed optimization
- **Dynamic Model Selection**: Runtime model selection based on speed requirements

## Concurrency and Rate Limiting

### Semaphore-Based Flow Control

```python
async with semaphore:  # Acquire semaphore lock
    # Translation logic here
```

**Benefits**:
- **Rate Limiting**: Prevents overwhelming AI service with concurrent requests
- **Resource Management**: Controls memory and network resource usage
- **Error Isolation**: Failed requests don't block other concurrent requests
- **Backpressure Handling**: Automatically queues requests when limit reached

### TaskGroup Orchestration

```python
async with asyncio.TaskGroup() as tg:
    for i, chunk in enumerate(sub):
        task = tg.create_task(_translate_single_chunk(...))
        tasks.append(task)
```

**Advantages**:
- **Structured Concurrency**: Clean task lifecycle management
- **Exception Aggregation**: Collects exceptions from all tasks
- **Resource Cleanup**: Automatic cleanup on errors or completion
- **Modern Async Pattern**: Uses latest asyncio best practices

## Error Handling and Recovery

### Exception Hierarchy Integration

The module integrates with the custom exception system:

1. **ChunkTranslationError**: AI response validation and processing errors
2. **Schema Validation**: Pydantic model validation errors
3. **Network Errors**: AI service communication failures
4. **Cancellation**: Proper async cancellation handling

### Recovery Strategies

1. **Retry Logic**: Automatic retry with configurable attempts
2. **Statistics Tracking**: Detailed failure and retry statistics
3. **Graceful Degradation**: Individual chunk failures don't stop overall process
4. **Error Context**: Comprehensive error logging with chunk context

### Performance Monitoring

```python
# Statistics returned by translate_all_chunks
total_failed_attempts, total_chunks_with_failures = await translate_all_chunks(...)

# Calculate success metrics
success_rate = (total_chunks - total_chunks_with_failures) / total_chunks * 100
average_retries = total_failed_attempts / total_chunks
```

**Monitoring Capabilities**:
- **Success Rate Tracking**: Percentage of successfully translated chunks
- **Retry Analysis**: Average retries per chunk
- **Failure Distribution**: Which chunks failed and why
- **Performance Metrics**: Processing time and throughput analysis

This sophisticated chunk translation module provides the core translation engine with enterprise-grade reliability, comprehensive error handling, and detailed performance monitoring, making it suitable for production subtitle translation workflows.