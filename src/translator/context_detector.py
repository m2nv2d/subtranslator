import logging
import asyncio
import random
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type
from functools import wraps

from google import genai
from google.genai import types

from translator.exceptions import ContextDetectionError
from translator.models import SubtitleBlock
from core.config import Settings

logger = logging.getLogger(__name__)

async def _call_openrouter_text_api(
    model: str,
    system_prompt: str,
    user_prompt: str,
    api_key: str
) -> str:
    """
    Helper function to make async API calls to OpenRouter for text responses.
    Returns the response text.
    """
    import aiohttp
    
    messages = [
        {
            "role": "system",
            "content": [{"type": "text", "text": system_prompt}]
        },
        {
            "role": "user", 
            "content": [{"type": "text", "text": user_prompt}]
        }
    ]
    
    payload = {
        "model": model,
        "messages": messages
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload
        ) as response:
            if response.status != 200:
                error_text = await response.text()
                raise ContextDetectionError(f"OpenRouter API error: {response.status} - {error_text}")
            
            result = await response.json()
            return result["choices"][0]["message"]["content"]

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
    sub: list[list[SubtitleBlock]],
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
        # Speed-based delay: fast mode = 5-8 seconds, normal mode = 8-13 seconds
        delay = random.uniform(5.0, 8.0)  # Default to fast timing for backward compatibility
        logger.debug(f"Mock context detection will take {delay:.2f} seconds")
        await asyncio.sleep(delay)
        return "Mock Context Detected"

    elif speed_mode in ["fast", "normal"]:
        # Prepare prompt for GenAI
        content = "\n".join([block.content for block in sub[0]])
        system_prompt = "You are a context detector. Your task is to analyze the subtitle content provided and determine the general context in one sentence. Only give me that context read to use. If it's a movie, just give a general theme. If a vlog/tutorial, the general topic the speaker(s) are talking about. The template is: This is a subtitle for a movie/vlog/tutorial/... for/of/about ..."
        request_prompt = f"{content}"

        model_to_use = settings.FAST_MODEL if speed_mode == "fast" else settings.NORMAL_MODEL
        
        # Check if using OpenRouter provider
        if settings.AI_PROVIDER == "openrouter":
            return await _call_openrouter_text_api(
                model=model_to_use,
                system_prompt=system_prompt,
                user_prompt=request_prompt,
                api_key=settings.AI_API_KEY
            )
        elif settings.AI_PROVIDER == "google-gemini":
            # Google Gemini provider
            response = await genai_client.aio.models.generate_content(
                model=model_to_use,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(text=request_prompt),
                        ],
                    )
                ],
                config=types.GenerateContentConfig(
                    response_mime_type='text/plain',
                    system_instruction=[
                        types.Part.from_text(text=system_prompt),
                    ],
                    thinking_config=types.ThinkingConfig(thinking_budget=0) if speed_mode == "fast" else None
                )
            )
            return response.text

    else:
        logger.error(f"Invalid speed_mode: {speed_mode}")
        raise ContextDetectionError(f"Invalid speed_mode: {speed_mode}. Must be 'mock', 'fast', or 'normal'.")
