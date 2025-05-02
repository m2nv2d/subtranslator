from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class SubtitleBlock:
    """Represents a single subtitle block from an SRT file."""
    index: int
    start: datetime
    end: datetime
    content: str
    translated_content: Optional[str] = None