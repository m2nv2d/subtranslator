from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List

@dataclass
class SubtitleBlock:
    """Represents a single subtitle block from an SRT file."""
    index: int
    start: datetime
    end: datetime
    content: str
    translated_content: Optional[str] = None

@dataclass
class Config:
    """Application configuration settings."""
    gemini_api_key: str
    target_languages: List[str]
    chunk_max_blocks: int
    retry_max_attempts: int
    log_level: str