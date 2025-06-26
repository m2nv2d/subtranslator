# models.py - Data Models Module

## Module Overview

**Purpose and responsibilities**: Defines the core data structures used throughout the subtitle translation system, providing a clean abstraction for subtitle data with type safety and validation.

**Design pattern used**: Data class pattern with immutable-by-default design, using Python's dataclass decorator for clean, type-safe data structures.

**Integration points**:
- Central data model used by all translator modules
- Integrates with the SRT parsing library for data conversion
- Provides the foundation for chunk-based processing architecture
- Used by the reassembler for output generation

## 🔍 Abstraction-Level Reference

### SubtitleBlock

**Name and signature**: 
```python
@dataclass
class SubtitleBlock:
    index: int
    start: datetime
    end: datetime
    content: str
    translated_content: Optional[str] = None
```

**Description and purpose**: Represents a single subtitle block from an SRT file, containing both the original content and space for translated content. This is the fundamental unit of data processing in the translation pipeline.

**Parameters**:
- `index` (int): The sequential number of the subtitle block in the SRT file
- `start` (datetime): The start timestamp when the subtitle should appear
- `end` (datetime): The end timestamp when the subtitle should disappear
- `content` (str): The original subtitle text content
- `translated_content` (Optional[str]): The translated text content, initially None

**Returns**: SubtitleBlock instance

**Behavior**:
- Immutable by design (dataclass with frozen=False allows modification of translated_content)
- Provides a clean separation between original and translated content
- Maintains temporal information (start/end times) for proper subtitle timing
- Supports both original and translated content in the same structure
- Enables in-place translation updates without losing original data

**Raises**: 
- `TypeError`: If parameters don't match the expected types
- `ValueError`: If datetime objects are invalid

**Example usage**:
```python
from datetime import datetime
from translator.models import SubtitleBlock

# Create a subtitle block from parsed SRT data
block = SubtitleBlock(
    index=1,
    start=datetime(2023, 1, 1, 0, 0, 1, 500000),  # 00:00:01,500
    end=datetime(2023, 1, 1, 0, 0, 4, 200000),    # 00:00:04,200
    content="Hello, world!",
    translated_content=None
)

# Access original content
print(block.content)  # "Hello, world!"

# Update with translation
block.translated_content = "¡Hola, mundo!"

# Check if translation is available
if block.translated_content:
    print(f"Original: {block.content}")
    print(f"Translated: {block.translated_content}")
```

**Tips/Notes**:
- **Design Philosophy**: The model maintains both original and translated content to enable fallback behavior and comparison
- **Memory Efficiency**: Uses Optional[str] for translated_content to avoid memory overhead for untranslated blocks
- **Temporal Integrity**: Preserves exact timing information from the original SRT file
- **Type Safety**: Leverages Python's type hints for better IDE support and runtime validation
- **Chunk Processing**: Designed to work efficiently in lists for chunk-based processing
- **Fallback Strategy**: The reassembler can use original content if translation fails
- **Debugging Support**: Maintains complete original data for troubleshooting translation issues

---

## Data Flow Integration

The `SubtitleBlock` model serves as the central data structure in the translation pipeline:

1. **Parser → SubtitleBlock**: The parser module converts SRT subtitle objects into SubtitleBlock instances
2. **SubtitleBlock → Chunks**: Blocks are organized into chunks for parallel processing
3. **Chunk Translation**: The translated_content field is populated during AI translation
4. **Reassembler**: Uses both original and translated content to generate the final SRT output

## Design Considerations

### Mutability Strategy
The model uses a hybrid approach:
- **Immutable fields**: `index`, `start`, `end`, `content` remain constant
- **Mutable field**: `translated_content` can be updated during processing
- This design prevents accidental modification of source data while allowing translation updates

### Memory Optimization
- Uses `Optional[str]` for `translated_content` to avoid memory allocation until translation occurs
- Maintains references to original data without duplication
- Supports garbage collection of translation data when no longer needed

### Type Safety Benefits
- Enables static type checking with mypy
- Provides IDE auto-completion and error detection
- Documents the expected data structure through type annotations
- Reduces runtime errors through early type validation

### Integration with External Libraries
- **SRT Library**: Seamlessly converts to/from `srt.Subtitle` objects
- **JSON Serialization**: Can be easily serialized for API responses or caching
- **Pydantic Integration**: Compatible with Pydantic models for API validation

## Error Handling Integration

The model integrates with the exception system:
- Type mismatches trigger `TypeError` exceptions
- Invalid datetime values raise `ValueError` exceptions
- Missing required fields are caught at instantiation time
- Provides clear error messages for debugging

This simple but powerful data model forms the foundation for the entire translation system, enabling clean data flow, type safety, and efficient processing throughout the pipeline.