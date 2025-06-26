# Statistics Module (`stats.py`)

## Module Overview

### Purpose and Responsibilities
The `stats.py` module provides comprehensive statistics tracking and monitoring capabilities for the subtranslator application. It tracks file processing metrics, translation performance, error rates, and provides both per-request and aggregate application-wide statistics.

### Design Pattern Used
- **Data Transfer Object (DTO) Pattern**: Uses Pydantic models for structured statistics data
- **Singleton Pattern**: Single AppStatsStore instance shared across the application
- **Observer Pattern**: Tracks events throughout the translation pipeline
- **Thread-Safe Pattern**: Uses asyncio.Lock for concurrent access protection

### Integration Points
- Injected through FastAPI dependency system (`dependencies.py`)
- Tracks metrics from translation pipeline components
- Provides data for monitoring and performance analysis
- Integrates with logging and error reporting systems

## 🔍 Abstraction-Level Reference

### `FileStats` Class

```python
class FileStats(BaseModel)
```

**Description**: Pydantic model that tracks statistics for a single file translation request throughout its lifecycle.

**Fields**:
- `request_id: str` - Unique identifier for the translation request
- `filename: str` - Name of the file being processed
- `file_size_bytes: int` - Size of the file in bytes
- `speed_mode: str` - Translation speed mode ("fast" or "normal")
- `total_blocks: int = 0` - Total number of subtitle blocks in the file
- `total_chunks: int = 0` - Number of chunks the file was divided into
- `translation_failed_attempts: int = 0` - Number of failed translation attempts
- `chunks_with_failures: int = 0` - Number of chunks that experienced failures
- `start_time: datetime` - Timestamp when processing started (auto-set)
- `end_time: Optional[datetime] = None` - Timestamp when processing completed
- `status: str = "processing"` - Current status ("processing", "completed", "failed")

**Behavior**: 
- Immutable data structure for tracking file processing metrics
- Automatic timestamp generation for start_time
- JSON serializable for API responses and logging

**Example Usage**:
```python
file_stats = FileStats(
    request_id="file_123",
    filename="movie_subtitles.srt",
    file_size_bytes=2048,
    speed_mode="fast",
    total_blocks=150,
    total_chunks=2
)

# Access processing time
if file_stats.end_time:
    duration = file_stats.end_time - file_stats.start_time
    print(f"Processing took: {duration.total_seconds()} seconds")
```

**Tips/Notes**:
- All datetime fields use system timezone
- Status field should only contain predefined values
- Used internally by AppStatsStore for tracking

---

### `TotalStats` Class

```python
class TotalStats(BaseModel)
```

**Description**: Pydantic model that maintains aggregate statistics across all translation requests since application startup.

**Fields**:
- `total_files_processed: int = 0` - Total number of files processed
- `total_blocks_processed: int = 0` - Total subtitle blocks processed across all files
- `total_chunks_processed: int = 0` - Total chunks processed across all files
- `total_translation_failed_attempts: int = 0` - Aggregate failed translation attempts
- `total_chunks_with_failures: int = 0` - Total chunks that experienced failures
- `app_start_time: datetime` - Application startup timestamp (auto-set)

**Behavior**: 
- Accumulates metrics from all FileStats instances
- Provides application-wide performance overview
- JSON serializable for monitoring endpoints

**Example Usage**:
```python
# Access through AppStatsStore
total_stats, file_stats = await stats_store.get_stats()

# Calculate application uptime
uptime = datetime.now() - total_stats.app_start_time
print(f"Application uptime: {uptime}")

# Calculate success rate
if total_stats.total_chunks_processed > 0:
    success_rate = 1 - (total_stats.total_chunks_with_failures / total_stats.total_chunks_processed)
    print(f"Translation success rate: {success_rate:.2%}")
```

**Tips/Notes**:
- Metrics are cumulative since application start
- Not reset during application runtime
- Useful for long-term performance monitoring

---

### `AppStatsStore` Class

```python
class AppStatsStore
```

**Description**: Thread-safe in-memory statistics store that manages all application metrics and provides atomic operations for concurrent access.

**Attributes**:
- `_request_id_counter: itertools.count` - Auto-incrementing counter for unique request IDs
- `_file_stats: Dict[str, FileStats]` - Storage for individual file statistics
- `_total_stats: TotalStats` - Aggregate application statistics
- `_lock: asyncio.Lock` - Async lock for thread-safe operations

**Behavior**: 
- Provides atomic operations for statistics updates
- Maintains both individual and aggregate statistics
- Thread-safe for concurrent access
- Generates unique request IDs automatically

---

#### `create_file_entry` Method

```python
async def create_file_entry(self, filename: str, size: int, speed_mode: str) -> str
```

**Description**: Creates a new statistics entry for a file translation request and initializes tracking.

**Parameters**:
- `filename: str` - Name of the file being processed
- `size: int` - File size in bytes
- `speed_mode: str` - Translation mode ("fast" or "normal")

**Returns**: 
- `str` - Unique request ID for tracking this file

**Behavior**: 
- Generates unique request ID using auto-incrementing counter
- Creates FileStats entry with "processing" status
- Increments total files processed counter
- Thread-safe operation using async lock

**Example Usage**:
```python
stats_store = AppStatsStore()

# Start tracking a new file
request_id = await stats_store.create_file_entry(
    filename="movie.srt",
    size=2048,
    speed_mode="fast"
)

print(f"Tracking file with ID: {request_id}")
# Output: "Tracking file with ID: file_1"
```

**Tips/Notes**:
- Must be called before any other statistics operations for a file
- Request ID format: "file_{number}"
- Size should be actual file size in bytes for accurate metrics

---

#### `update_parsing_stats` Method

```python
async def update_parsing_stats(self, request_id: str, num_chunks: int, total_blocks: int)
```

**Description**: Updates statistics after subtitle file parsing is complete with chunk and block counts.

**Parameters**:
- `request_id: str` - Request ID returned from create_file_entry
- `num_chunks: int` - Number of chunks the file was divided into
- `total_blocks: int` - Total number of subtitle blocks in the file

**Behavior**: 
- Updates FileStats entry with parsing results
- Increments aggregate chunk and block counters
- Prints error message if request ID not found
- Thread-safe operation using async lock

**Example Usage**:
```python
# After parsing subtitle file
await stats_store.update_parsing_stats(
    request_id="file_1",
    num_chunks=3,
    total_blocks=245
)

# Check updated stats
total_stats, file_stats = await stats_store.get_stats()
print(f"Total blocks processed: {total_stats.total_blocks_processed}")
```

**Tips/Notes**:
- Should be called after subtitle parsing but before translation
- Invalid request IDs are handled gracefully with error logging
- Chunk count affects concurrency planning

---

#### `update_translation_stats` Method

```python
async def update_translation_stats(self, request_id: str, total_failed_attempts: int, chunks_with_failures: int)
```

**Description**: Updates statistics with translation attempt results including failure counts and retry information.

**Parameters**:
- `request_id: str` - Request ID for the file being processed
- `total_failed_attempts: int` - Total number of failed translation attempts across all chunks
- `chunks_with_failures: int` - Number of chunks that experienced at least one failure

**Behavior**: 
- Updates FileStats with failure metrics
- Increments aggregate failure counters
- Provides data for success rate calculations
- Thread-safe operation using async lock

**Example Usage**:
```python
# After translation attempts (including retries)
await stats_store.update_translation_stats(
    request_id="file_1", 
    total_failed_attempts=2,  # Some chunks required retries
    chunks_with_failures=1    # Only 1 chunk had issues
)

# Calculate success metrics
total_stats, file_stats = await stats_store.get_stats()
file_stat = file_stats["file_1"]

success_rate = 1 - (file_stat.chunks_with_failures / file_stat.total_chunks)
print(f"File success rate: {success_rate:.2%}")
```

**Tips/Notes**:
- Called after all translation attempts are complete
- Helps identify problematic files or chunks
- Useful for optimizing retry strategies

---

#### `complete_request` Method

```python
async def complete_request(self, request_id: str, status: str)
```

**Description**: Marks a translation request as completed or failed and records the completion timestamp.

**Parameters**:
- `request_id: str` - Request ID for the file being processed
- `status: str` - Final status ("completed" or "failed")

**Behavior**: 
- Sets end_time to current timestamp
- Updates status field with final result
- Enables processing time calculations
- Thread-safe operation using async lock

**Example Usage**:
```python
try:
    # Perform translation
    result = await translate_file(file_content)
    
    # Mark as successful
    await stats_store.complete_request(request_id, "completed")
    return result
    
except Exception as e:
    # Mark as failed
    await stats_store.complete_request(request_id, "failed")
    raise
```

**Tips/Notes**:
- Should always be called to properly close request tracking
- Status should be either "completed" or "failed"
- Enables accurate processing time metrics

---

#### `get_stats` Method

```python
async def get_stats(self) -> Tuple[TotalStats, Dict[str, FileStats]]
```

**Description**: Returns a snapshot of current application statistics including both aggregate and per-file data.

**Returns**: 
- `Tuple[TotalStats, Dict[str, FileStats]]` - Aggregate stats and dictionary of file stats

**Behavior**: 
- Creates copies of internal data structures
- Prevents external modification of statistics
- Provides thread-safe read access
- Includes all historical data since application start

**Example Usage**:
```python
# Get current statistics
total_stats, file_stats = await stats_store.get_stats()

# Display aggregate metrics
print(f"Files processed: {total_stats.total_files_processed}")
print(f"Total blocks: {total_stats.total_blocks_processed}")
print(f"Success rate: {1 - (total_stats.total_chunks_with_failures / total_stats.total_chunks_processed):.2%}")

# Display recent file stats
for request_id, file_stat in list(file_stats.items())[-5:]:
    duration = None
    if file_stat.end_time:
        duration = (file_stat.end_time - file_stat.start_time).total_seconds()
    
    print(f"{file_stat.filename}: {file_stat.status} ({duration}s)")
```

**Tips/Notes**:
- Returns copies to prevent accidental modification
- Safe to call frequently for monitoring
- File stats dictionary includes all tracked files

## Usage Patterns

### Complete File Processing Workflow

```python
from core.dependencies import get_stats_store
from fastapi import Depends

@app.post("/translate")
async def translate_file(
    file: UploadFile,
    stats: AppStatsStore = Depends(get_stats_store)
):
    # Step 1: Initialize tracking
    request_id = await stats.create_file_entry(
        filename=file.filename,
        size=file.size or 0,
        speed_mode="normal"
    )
    
    try:
        # Step 2: Parse file
        parsed_content = await parse_subtitle_file(file)
        
        # Step 3: Update parsing stats
        await stats.update_parsing_stats(
            request_id=request_id,
            num_chunks=len(parsed_content.chunks),
            total_blocks=parsed_content.total_blocks
        )
        
        # Step 4: Perform translation with retry tracking
        translation_result = await translate_with_retries(parsed_content)
        
        # Step 5: Update translation stats
        await stats.update_translation_stats(
            request_id=request_id,
            total_failed_attempts=translation_result.failed_attempts,
            chunks_with_failures=translation_result.chunks_with_failures
        )
        
        # Step 6: Mark as completed
        await stats.complete_request(request_id, "completed")
        
        return translation_result.content
        
    except Exception as e:
        # Mark as failed on any error
        await stats.complete_request(request_id, "failed")
        raise HTTPException(500, f"Translation failed: {str(e)}")
```

### Statistics Monitoring Endpoint

```python
@app.get("/stats")
async def get_application_stats(
    stats: AppStatsStore = Depends(get_stats_store)
):
    total_stats, file_stats = await stats.get_stats()
    
    # Calculate derived metrics
    uptime = datetime.now() - total_stats.app_start_time
    
    success_rate = 0.0
    if total_stats.total_chunks_processed > 0:
        success_rate = 1 - (total_stats.total_chunks_with_failures / total_stats.total_chunks_processed)
    
    # Get recent files (last 10)
    recent_files = [
        {
            "filename": fs.filename,
            "status": fs.status,
            "duration": (fs.end_time - fs.start_time).total_seconds() if fs.end_time else None,
            "blocks": fs.total_blocks,
            "chunks": fs.total_chunks
        }
        for fs in list(file_stats.values())[-10:]
    ]
    
    return {
        "uptime_seconds": uptime.total_seconds(),
        "total_files": total_stats.total_files_processed,
        "total_blocks": total_stats.total_blocks_processed,
        "total_chunks": total_stats.total_chunks_processed,
        "success_rate": success_rate,
        "failed_attempts": total_stats.total_translation_failed_attempts,
        "recent_files": recent_files
    }
```

### Performance Analysis

```python
async def analyze_performance(stats: AppStatsStore):
    """Analyze translation performance metrics."""
    total_stats, file_stats = await stats.get_stats()
    
    # Processing time analysis
    completed_files = [fs for fs in file_stats.values() if fs.end_time]
    if completed_files:
        processing_times = [
            (fs.end_time - fs.start_time).total_seconds() 
            for fs in completed_files
        ]
        
        avg_processing_time = sum(processing_times) / len(processing_times)
        print(f"Average processing time: {avg_processing_time:.2f} seconds")
    
    # Error rate analysis
    if total_stats.total_chunks_processed > 0:
        error_rate = total_stats.total_chunks_with_failures / total_stats.total_chunks_processed
        print(f"Error rate: {error_rate:.2%}")
    
    # Throughput analysis
    uptime_hours = (datetime.now() - total_stats.app_start_time).total_seconds() / 3600
    if uptime_hours > 0:
        files_per_hour = total_stats.total_files_processed / uptime_hours
        blocks_per_hour = total_stats.total_blocks_processed / uptime_hours
        print(f"Throughput: {files_per_hour:.1f} files/hour, {blocks_per_hour:.0f} blocks/hour")
```

## Thread Safety

The AppStatsStore class is designed for concurrent access:

- **AsyncIO Lock**: All state-modifying operations use `async with self._lock`
- **Atomic Operations**: Each public method is an atomic operation
- **Copy Safety**: `get_stats()` returns copies to prevent external modification
- **Exception Safety**: Lock is properly released even if operations fail

## Monitoring and Alerting

Statistics can be used for:
- **Performance Monitoring**: Track processing times and throughput
- **Error Rate Monitoring**: Identify translation quality issues
- **Capacity Planning**: Monitor concurrent request patterns
- **SLA Compliance**: Track completion rates and response times

The data structure supports integration with monitoring systems like Prometheus, Grafana, or custom dashboards.