"""
AI Provider abstraction layer for translation and context detection.

This module defines the provider interface and implementations for different
AI services (Google Gemini, Mock, etc.). Each provider uses its own specific
libraries and API calls.
"""
import abc
import asyncio
import logging
import random
from typing import Any, Optional, Tuple

from translator.models import SubtitleBlock
from translator.exceptions import ChunkTranslationError, ContextDetectionError
from core.config import Settings


logger = logging.getLogger(__name__)


class AIProvider(abc.ABC):
    """Abstract base class for AI providers."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
    
    @abc.abstractmethod
    async def detect_context(
        self,
        sub: list[list[SubtitleBlock]],
        speed_mode: str,
    ) -> str:
        """
        Detect context from subtitle content.
        
        Args:
            sub: Parsed subtitle data, chunked
            speed_mode: Processing mode ('mock', 'fast', 'normal')
            
        Returns:
            Detected context string
            
        Raises:
            ContextDetectionError: If context detection fails
        """
        pass
    
    @abc.abstractmethod
    async def translate_all_chunks(
        self,
        context: str,
        sub: list[list[SubtitleBlock]],
        target_lang: str,
        speed_mode: str,
        semaphore: asyncio.Semaphore,
    ) -> Tuple[int, int]:
        """
        Translate all chunks of subtitle blocks.
        
        Args:
            context: Detected context for translation
            sub: List of subtitle chunks to translate (modified in-place)
            target_lang: Target language for translation
            speed_mode: Processing mode ('mock', 'fast', 'normal')
            semaphore: Semaphore for concurrency control
            
        Returns:
            Tuple of (total_failed_attempts, total_chunks_with_failures)
            
        Raises:
            ChunkTranslationError: If translation fails
        """
        pass


class MockProvider(AIProvider):
    """Mock AI provider that simulates translation with random delays."""
    
    async def detect_context(
        self,
        sub: list[list[SubtitleBlock]],
        speed_mode: str,
    ) -> str:
        """Mock context detection with speed-based random delay."""
        logger.debug(f"Using mock context detection in {speed_mode} mode.")
        
        # Different delays based on speed mode
        if speed_mode == "fast":
            delay = random.uniform(5.0, 8.0)
        else:  # normal mode
            delay = random.uniform(8.0, 13.0)
        
        logger.debug(f"Mock context detection will take {delay:.2f} seconds")
        await asyncio.sleep(delay)
        return f"Mock Context Detected ({speed_mode} mode)"
    
    async def translate_all_chunks(
        self,
        context: str,
        sub: list[list[SubtitleBlock]],
        target_lang: str,
        speed_mode: str,
        semaphore: asyncio.Semaphore,
    ) -> Tuple[int, int]:
        """Mock translation that copies original content with speed-based random delays."""
        # Use the existing mock logic from chunk_translator, but preserve original speed_mode
        from translator.chunk_translator import translate_all_chunks
        
        # For mock provider, we pass None as the client and use mock_{speed_mode} format
        # This allows the chunk_translator to know both that it's mock AND the original speed
        mock_speed_mode = f"mock_{speed_mode}"
        
        return await translate_all_chunks(
            context=context,
            sub=sub,
            target_lang=target_lang,
            speed_mode=mock_speed_mode,
            client=None,
            settings=self.settings,
            semaphore=semaphore,
        )


class GeminiProvider(AIProvider):
    """Google Gemini AI provider implementation."""
    
    def __init__(self, settings: Settings):
        super().__init__(settings)
        self.client = None
    
    def initialize(self) -> None:
        """Initialize the Gemini client using existing helper."""
        from translator.gemini_helper import init_genai_client
        try:
            self.client = init_genai_client(self.settings)
            logger.info("Gemini provider initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise
    
    async def detect_context(
        self,
        sub: list[list[SubtitleBlock]],
        speed_mode: str,
    ) -> str:
        """Detect context using existing Gemini context detector."""
        from translator.context_detector import detect_context
        return await detect_context(sub, speed_mode, self.client, self.settings)
    
    async def translate_all_chunks(
        self,
        context: str,
        sub: list[list[SubtitleBlock]],
        target_lang: str,
        speed_mode: str,
        semaphore: asyncio.Semaphore,
    ) -> Tuple[int, int]:
        """Translate all chunks using existing Gemini translator."""
        from translator.chunk_translator import translate_all_chunks
        
        return await translate_all_chunks(
            context=context,
            sub=sub,
            target_lang=target_lang,
            speed_mode=speed_mode,
            client=self.client,
            settings=self.settings,
            semaphore=semaphore,
        )


def create_provider(settings: Settings) -> AIProvider:
    """
    Factory function to create the appropriate provider based on settings.
    
    Args:
        settings: Application settings
        
    Returns:
        Initialized AI provider instance
        
    Raises:
        ValueError: If provider type is unsupported
    """
    provider_type = settings.AI_PROVIDER.lower()
    
    if provider_type == "mock":
        return MockProvider(settings)
    elif provider_type == "google-gemini":
        provider = GeminiProvider(settings)
        provider.initialize()
        return provider
    else:
        raise ValueError(f"Unsupported AI provider: {settings.AI_PROVIDER}")