# context_detector.py - AI-Powered Context Detection Module

## Module Overview

**Purpose and responsibilities**: Analyzes subtitle content to detect and describe the general context of the media (movie genre, tutorial topic, vlog theme, etc.). This context information enhances translation quality by providing AI translators with situational awareness.

**Design pattern used**: Strategy pattern with retry decorator and async AI integration. Implements multiple processing modes (mock, fast, normal) with configurable retry mechanisms and robust error handling.

**Integration points**:
- Integrates with AI client from gemini_helper module
- Uses configurable retry logic with application settings
- Provides context information to chunk translation module
- Supports multiple processing modes for different performance/quality tradeoffs

## 🔍 Abstraction-Level Reference

### configurable_retry (Decorator)

**Name and signature**: 
```python
def configurable_retry(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        # Implementation with settings-based retry configuration
```

**Description and purpose**: Decorator that adds configurable retry logic to async functions. Extracts retry configuration from application settings and applies exponential backoff with comprehensive logging.

**Parameters**:
- `f`: The async function to wrap with retry logic

**Returns**: Wrapped async function with retry capabilities

**Behavior**:
- Extracts settings from function arguments (position 3 or 'settings' kwarg)
- Configures retry attempts based on `settings.RETRY_MAX_ATTEMPTS`
- Uses fixed 1-second wait between retries
- Logs retry attempts and failures
- Re-raises final exception if all attempts fail

**Raises**:
- Re-raises the original exception after max attempts exceeded
- Maintains exception chain for debugging

**Example usage**:
```python
@configurable_retry
async def my_ai_function(data, mode, client, settings):
    # Function with automatic retry logic
    result = await ai_client.generate_content(...)
    return result
```

**Tips/Notes**:
- **Configuration Driven**: Retry behavior controlled by settings
- **Argument Extraction**: Automatically finds settings in function arguments
- **Logging Integration**: Comprehensive retry attempt logging
- **Exception Preservation**: Maintains original error context

---

### detect_context

**Name and signature**: 
```python
@configurable_retry
async def detect_context(
    sub: list[list[SubtitleBlock]],
    speed_mode: str,
    genai_client: Optional[genai.client.Client],
    settings: Settings,
) -> str
```

**Description and purpose**: Main context detection function that analyzes subtitle content to determine the general context of the media. Supports multiple processing modes and provides contextual information to improve translation quality.

**Parameters**:
- `sub` (list[list[SubtitleBlock]]): Parsed subtitle data organized in chunks
- `speed_mode` (str): Processing mode - 'mock', 'fast', or 'normal'
- `genai_client` (Optional[genai.client.Client]): Initialized AI client (required for 'fast'/'normal' modes)
- `settings` (Settings): Application configuration including model settings and retry configuration

**Returns**: 
- `str`: A descriptive context string about the media content

**Behavior**:
1. **Mode Selection**: Chooses processing strategy based on speed_mode
2. **Mock Mode**: Returns hardcoded context for testing/development
3. **AI Modes**: Uses first chunk content to analyze context with AI
4. **Prompt Engineering**: Applies specialized system prompt for context detection
5. **Model Selection**: Uses fast or normal model based on speed mode
6. **Error Handling**: Comprehensive error handling with domain-specific exceptions

**Raises**:
- `ContextDetectionError`: Invalid speed_mode or other context detection failures
- `ValueError`: Missing required parameters (genai_client for AI modes)

**Example usage**:
```python
from translator.context_detector import detect_context
from translator.exceptions import ContextDetectionError

try:
    # Parse subtitles first
    chunks = await parse_srt("movie.srt", chunk_max_blocks=10)
    
    # Detect context using normal mode
    context = await detect_context(
        sub=chunks,
        speed_mode="normal",
        genai_client=ai_client,
        settings=app_settings
    )
    
    print(f"Detected context: {context}")
    # Example output: "This is a subtitle for a movie about space exploration and human survival"
    
except ContextDetectionError as e:
    print(f"Context detection failed: {e}")
```

**Tips/Notes**:
- **First Chunk Analysis**: Only analyzes the first chunk for efficiency
- **Prompt Engineering**: Uses carefully crafted prompts for consistent context extraction
- **Model Selection**: Fast mode trades quality for speed, normal mode for best results
- **Mock Mode**: Enables testing without AI service dependencies
- **Retry Integration**: Automatic retry on failures with configurable attempts
- **Content Preparation**: Joins subtitle blocks with newlines for AI analysis

---

## Processing Modes

### Mock Mode (`speed_mode="mock"`)

```python
if speed_mode == "mock":
    logger.debug("Using mock context detection.")
    return "Mock Context Detected"
```

**Use Cases**:
- Development and testing environments
- CI/CD pipelines without AI service access
- Performance testing with predictable responses
- Cost-free context detection for demos

**Benefits**:
- No AI service dependencies
- Instant response time
- Zero API costs
- Predictable behavior

---

### Fast Mode (`speed_mode="fast"`)

```python
model_to_use = settings.FAST_MODEL if speed_mode == "fast" else settings.NORMAL_MODEL
# Uses faster, less accurate model with thinking_budget=0
thinking_config=types.ThinkingConfig(thinking_budget=0)
```

**Use Cases**:
- High-volume processing scenarios
- Cost-sensitive applications
- Real-time or near-real-time processing
- Acceptable quality tradeoffs for speed

**Benefits**:
- Faster response times
- Lower API costs
- Reduced computational overhead
- Good enough quality for many use cases

---

### Normal Mode (`speed_mode="normal"`)

```python
model_to_use = settings.NORMAL_MODEL
# Uses higher quality model without thinking budget restrictions
```

**Use Cases**:
- High-quality translation requirements
- Professional or commercial applications
- Complex content requiring nuanced understanding
- Maximum context detection accuracy

**Benefits**:
- Highest quality context detection
- Better understanding of nuanced content
- More accurate genre/topic identification
- Enhanced translation context

## AI Integration Architecture

### Prompt Engineering Strategy

```python
system_prompt = """You are a context detector. Your task is to analyze the subtitle content provided and determine the general context in one sentence. Only give me that context read to use. If it's a movie, just give a general theme. If a vlog/tutorial, the general topic the speaker(s) are talking about. The template is: This is a subtitle for a movie/vlog/tutorial/... for/of/about ..."""

request_prompt = f"{content}"
```

**Design Principles**:
- **Clear Instructions**: Specific task definition and output format
- **Template Guidance**: Consistent output structure
- **Context Awareness**: Different handling for different media types
- **Concise Output**: Single sentence context description

### AI Client Integration

```python
response = await genai_client.aio.models.generate_content(
    model=model_to_use,
    contents=[
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=request_prompt)],
        )
    ],
    config=types.GenerateContentConfig(
        response_mime_type='text/plain',
        system_instruction=[types.Part.from_text(text=system_prompt)],
        thinking_config=types.ThinkingConfig(thinking_budget=0) # Fast mode only
    )
)
```

**Integration Features**:
- **Async Operations**: Non-blocking AI service calls
- **Model Selection**: Dynamic model choice based on speed mode
- **Configuration Management**: Proper request configuration
- **Response Handling**: Text-based response processing

## Error Handling and Retry Strategy

### Retry Configuration

The module uses the `@configurable_retry` decorator with:
- **Max Attempts**: Controlled by `settings.RETRY_MAX_ATTEMPTS`
- **Wait Strategy**: Fixed 1-second intervals between retries
- **Exception Types**: Retries on any Exception type
- **Logging**: Comprehensive retry attempt logging

### Error Scenarios

1. **Invalid Speed Mode**:
   ```python
   if speed_mode not in ["mock", "fast", "normal"]:
       raise ContextDetectionError(f"Invalid speed_mode: {speed_mode}")
   ```

2. **Missing AI Client**:
   ```python
   if speed_mode in ["fast", "normal"] and genai_client is None:
       # Implicit ValueError from AI client operations
   ```

3. **AI Service Failures**:
   - Network connectivity issues
   - API rate limiting
   - Service authentication problems
   - Model availability issues

### Recovery Strategies

- **Automatic Retry**: Failed requests are automatically retried
- **Mode Fallback**: Applications can fall back to mock mode
- **Error Propagation**: Clear error messages for debugging
- **Graceful Degradation**: Translation can proceed with generic context

## Performance Optimization

### Content Processing Efficiency

```python
content = "\n".join([block.content for block in sub[0]])
```

**Optimizations**:
- **First Chunk Only**: Analyzes only the first chunk for speed
- **Content Joining**: Efficient string concatenation
- **Memory Management**: Minimal memory footprint
- **Batch Processing**: Single AI request per context detection

### Caching Considerations

While not implemented in this module, context detection results are suitable for caching:
- **File-Level Caching**: Same file always produces same context
- **Hash-Based Keys**: Use content hash for cache keys
- **TTL Strategy**: Long-lived cache entries for stable contexts
- **Memory Efficiency**: Context strings are lightweight cache values

## Integration with Translation Pipeline

The context detection module provides essential context information for the translation process:

1. **Context Enrichment**: Provides media context to AI translators
2. **Quality Improvement**: Better translations through situational awareness
3. **Consistency**: Ensures consistent terminology and tone
4. **Performance**: Single context detection serves entire translation job

This sophisticated context detection module enhances the overall translation quality by providing AI translators with crucial situational context, while maintaining flexibility through multiple processing modes and robust error handling.