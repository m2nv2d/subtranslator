# AI Providers Module

## Overview

The AI providers module implements an abstraction layer for different AI translation services. It provides a unified interface for context detection and subtitle translation while supporting multiple backend providers including Google Gemini and mock implementations.

## Architecture

### Provider Interface

The `AIProvider` abstract base class defines the contract that all providers must implement:

```python
class AIProvider(abc.ABC):
    @abc.abstractmethod
    async def detect_context(self, sub: list[list[SubtitleBlock]], speed_mode: str) -> str:
        """Detect context from subtitle content."""
        pass
    
    @abc.abstractmethod
    async def translate_all_chunks(
        self, context: str, sub: list[list[SubtitleBlock]], 
        target_lang: str, speed_mode: str, semaphore: asyncio.Semaphore
    ) -> Tuple[int, int]:
        """Translate all chunks of subtitle blocks."""
        pass
```

## Supported Providers

### MockProvider

A testing and development provider that simulates AI translation with configurable delays.

**Features:**
- Speed-based random delays (fast: 5-8s, normal: 8-13s)
- Copies original content as "translation"
- No external API dependencies
- Useful for development and testing

**Configuration:**
```bash
AI_PROVIDER=mock
AI_API_KEY=  # Optional for mock provider
```

### GeminiProvider

Production provider that integrates with Google's Gemini AI models.

**Features:**
- Full integration with Google Gemini API
- Support for fast and normal translation modes
- Real AI-powered context detection and translation
- Configurable model selection

**Configuration:**
```bash
AI_PROVIDER=google-gemini
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_FAST_MODEL=gemini-2.5-flash-preview-04-17
GEMINI_NORMAL_MODEL=gemini-2.5-pro-preview-03-25
```

### OpenRouterProvider

Production provider that integrates with OpenRouter's API for accessing various AI models.

**Features:**
- HTTP-based API integration with OpenRouter
- Support for fast and normal translation modes
- Real AI-powered context detection and translation
- Access to multiple AI models through OpenRouter's platform
- Structured JSON responses for translation
- Text responses for context detection

**Configuration:**
```bash
AI_PROVIDER=openrouter
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_FAST_MODEL=google/gemini-2.5-flash
OPENROUTER_NORMAL_MODEL=google/gemini-2.5-pro
```

## Configuration

### Environment Variables

The provider system is configured through environment variables:

```bash
# Provider Selection
AI_PROVIDER=google-gemini  # or "openrouter" or "mock"

# Provider-specific API Configuration
GEMINI_API_KEY=your_gemini_api_key_here         # For Google Gemini
OPENROUTER_API_KEY=your_openrouter_api_key_here # For OpenRouter

# Provider-specific Model Configuration
GEMINI_FAST_MODEL=gemini-2.5-flash-preview-04-17   # For Google Gemini
GEMINI_NORMAL_MODEL=gemini-2.5-pro-preview-03-25   # For Google Gemini
OPENROUTER_FAST_MODEL=google/gemini-2.5-flash      # For OpenRouter
OPENROUTER_NORMAL_MODEL=google/gemini-2.5-pro      # For OpenRouter

# Fallback/Generic Configuration (used if provider-specific keys are not set)
AI_API_KEY=fallback_api_key
FAST_MODEL=fallback_fast_model
NORMAL_MODEL=fallback_normal_model
```

### Validation

The configuration system validates provider settings:

- **AI_PROVIDER**: Must be one of `["google-gemini", "openrouter", "mock"]`
- **API Keys**: 
  - Required for `google-gemini` (GEMINI_API_KEY or AI_API_KEY)
  - Required for `openrouter` (OPENROUTER_API_KEY or AI_API_KEY)
  - Optional for `mock`
- **Models**: 
  - Required for `google-gemini` (provider-specific or generic model fields)
  - Required for `openrouter` (provider-specific or generic model fields)
  - Ignored for `mock`

## Usage

### Provider Factory

The `create_provider()` function instantiates the appropriate provider based on configuration:

```python
def create_provider(settings: Settings) -> AIProvider:
    provider_type = settings.AI_PROVIDER.lower()
    
    if provider_type == "mock":
        return MockProvider(settings)
    elif provider_type == "google-gemini":
        provider = GeminiProvider(settings)
        provider.initialize()
        return provider
    elif provider_type == "openrouter":
        return OpenRouterProvider(settings)
    else:
        raise ValueError(f"Unsupported AI provider: {settings.AI_PROVIDER}")
```

### Dependency Injection

The provider is integrated into FastAPI through dependency injection:

```python
@functools.lru_cache()
def get_ai_provider(settings: Settings = Depends(get_application_settings)) -> AIProvider:
    """Dependency provider for the AI provider."""
    try:
        provider = create_provider(settings)
        logger.info(f"AI provider '{settings.AI_PROVIDER}' initialized successfully.")
        return provider
    except Exception as e:
        logger.error(f"Failed to initialize AI provider: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize AI provider: {str(e)}")
```

### Router Integration

Translation endpoints use the provider through dependency injection:

```python
@router.post("/translate")
async def translate_srt(
    provider: Annotated[AIProvider, Depends(get_ai_provider)],
    # ... other dependencies
):
    # Context detection
    context = await provider.detect_context(subtitle_chunks, speed_mode)
    
    # Translation
    failed_attempts, chunks_with_failures = await provider.translate_all_chunks(
        context=context,
        sub=subtitle_chunks,
        target_lang=target_lang,
        speed_mode=speed_mode,
        semaphore=semaphore,
    )
```

## Implementation Details

### Mock Provider

The MockProvider simulates realistic AI behavior with speed-based delays:

```python
async def detect_context(self, sub: list[list[SubtitleBlock]], speed_mode: str) -> str:
    if speed_mode == "fast":
        delay = random.uniform(5.0, 8.0)
    else:  # normal mode
        delay = random.uniform(8.0, 13.0)
    
    await asyncio.sleep(delay)
    return f"Mock Context Detected ({speed_mode} mode)"
```

### Gemini Provider

The GeminiProvider wraps existing Gemini integration logic:

```python
async def detect_context(self, sub: list[list[SubtitleBlock]], speed_mode: str) -> str:
    from translator.context_detector import detect_context
    return await detect_context(sub, speed_mode, self.client, self.settings)

async def translate_all_chunks(self, context: str, sub: list[list[SubtitleBlock]], 
                             target_lang: str, speed_mode: str, 
                             semaphore: asyncio.Semaphore) -> Tuple[int, int]:
    from translator.chunk_translator import translate_all_chunks
    return await translate_all_chunks(
        context=context, sub=sub, target_lang=target_lang,
        speed_mode=speed_mode, client=self.client, 
        settings=self.settings, semaphore=semaphore,
    )
```

### OpenRouter Provider

The OpenRouterProvider uses HTTP-based API calls without requiring a persistent client:

```python
async def detect_context(self, sub: list[list[SubtitleBlock]], speed_mode: str) -> str:
    from translator.context_detector import detect_context
    return await detect_context(sub, speed_mode, None, self.settings)

async def translate_all_chunks(self, context: str, sub: list[list[SubtitleBlock]], 
                             target_lang: str, speed_mode: str, 
                             semaphore: asyncio.Semaphore) -> Tuple[int, int]:
    from translator.chunk_translator import translate_all_chunks
    return await translate_all_chunks(
        context=context, sub=sub, target_lang=target_lang,
        speed_mode=speed_mode, client=None,  # OpenRouter doesn't use a client
        settings=self.settings, semaphore=semaphore,
    )
```

## Error Handling

### Provider Initialization

Provider initialization errors are handled at the dependency injection level:

```python
try:
    provider = create_provider(settings)
    return provider
except Exception as e:
    raise HTTPException(
        status_code=500,
        detail=f"Server Configuration Error: Failed to initialize AI provider: {str(e)}"
    )
```

### Runtime Errors

Runtime errors are propagated from the underlying translation modules:

- `ContextDetectionError`: Context detection failures
- `ChunkTranslationError`: Translation failures
- Network and API errors from external services

## Speed Mode Integration

The provider system preserves the original speed mode semantics while extending them for mock operations:

- **fast**: Uses fast models/short delays
- **normal**: Uses normal models/longer delays  
- **mock_fast**: Mock mode with fast timing
- **mock_normal**: Mock mode with normal timing

## Testing

Provider functionality can be tested using the mock provider:

```bash
# Enable mock provider
export AI_PROVIDER=mock

# Test with different speed modes
curl -X POST -F "file=@test.srt" -F "target_lang=Vietnamese" -F "speed_mode=fast" \
     http://localhost:8000/translate
```

## Related Components

- **Config Module**: Provides provider configuration and validation
- **Dependencies Module**: Manages provider initialization and dependency injection
- **Translation Router**: Primary consumer of provider services
- **Existing Translation Modules**: Context detector and chunk translator implementations
- **Gemini Helper**: Gemini-specific client initialization and configuration

## Future Extensions

The provider architecture supports easy addition of new AI services:

1. Implement the `AIProvider` interface
2. Add provider type to configuration validation
3. Update the `create_provider()` factory function
4. Add provider-specific configuration options