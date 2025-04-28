import logging
import asyncio
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from functools import wraps

from google import genai

from translator.exceptions import ContextDetectionError
from translator.models import SubtitleBlock
from core.config import Settings

logger = logging.getLogger(__name__)

def configurable_retry(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        # Extract settings from the function arguments
        settings = kwargs.get('settings') or args[3]
        
        @retry(
            stop=stop_after_attempt(settings.RETRY_MAX_ATTEMPTS),
            wait=wait_fixed(1),
            retry=retry_if_exception_type(Exception),
            reraise=True
        )
        async def wrapped_f(*args, **kwargs):
            return await f(*args, **kwargs)
        
        return await wrapped_f(*args, **kwargs)
    return wrapper

@configurable_retry
async def detect_context(
    sub: List[List[SubtitleBlock]],
    speed_mode: str,
    genai_client: Optional[genai.client.Client],
    settings: Settings,
) -> str:
    """Analyzes initial subtitle content to detect the general context.

    Args:
        sub: Parsed subtitle data, chunked.
        speed_mode: Processing mode ('mock', 'fast', 'normal').
        genai_client: Initialized GenAI client (required for 'fast'/'normal').
        settings: Application settings.

    Returns:
        A string representing the detected context.

    Raises:
        ContextDetectionError: If context detection fails.
        ValueError: If speed_mode is invalid or genai_client is missing when required.
    """

    if speed_mode == "mock":
        logger.debug("Using mock context detection.")
        # Return a hardcoded context for mock mode
        return "Mock Context Detected"

    elif speed_mode in ["fast", "normal"]:
        # Prepare prompt for GenAI
        content = "\n".join([block.content for block in sub[0]])
        system_prompt = "You are a context detector. Your task is to analyze the subtitle content provided and determine the general context in one sentence. Only give me that context read to use. If it's a movie, just give a general theme. If a vlog/tutorial, the general topic the speaker(s) are talking about. The template is: This is a subtitle for a movie/vlog/tutorial/... for/of/about ..."
        request_prompt = f"{content}"

        # Call GenAI using async API
        model = settings.FAST_MODEL if speed_mode == "fast" else settings.NORMAL_MODEL
        response = await genai_client.aio.models.generate_content(
                model=model,
                contents=[system_prompt, request_prompt]
        )
        return response.text

    else:
        logger.error(f"Invalid speed_mode: {speed_mode}")
        raise ContextDetectionError(f"Invalid speed_mode: {speed_mode}. Must be 'mock', 'fast', or 'normal'.")
