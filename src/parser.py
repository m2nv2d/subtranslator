"""Module for parsing and chunking SRT subtitle files."""

import io
import math
import srt
from typing import List
from werkzeug.datastructures import FileStorage

from .exceptions import ParsingError, ValidationError
from .models import SubtitleBlock

MAX_FILE_SIZE_MB = 2
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

def parse_srt(file: FileStorage, max_blocks: int) -> List[List[SubtitleBlock]]:
    """Parses an SRT file, validates it, and chunks the content.

    Args:
        file: The uploaded SRT file (Werkzeug FileStorage object).
        max_blocks: The maximum number of subtitle blocks per chunk.

    Returns:
        A list of lists, where each inner list is a chunk of SubtitleBlock objects.

    Raises:
        ValidationError: If the file fails validation (extension, size).
        ParsingError: If the SRT content is malformed.
    """
    # Input File Validation
    if not file.filename or not file.filename.lower().endswith('.srt'):
        raise ValidationError("Invalid file type. Only .srt files are accepted.")

    # Check file size - FileStorage.content_length might not be reliable
    # Read the file stream to get the actual size if content_length is not set
    file.seek(0, io.SEEK_END)
    file_size = file.tell()
    file.seek(0) # Reset stream position

    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValidationError(f"File size exceeds the limit of {MAX_FILE_SIZE_MB}MB.")

    if file_size == 0:
         raise ValidationError("File is empty.")

    # SRT Content Parsing
    try:
        content = file.read().decode('utf-8', errors='replace') # Read content and decode
        # Use io.StringIO to provide a file-like object to srt.parse
        parsed_subs = list(srt.parse(content))
    except Exception as e:
        # Catching generic Exception as srt library might raise various errors
        raise ParsingError(f"Failed to parse SRT file: {e}") from e

    if not parsed_subs:
        return [] # Return empty list if the SRT file has no subtitles

    # Data Structure Mapping
    subtitle_blocks: List[SubtitleBlock] = []
    for sub in parsed_subs:
        block = SubtitleBlock(
            index=sub.index,
            start=sub.start,
            end=sub.end,
            content=sub.content,
            translated_content=None # Initially None
        )
        subtitle_blocks.append(block)

    # Chunking Logic
    num_chunks = math.ceil(len(subtitle_blocks) / max_blocks)
    chunks = []
    for i in range(num_chunks):
        start_index = i * max_blocks
        end_index = start_index + max_blocks
        chunks.append(subtitle_blocks[start_index:end_index])

    return chunks
