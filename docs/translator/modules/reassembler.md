# reassembler.py - SRT File Reassembly Module

## Module Overview

**Purpose and responsibilities**: Reconstructs translated subtitle chunks into a complete, properly formatted SRT file. Handles content selection (translated vs. original), maintains temporal integrity, and produces UTF-8 encoded output suitable for media players and subtitle software.

**Design pattern used**: Builder pattern with data transformation pipeline. Implements a straightforward reconstruction process with fallback mechanisms and robust content handling.

**Integration points**:
- Final stage of the translation pipeline
- Consumes SubtitleBlock data from chunk translation
- Integrates with the SRT library for proper formatting
- Produces downloadable content for API responses
- Handles both successful and partially failed translations gracefully

## 🔍 Abstraction-Level Reference

### reassemble_srt

**Name and signature**: 
```python
def reassemble_srt(sub_chunks: list[list[SubtitleBlock]]) -> bytes
```

**Description and purpose**: Main reassembly function that reconstructs translated subtitle chunks into a complete SRT file. Handles content selection, format conversion, and encoding to produce a ready-to-use subtitle file.

**Parameters**:
- `sub_chunks` (list[list[SubtitleBlock]]): A list of chunks, where each chunk contains a list of SubtitleBlock objects with original and potentially translated content

**Returns**: 
- `bytes`: Complete SRT file content encoded in UTF-8, ready for file download or saving

**Behavior**:
1. **Content Selection**: Chooses translated content when available, falls back to original content
2. **Data Validation**: Handles invalid or malformed SubtitleBlock objects gracefully
3. **Format Conversion**: Converts SubtitleBlock objects to SRT library format
4. **Content Assembly**: Reconstructs the complete SRT file with proper formatting
5. **Encoding**: Produces UTF-8 encoded bytes for universal compatibility
6. **Fallback Strategy**: Ensures every subtitle has content (translated or original)

**Raises**:
- Generally does not raise exceptions, implements defensive programming with fallbacks
- May raise encoding errors in extreme edge cases (highly unlikely with UTF-8)

**Example usage**:
```python
from translator.reassembler import reassemble_srt

# After translation processing
translated_chunks = [
    [
        SubtitleBlock(index=1, start=..., end=..., content="Hello", translated_content="Hola"),
        SubtitleBlock(index=2, start=..., end=..., content="World", translated_content="Mundo"),
    ],
    [
        SubtitleBlock(index=3, start=..., end=..., content="Goodbye", translated_content=None),  # Failed translation
    ]
]

# Reassemble into SRT file
srt_bytes = reassemble_srt(translated_chunks)

# Save to file
with open("translated.srt", "wb") as f:
    f.write(srt_bytes)

# Or serve via HTTP response
return Response(
    content=srt_bytes,
    media_type="application/x-subrip",
    headers={"Content-Disposition": "attachment; filename=translated.srt"}
)
```

**Tips/Notes**:
- **Fallback Strategy**: Always produces valid SRT output even with partial translation failures
- **Content Priority**: Prefers translated content but gracefully handles missing translations
- **Encoding Safety**: UTF-8 encoding ensures broad compatibility across platforms
- **Memory Efficiency**: Processes chunks sequentially to minimize memory usage
- **Format Compliance**: Uses the SRT library to ensure proper subtitle format compliance
- **Defensive Programming**: Validates data types and handles edge cases gracefully

---

## Content Selection Strategy

### Translation Priority Logic

```python
# Choose content: translated or original as fallback
content = block.translated_content if block.translated_content else block.content
if content is None:
    content = ""  # Ensure content is never None
```

**Selection Rules**:
1. **Primary**: Use `translated_content` if available and not empty
2. **Fallback**: Use original `content` if translation is missing
3. **Safety**: Use empty string if both are None (defensive programming)

**Benefits**:
- **Graceful Degradation**: Partial translation failures don't break the entire file
- **Mixed Content**: Supports files with some successful and some failed translations
- **User Experience**: Users get a complete file with maximum available translations
- **Error Resilience**: Handles unexpected data states without crashing

### Content Validation

```python
if not isinstance(block, SubtitleBlock):
    # Skip if the item is not a valid SubtitleBlock
    continue
```

**Validation Features**:
- **Type Safety**: Ensures only valid SubtitleBlock objects are processed
- **Error Recovery**: Skips invalid objects rather than failing completely
- **Data Integrity**: Prevents processing of corrupted or unexpected data
- **Robustness**: Handles edge cases in chunk processing gracefully

## SRT Format Integration

### Library Integration

```python
from srt import Subtitle, compose

# Convert to SRT library format
srt_content.append(Subtitle(
    index=block.index,
    start=block.start,
    end=block.end,
    content=content
))

# Generate properly formatted SRT content
full_srt_string = compose(srt_content)
```

**Integration Benefits**:
- **Format Compliance**: Ensures output follows SRT standard exactly
- **Timing Preservation**: Maintains precise subtitle timing from original file
- **Index Integrity**: Preserves original subtitle numbering and sequence
- **Standards Adherence**: Uses industry-standard library for format generation

### Temporal Data Handling

The reassembler preserves critical temporal information:

- **Start Times**: Exact moment when subtitle should appear
- **End Times**: Precise moment when subtitle should disappear  
- **Duration**: Implicit subtitle display duration maintained
- **Sequence**: Original subtitle order preserved through index values

**Temporal Integrity Benefits**:
- **Synchronization**: Translated subtitles remain synchronized with video
- **User Experience**: Viewers see subtitles at correct times
- **Professional Quality**: Output matches commercial subtitle standards
- **Compatibility**: Works with all standard media players and subtitle software

## Output Generation Process

### Assembly Pipeline

1. **Chunk Iteration**: Process each chunk in sequence
   ```python
   for chunk in sub_chunks:
   ```

2. **Block Processing**: Handle each subtitle block individually
   ```python
   for block in chunk:
   ```

3. **Content Selection**: Choose best available content
   ```python
   content = block.translated_content if block.translated_content else block.content
   ```

4. **Format Conversion**: Convert to SRT library objects
   ```python
   srt_content.append(Subtitle(...))
   ```

5. **Final Assembly**: Generate complete SRT string
   ```python
   full_srt_string = compose(srt_content)
   ```

6. **Encoding**: Convert to UTF-8 bytes
   ```python
   return full_srt_string.encode('utf-8')
   ```

### Memory Management

The reassembler uses efficient memory management:

- **Sequential Processing**: Processes chunks one at a time
- **Minimal Buffering**: Only holds SRT objects in memory, not duplicate text
- **Streaming Assembly**: Builds output progressively rather than loading everything
- **Garbage Collection**: Python's GC handles cleanup of intermediate objects

## Error Handling Philosophy

### Defensive Programming Approach

The reassembler uses defensive programming principles:

1. **Type Checking**: Validates object types before processing
2. **Null Safety**: Handles None values gracefully
3. **Fallback Content**: Always provides some content for each subtitle
4. **Continue on Error**: Skips invalid items rather than failing completely
5. **Safe Defaults**: Uses safe default values when data is unexpected

### Robustness Features

```python
# Robust content selection
content = block.translated_content if block.translated_content else block.content
if content is None:
    content = ""  # Ensure content is never None

# Type validation
if not isinstance(block, SubtitleBlock):
    continue  # Skip invalid objects
```

**Robustness Benefits**:
- **Fault Tolerance**: Handles unexpected data gracefully
- **Partial Success**: Produces output even with some data corruption
- **User Experience**: Users get usable results even with processing errors
- **Debugging Support**: Invalid data is skipped but doesn't crash the system

## Integration with Translation Pipeline

### Pipeline Position

The reassembler serves as the final stage in the translation pipeline:

1. **Input**: Receives fully processed chunks from chunk translator
2. **Processing**: Handles content selection and format conversion
3. **Output**: Produces downloadable SRT file content

### Data Flow

```
Translation Pipeline:
Parser → Context Detector → Chunk Translator → Reassembler
  ↓           ↓               ↓                ↓
SubtitleBlocks → Context → Translated Chunks → SRT Bytes
```

### Quality Assurance

The reassembler provides several quality assurance features:

- **Content Integrity**: Ensures no subtitles are lost or corrupted
- **Timing Preservation**: Maintains exact timing from original file
- **Format Compliance**: Produces standards-compliant SRT output
- **Encoding Safety**: UTF-8 encoding prevents character issues
- **Fallback Quality**: Even failed translations produce usable output

## Performance Characteristics

### Efficiency Metrics

- **Time Complexity**: O(n) where n is the total number of subtitle blocks
- **Space Complexity**: O(n) for the output SRT content list
- **Memory Usage**: Minimal overhead beyond the final output
- **Processing Speed**: Very fast - mostly string operations and object creation

### Scalability

- **Large Files**: Handles large subtitle files efficiently
- **Memory Scalability**: Memory usage scales linearly with file size
- **Processing Speed**: Fast enough for real-time web applications
- **Resource Requirements**: Minimal CPU and memory requirements

This elegant reassembler module provides the crucial final step in the translation pipeline, ensuring that translated subtitles are properly formatted, encoded, and ready for use while gracefully handling any translation failures that may have occurred during processing.