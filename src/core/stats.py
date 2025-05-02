import asyncio
import itertools
from datetime import datetime
from typing import Dict, Optional, Tuple

from pydantic import BaseModel, Field


class FileStats(BaseModel):
    """Statistics for a single file translation request."""

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
    status: str = "processing"  # e.g., "processing", "completed", "failed"


class TotalStats(BaseModel):
    """Aggregated application statistics."""

    total_files_processed: int = 0
    total_blocks_processed: int = 0
    total_chunks_processed: int = 0
    total_translation_failed_attempts: int = 0
    total_chunks_with_failures: int = 0
    app_start_time: datetime = Field(default_factory=datetime.now)


class AppStatsStore:
    """In-memory store for application statistics."""

    def __init__(self):
        self._request_id_counter = itertools.count(1)
        self._file_stats: Dict[str, FileStats] = {}
        self._total_stats: TotalStats = TotalStats()
        self._lock = asyncio.Lock()

    async def create_file_entry(
        self, filename: str, size: int, speed_mode: str
    ) -> str:
        """Creates a new entry for a file translation request."""
        request_id_num = next(self._request_id_counter)
        request_id = f"file_{request_id_num}"

        entry = FileStats(
            request_id=request_id,
            filename=filename,
            file_size_bytes=size,
            speed_mode=speed_mode,
            status="processing",
        )

        async with self._lock:
            self._file_stats[request_id] = entry
            self._total_stats.total_files_processed += 1

        return request_id

    async def update_parsing_stats(
        self, request_id: str, num_chunks: int, total_blocks: int
    ):
        """Updates stats after parsing is complete."""
        async with self._lock:
            if entry := self._file_stats.get(request_id):
                entry.total_chunks = num_chunks
                entry.total_blocks = total_blocks
                self._total_stats.total_chunks_processed += num_chunks
                self._total_stats.total_blocks_processed += total_blocks
            else:
                # Handle error: Request ID not found (optional: log this)
                print(f"Error: Request ID {request_id} not found for parsing stats.")

    async def update_translation_stats(
        self,
        request_id: str,
        total_failed_attempts: int,
        chunks_with_failures: int,
    ):
        """Updates stats after translation attempts."""
        async with self._lock:
            if entry := self._file_stats.get(request_id):
                entry.translation_failed_attempts = total_failed_attempts
                entry.chunks_with_failures = chunks_with_failures
                self._total_stats.total_translation_failed_attempts += (
                    total_failed_attempts
                )
                self._total_stats.total_chunks_with_failures += (
                    chunks_with_failures
                )
            else:
                # Handle error: Request ID not found (optional: log this)
                print(
                    f"Error: Request ID {request_id} not found for translation stats."
                )

    async def complete_request(self, request_id: str, status: str):
        """Marks a request as completed or failed."""
        async with self._lock:
            if entry := self._file_stats.get(request_id):
                entry.end_time = datetime.now()
                entry.status = status
            else:
                # Handle error: Request ID not found (optional: log this)
                print(f"Error: Request ID {request_id} not found for completion.")

    async def get_stats(self) -> Tuple[TotalStats, Dict[str, FileStats]]:
        """Returns a snapshot of the current statistics."""
        async with self._lock:
            # Return copies to prevent external modification
            total_stats_copy = self._total_stats.copy()
            file_stats_copy = self._file_stats.copy()
        return total_stats_copy, file_stats_copy
