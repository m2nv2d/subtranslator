# parser.py - SRT File Parser Module

## Module Overview

**Purpose and responsibilities**: Handles the parsing, validation, and chunking of SRT subtitle files. Acts as the entry point for subtitle data into the translation pipeline, ensuring data integrity and preparing content for parallel processing.

**Design pattern used**: Async I/O pattern with comprehensive validation pipeline. Implements fail-fast validation with detailed error reporting and streaming file processing for memory efficiency.

**Integration points**:
- Entry point for the translation pipeline
- Integrates with the file upload system in routers
- Produces chunked SubtitleBlock data for the translation modules
- Uses custom exceptions for error propagation
- Configurable chunking for parallel processing optimization

## 🔍 Abstraction-Level Reference

### Constants

**MAX_FILE_SIZE_MB**: `2`
**MAX_FILE_SIZE_BYTES**: `2 * 1024 * 1024`

**Description**: File size limits to prevent memory exhaustion and ensure reasonable processing times.

---

### parse_srt

**Name and signature**: 
```python
async def parse_srt(file_path: str, chunk_max_blocks: int) -> list[list[SubtitleBlock]]
```

**Description and purpose**: Comprehensive SRT file parser that validates, parses, and chunks subtitle content for translation processing. Handles the complete pipeline from file validation to structured data output.

**Parameters**:
- `file_path` (str): Absolute path to the SRT file to be parsed
- `chunk_max_blocks` (int): Maximum number of subtitle blocks per chunk for parallel processing

**Returns**: 
- `list[list[SubtitleBlock]]`: A list of chunks, where each chunk is a list of SubtitleBlock objects. Returns empty list for files with no subtitles.

**Behavior**:
1. **File Validation**: Checks file extension, accessibility, size limits, and content
2. **Content Parsing**: Uses the `srt` library to parse subtitle format with error handling
3. **Data Transformation**: Converts SRT subtitle objects to SubtitleBlock instances
4. **Chunking**: Organizes blocks into chunks for parallel processing
5. **Memory Management**: Uses async file I/O and streaming for large files
6. **Error Handling**: Provides detailed error context for debugging

**Raises**:
- `ValidationError`: File validation failures (extension, size, accessibility)
- `ParsingError`: SRT parsing failures or file access issues

**Example usage**:
```python
from translator.parser import parse_srt
from translator.exceptions import ValidationError, ParsingError

try:
    # Parse an SRT file with chunks of 10 blocks each
    chunks = await parse_srt("/path/to/subtitle.srt", chunk_max_blocks=10)
    
    print(f"Parsed {len(chunks)} chunks")
    for i, chunk in enumerate(chunks):
        print(f"Chunk {i}: {len(chunk)} subtitle blocks")
        for block in chunk:
            print(f"  Block {block.index}: {block.content[:50]}...")
            
except ValidationError as e:
    print(f"File validation failed: {e}")
except ParsingError as e:
    print(f"Parsing failed: {e}")
```

**Tips/Notes**:
- **Performance**: Uses async I/O for non-blocking file operations
- **Memory Safety**: Streams file content to avoid loading large files entirely into memory
- **Chunking Strategy**: Chunk size affects parallel processing performance and memory usage
- **Error Recovery**: Uses `errors='replace'` for encoding issues to prevent total failure
- **Empty File Handling**: Returns empty list rather than raising an exception for empty subtitle files
- **Validation Order**: Validates file properties before attempting to read content for efficiency
- **Thread Safety**: Async design allows concurrent parsing of multiple files

---

## Validation Pipeline

The parser implements a comprehensive validation pipeline:

### 1. File Type Validation
```python
if not file_path or not file_path.lower().endswith('.srt'):
    raise ValidationError("Invalid file type. Only .srt files are accepted.")
```
- Checks for valid file extension
- Case-insensitive validation
- Prevents processing of non-subtitle files

### 2. File Accessibility Check
```python
try:
    stat_result = await aiofiles.os.stat(file_path)
    file_size = stat_result.st_size
except OSError as e:
    raise ValidationError(f"Could not access file: {e}")
```
- Verifies file exists and is accessible
- Gets file metadata for further validation
- Handles permission and path issues

### 3. File Size Validation
```python
if file_size > MAX_FILE_SIZE_BYTES:
    raise ValidationError(f"File size exceeds the limit of {MAX_FILE_SIZE_MB}MB.")

if file_size == 0:
    raise ValidationError("File is empty.")
```
- Prevents memory exhaustion from oversized files
- Handles empty file edge case
- Provides clear feedback about size limits

### 4. Content Parsing Validation
```python
try:
    async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        content = await f.read()
    parsed_subs = list(srt.parse(content))
except Exception as e:
    raise ParsingError(f"Failed to parse SRT file '{file_path}': {e}") from e
```
- Uses robust encoding handling with fallback
- Wraps parsing library exceptions with domain context
- Preserves original error information for debugging

## Chunking Algorithm

The parser implements an efficient chunking algorithm:

```python
num_chunks = math.ceil(len(subtitle_blocks) / chunk_max_blocks)
chunks = []
for i in range(num_chunks):
    start_index = i * chunk_max_blocks
    end_index = start_index + chunk_max_blocks
    chunks.append(subtitle_blocks[start_index:end_index])
```

### Chunking Benefits:
- **Parallel Processing**: Enables concurrent translation of subtitle segments
- **Memory Management**: Limits memory usage per processing unit
- **Error Isolation**: Failures in one chunk don't affect others
- **Progress Tracking**: Allows fine-grained progress reporting
- **Retry Granularity**: Failed chunks can be retried individually

### Chunking Considerations:
- **Optimal Chunk Size**: Balance between parallelism and overhead
- **Context Preservation**: Each chunk maintains sequential subtitle blocks
- **Load Balancing**: Chunks may have different processing times based on content
- **Memory Usage**: Smaller chunks reduce peak memory usage

## Data Transformation Process

The parser transforms external SRT data into internal domain models:

```python
for sub in parsed_subs:
    block = SubtitleBlock(
        index=sub.index,
        start=sub.start,
        end=sub.end,
        content=sub.content,
        translated_content=None
    )
    subtitle_blocks.append(block)
```

### Transformation Benefits:
- **Type Safety**: Converts to strongly-typed internal models
- **Data Consistency**: Ensures all blocks follow the same structure
- **Translation Ready**: Initializes translated_content field for later processing
- **Temporal Preservation**: Maintains exact timing information
- **Content Integrity**: Preserves original text without modification

## Error Handling Strategy

The parser uses a layered error handling approach:

1. **Validation Errors**: User-correctable issues (file type, size)
2. **Parsing Errors**: System or data format issues
3. **Context Preservation**: Uses `from e` to maintain error chain
4. **Detailed Messages**: Includes file path and specific failure reason
5. **Recovery Options**: Provides clear guidance for error resolution

This comprehensive parsing module serves as the robust foundation for the subtitle translation pipeline, ensuring data quality and preparing content for efficient parallel processing.