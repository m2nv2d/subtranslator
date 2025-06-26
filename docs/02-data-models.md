# Data Models

## Overview

The Subtranslator application uses a well-structured data model architecture based on Python dataclasses and Pydantic models. The design emphasizes type safety, validation, and clear separation between core domain objects, API response models, and configuration/monitoring structures.

## Core Domain Models

### SubtitleBlock
**File**: `src/translator/models.py:7`

The fundamental unit representing a single subtitle entry from an SRT file.

```python
@dataclass
class SubtitleBlock:
    index: int
    start: datetime
    end: datetime
    content: str
    translated_content: Optional[str] = None
```

**Fields**:
- `index`: Sequential identifier matching the original SRT block number
- `start`: Subtitle display start time as datetime object
- `end`: Subtitle display end time as datetime object  
- `content`: Original subtitle text content
- `translated_content`: Translated text, populated during processing (initially None)

**Usage Pattern**: This is the central data structure that flows through the entire translation pipeline. Blocks are parsed from SRT files, grouped into chunks for processing, modified in-place during translation, and reassembled into output files.

**Key Behaviors**:
- Immutable timing information preserves synchronization
- In-place translation modification via `translated_content` field
- Used both individually and in collections (chunks)

## API Response Models

### TranslatedBlock
**File**: `src/translator/chunk_translator.py:25`

Pydantic model for validating individual translation responses from the AI service.

```python
class TranslatedBlock(BaseModel):
    index: int
    translated_lines: list[str]
```

**Fields**:
- `index`: Block identifier matching the original SubtitleBlock index
- `translated_lines`: List of translated text lines for multi-line subtitles

**Validation**: Ensures AI responses contain proper block identifiers and non-empty translation arrays.

**Relationship**: Maps back to `SubtitleBlock.translated_content` after validation.

### TranslatedChunk
**File**: `src/translator/chunk_translator.py:30`

Type alias for validating complete chunk translation responses.

```python
TranslatedChunk = RootModel[list[TranslatedBlock]]
```

**Purpose**: Validates that AI service returns translations for all blocks in a chunk, maintaining order and completeness.

**Usage**: Used with Pydantic validation to ensure structured JSON responses from the AI service conform to expected formats.

## Statistics and Monitoring Models

### FileStats
**File**: `src/core/stats.py:7`

Tracks detailed metrics for individual translation requests.

```python
class FileStats(BaseModel):
    request_id: str
    filename: str
    file_size_bytes: int
    speed_mode: str
    total_blocks: int = 0
    total_chunks: int = 0
    translation_failed_attempts: int = 0
    chunks_with_failures: int = 0
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    status: str = "processing"
```

**Lifecycle States**:
- `"processing"`: Active translation in progress
- `"completed"`: Successful translation finished
- `"failed"`: Translation failed with errors

**Key Metrics**:
- Processing time: Calculated from `start_time` to `end_time`
- Failure rates: Failed attempts vs. total processing attempts
- Resource usage: File size and block/chunk counts

### TotalStats
**File**: `src/core/stats.py:24`

Aggregated application-wide statistics and performance metrics.

```python
class TotalStats(BaseModel):
    total_files_processed: int = 0
    total_blocks_processed: int = 0
    total_chunks_processed: int = 0
    total_translation_failed_attempts: int = 0
    total_chunks_with_failures: int = 0
    app_start_time: datetime = Field(default_factory=datetime.now)
```

**Aggregation**: Automatically calculated from individual `FileStats` entries by the `AppStatsStore`.

**Usage**: Provides operational insights into application performance, error rates, and resource utilization over time.

### AppStatsStore
**File**: `src/core/stats.py:35`

Thread-safe in-memory statistics management system.

**Key Features**:
- Unique request ID generation using `itertools.count()`
- Async locks for thread-safe operations
- CRUD operations for file statistics
- Real-time aggregation of total statistics

**Core Methods**:
```python
async def create_file_entry(filename: str, size: int, speed_mode: str) -> str
async def update_parsing_stats(request_id: str, chunks: int, blocks: int)
async def update_translation_stats(request_id: str, failed_attempts: int, chunks_with_failures: int)
async def complete_request(request_id: str, status: str)
async def get_stats() -> tuple[TotalStats, dict[str, FileStats]]
```

## Configuration Models

### Settings
**File**: `src/core/config.py:14`

Comprehensive application configuration using Pydantic BaseSettings.

```python
class Settings(BaseSettings):
    AI_PROVIDER: str = Field(default="google-gemini")
    AI_API_KEY: str = Field(...)
    FAST_MODEL: str = Field(default="gemini-2.5-flash-preview-04-17")
    NORMAL_MODEL: str = Field(default="gemini-2.5-pro-preview-03-25")
    TARGET_LANGUAGES: Annotated[tuple[str, ...], NoDecode] = Field(default=("Vietnamese", "French"))
    CHUNK_MAX_BLOCKS: int = Field(default=100, gt=0)
    RETRY_MAX_ATTEMPTS: int = Field(default=4, ge=0)
    LOG_LEVEL: str = Field(default="INFO")
    MAX_CONCURRENT_TRANSLATIONS: int = Field(default=10, gt=0)
```

**Validation Rules**:
- `TARGET_LANGUAGES`: Custom validator parses comma-separated strings into tuples
- `LOG_LEVEL`: Restricted to valid Python logging levels
- `CHUNK_MAX_BLOCKS`: Must be positive integer for proper chunking
- `MAX_CONCURRENT_TRANSLATIONS`: Controls semaphore limits for concurrency
- `AI_API_KEY`: Required field that must be provided via environment

**Environment Integration**:
- Loads from `.env` files automatically
- Case-sensitive environment variable names
- Frozen configuration (immutable after initialization)

## Error Models

### ErrorDetail
**File**: `src/core/errors.py:6`

Standardized error response format for consistent API error reporting.

```python
class ErrorDetail(BaseModel):
    error: str = Field(..., description="Error message describing what went wrong")
    detail: Optional[str] = Field(None, description="Optional additional error details")
```

**Usage**: Used by `create_error_response()` helper and FastAPI exception handlers to ensure consistent error message formats across all endpoints.

### Custom Exceptions
**File**: `src/translator/exceptions.py`

Domain-specific exception hierarchy for different failure scenarios:

```python
class ConfigError(Exception): pass
class ValidationError(Exception): pass  
class ParsingError(Exception): pass
class ContextDetectionError(Exception): pass
class ChunkTranslationError(Exception): pass
class GenAIClientInitError(Exception): pass
class GenAIRequestError(Exception): pass
class GenAIParsingError(Exception): pass
```

**HTTP Status Mapping**:
- `ValidationError` → 400 (Bad Request)
- `ParsingError` → 422 (Unprocessable Entity)
- `ContextDetectionError` → 500 (Internal Server Error)
- `ChunkTranslationError` → 500 (Internal Server Error)
- Other exceptions → Appropriate status codes based on context

## Data Relationships

### Primary Data Flow
```
SRT File → SubtitleBlock[] → TranslatedChunk → SubtitleBlock[] → SRT File
          (parsing)        (AI validation)   (reassembly)
```

### Statistics Relationships
```
Request → FileStats (1:1) → TotalStats (aggregation)
       ↓
   AppStatsStore (manages all FileStats + TotalStats)
```

### Configuration Relationships
```
Environment Variables → Settings → Dependencies → Components
                     (validation) (injection)   (usage)
```

## Key Design Patterns

### Immutable Configuration
Settings are frozen after validation to prevent runtime modification, ensuring consistent behavior across the application lifecycle.

### In-Place Data Modification
`SubtitleBlock` objects are modified in-place during translation rather than creating new objects, optimizing memory usage for large subtitle files.

### Validation-First Architecture
All external data (file uploads, API responses, configuration) passes through Pydantic validation before entering the application logic.

### Type Safety
Extensive use of Python type hints combined with Pydantic models provides compile-time and runtime type checking.

### Async-Safe Operations
Statistics operations use async locks to ensure thread safety in the concurrent processing environment.

## Field Validation Examples

### Target Languages
```python
# Environment: TARGET_LANGUAGES=Vietnamese,French,Spanish
# Parsed to: ("Vietnamese", "French", "Spanish")

@field_validator("TARGET_LANGUAGES", mode="before")
@classmethod  
def parse_target_languages(cls, v):
    if isinstance(v, str):
        return tuple(lang.strip() for lang in v.split(",") if lang.strip())
    return v
```

### Log Level Validation
```python
@field_validator("LOG_LEVEL")
@classmethod
def validate_log_level(cls, v):
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    if v.upper() not in valid_levels:
        return "INFO"  # Default fallback
    return v.upper()
```

### Model Name Validation
```python
@model_validator(mode="after")
def validate_model_names(self):
    if self.AI_PROVIDER == "google-gemini":
        required_models = [self.FAST_MODEL, self.NORMAL_MODEL]
        for model in required_models:
            if not model.startswith("gemini-"):
                raise ValueError(f"Invalid model name for Google Gemini: {model}")
    return self
```