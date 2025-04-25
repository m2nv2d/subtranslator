from typing import List
from datetime import datetime, timedelta
from srt import Subtitle, compose

from models import SubtitleBlock

def reassemble_srt(sub_chunks: List[List[SubtitleBlock]]) -> bytes:
    """Reassembles translated subtitle chunks into a complete SRT file content.

    Args:
        sub_chunks: A list of lists, where each inner list contains
                    SubtitleBlock objects representing a chunk.

    Returns:
        A bytes object containing the full SRT file content, encoded in UTF-8.
    """
    srt_content = []

    for chunk in sub_chunks:
        for block in chunk:
            if not isinstance(block, SubtitleBlock):
                # Skip if the item is not a valid SubtitleBlock
                continue

            # Choose content: translated or original as fallback
            content = block.translated_content if block.translated_content else block.content
            if content is None:
                content = "" # Ensure content is never None

            # Append the block to the SRT content
            srt_content.append(Subtitle(index=block.index, start=block.start, end=block.end, content=content))

    # Join all blocks with exactly one blank line
    full_srt_string = compose(srt_content)

    # Encode the final string to bytes using UTF-8
    return full_srt_string.encode('utf-8')