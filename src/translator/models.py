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
    target_languages: List[str]
    chunk_max_blocks: int
    retry_max_attempts: int
    log_level: str
    ai_provider: str
    ai_api_key: str
    fast_model: str
    normal_model: str