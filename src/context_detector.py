import logging
from typing import List, Optional
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from google import genai
from .gemini_helper import FAST_MODEL, NORMAL_MODEL

from .exceptions import ContextDetectionError
from .models import Config, SubtitleBlock

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3), # Default, will be overridden by config if available
    wait=wait_fixed(1),
    retry=retry_if_exception_type(Exception), # Broadly retry on exceptions for now
    reraise=True
)

def detect_context(
    sub: List[List[SubtitleBlock]],
    speed_mode: str,
    genai_client: Optional[genai.client.Client],
    config: Config,
) -> str:
    """Analyzes initial subtitle content to detect the general context.

    Args:
        sub: Parsed subtitle data, chunked.
        speed_mode: Processing mode ('mock', 'fast', 'normal').
        genai_client: Initialized GenAI client (required for 'fast'/'normal').
        config: Application configuration.

    Returns:
        A string representing the detected context.

    Raises:
        ContextDetectionError: If context detection fails.
        ValueError: If speed_mode is invalid or genai_client is missing when required.
    """
    logger.info(f"Starting context detection in '{speed_mode}' mode.")

    if speed_mode == "mock":
        logger.debug("Using mock context detection.")
        # Return a hardcoded context for mock mode
        return "Mock Context Detected"

    elif speed_mode in ["fast", "normal"]:
        # Prepare prompt for GenAI
        content = "\n".join([block.content for block in sub[0]])
        system_prompt = "You are a context detector. Your task is to analyze the subtitle content provided and determine the general context in one sentence. Only give me that context read to use. If it's a movie, just give a general theme. If a vlog/tutorial, the general topic the speaker(s) are talking about. The template is: This is a subtitle for a movie/vlog/tutorial/... for/of/about ..."
        request_prompt = f"{content}"

        # Call GenAI
        if speed_mode == "fast":
            detected_context = genai_client.models.generate_content(
                model=FAST_MODEL,
                contents=[system_prompt, request_prompt]
            ).text
        else:
            detected_context = genai_client.models.generate_content(
                model=NORMAL_MODEL,
                contents=[system_prompt, request_prompt]
            ).text
        return detected_context

    else:
        logger.error(f"Invalid speed_mode: {speed_mode}")
        raise ValueError(f"Invalid speed_mode: {speed_mode}. Must be 'mock', 'fast', or 'normal'.")
