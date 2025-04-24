# src/context_detector.py

import logging
from typing import List, Optional

from google import genai
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

from .exceptions import ContextDetectionError
from .models import Config, SubtitleBlock

logger = logging.getLogger(__name__)


@retry(
    stop=stop_after_attempt(3), # Default, will be overridden by config if available
    wait=wait_fixed(1),
    retry=retry_if_exception_type(Exception), # Broadly retry on exceptions for now
    reraise=True
)
def _call_genai_context_detection(prompt: str, genai_client: genai.client.Client) -> str:
    """Placeholder for the actual Gemini API call with retry logic."""
    logger.info("Attempting to call GenAI for context detection...")
    # --- Placeholder for GenAI API call ---
    # Example (replace with actual implementation later):
    # try:
    #     response = genai_client.generate_content(prompt)
    #     detected_context = response.text.strip()
    #     logger.info(f"GenAI detected context: {detected_context}")
    #     return detected_context
    # except Exception as e:
    #     logger.error(f"Error calling GenAI for context detection: {e}")
    #     raise ContextDetectionError(f"GenAI API call failed: {e}") from e
    # --- End Placeholder ---

    # For now, raise error as it's not implemented
    raise ContextDetectionError("GenAI API call for context detection not implemented.")


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
        return "General conversation (mock)"

    elif speed_mode in ["fast", "normal"]:
        if genai_client is None:
            logger.error("GenAI client is required for 'fast' or 'normal' mode but was not provided.")
            raise ValueError("GenAI client is required for 'fast'/'normal' mode.")

        logger.debug(f"Preparing text for GenAI context detection (mode: {speed_mode}).")

        if not sub or not sub[0]:
            logger.warning("Subtitle data is empty, cannot detect context.")
            return "Unknown (empty input)"

        # Extract text from the first chunk (approx first 100 lines)
        first_chunk = sub[0]
        text_lines = [block.content for block in first_chunk]
        combined_text = "\n".join(text_lines[:100]) # Limit to roughly 100 lines

        if not combined_text.strip():
             logger.warning("Extracted text for context detection is empty.")
             return "Unknown (no text content)"

        logger.debug(f"Extracted text for context detection (first {len(text_lines[:100])} lines):\n{combined_text[:200]}...") # Log beginning of text

        # --- Placeholder for Prompt Construction ---
        # Define the prompt for the Gemini API
        # Example:
        prompt = f"Determine the general topic or context of the following subtitle dialogue:\n\n---\n{combined_text}\n---\n\nContext:"
        logger.debug("Prompt constructed for GenAI.")
        # --- End Placeholder ---

        # Configure retry attempts based on config
        retry_decorator = retry(
            stop=stop_after_attempt(config.retry_max_attempts),
            wait=wait_fixed(1),
            retry=retry_if_exception_type(Exception), # Keep broad retry for now
            reraise=True
        )

        try:
            # Apply the configured retry decorator to the API call function
            wrapped_genai_call = retry_decorator(_call_genai_context_detection)
            detected_context = wrapped_genai_call(prompt=prompt, genai_client=genai_client)
            return detected_context
        except ContextDetectionError as e:
             # Reraise our specific error
             logger.error(f"Context detection failed after retries: {e}")
             raise e
        except Exception as e:
            # Catch any other unexpected errors during the process
            logger.error(f"An unexpected error occurred during context detection: {e}", exc_info=True)
            raise ContextDetectionError(f"Unexpected error during context detection: {e}") from e

    else:
        logger.error(f"Invalid speed_mode: {speed_mode}")
        raise ValueError(f"Invalid speed_mode: {speed_mode}. Must be 'mock', 'fast', or 'normal'.")
