import asyncio
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type, before_sleep_log
from functools import wraps

from typing import List, Optional
import json
import logging

from google import genai
from google.genai import types

from translator.models import SubtitleBlock
from translator.exceptions import ChunkTranslationError
from core.config import Settings

def configurable_retry(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        # Extract settings and chunk_index from the function arguments more safely
        settings = kwargs.get('settings')
        chunk_index = kwargs.get('chunk_index')
        
        # If not in kwargs, try to find them in args by matching the function signature
        if settings is None or chunk_index is None:
            # Get the parameter names from the function
            from inspect import signature
            sig = signature(f)
            param_names = list(sig.parameters.keys())
            
            # Find positions of settings and chunk_index in the signature
            if settings is None and 'settings' in param_names:
                settings_pos = param_names.index('settings')
                if len(args) > settings_pos:
                    settings = args[settings_pos]
            
            if chunk_index is None and 'chunk_index' in param_names:
                chunk_pos = param_names.index('chunk_index')
                if len(args) > chunk_pos:
                    chunk_index = args[chunk_pos]
        
        if settings is None:
            raise ValueError("Could not find settings in arguments")
        if chunk_index is None:
            raise ValueError("Could not find chunk_index in arguments")

        logger = logging.getLogger(__name__)
        attempt_count = 0

        @retry(
            stop=stop_after_attempt(settings.RETRY_MAX_ATTEMPTS),
            wait=wait_fixed(1),
            retry=retry_if_exception_type(Exception),
            before_sleep=before_sleep_log(logger, logging.INFO, exc_info=True),
            reraise=True
        )
        async def wrapped_f(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            try:
                result = await f(*args, **kwargs)
                logger.info(f"Chunk {chunk_index} succeeded on attempt {attempt_count}/{settings.RETRY_MAX_ATTEMPTS}")
                return result
            except Exception as e:
                if attempt_count >= settings.RETRY_MAX_ATTEMPTS:
                    logger.error(f"Chunk {chunk_index} failed after all {attempt_count} attempts")
                else:
                    logger.warning(f"Chunk {chunk_index} failed on attempt {attempt_count}/{settings.RETRY_MAX_ATTEMPTS}, retrying...")
                raise
        
        return await wrapped_f(*args, **kwargs)
    return wrapper

@configurable_retry
async def _translate_single_chunk(
    chunk_index: int,
    chunk: List[SubtitleBlock],
    system_prompt: str,
    speed_mode: str,
    genai_client: Optional[genai.client.Client],
    settings: Settings,
    retry_max_attempts: int = None,
    normal_model: str = None,
    fast_model: str = None
) -> None:
    """
    Translates a single chunk of subtitle blocks.

    Applies retry logic based on the provided configuration.
    Currently implements 'mock' translation and has a placeholder for real translation.
    """

    if speed_mode == "mock":
        # Mock Logic: Copy original content to translated_content
        for block in chunk:
            block.translated_content = block.content
        await asyncio.sleep(0.1)
        print(f"Chunk {chunk_index} processed (mock).")
    else:
        request_prompt = ""
        for i, block in enumerate(chunk):
            request_prompt += f"\n{i}\n{block.content}\n"

        model_to_use = fast_model if speed_mode == "fast" else normal_model
        if model_to_use is None:
            model_to_use = settings.FAST_MODEL if speed_mode == "fast" else settings.NORMAL_MODEL
            
        response = await genai_client.aio.models.generate_content(
            model=model_to_use,
            contents=[system_prompt, request_prompt],
            config=types.GenerateContentConfig(
            response_mime_type='application/json',
            )
        )

        # Parse response
        try:
            translated_json = json.loads(response.text)
            for block in translated_json:
                block_index = block['index']
                translated_lines = ""
                i = 1
                while f'translated_line_{i}' in block:
                    if translated_lines:
                        translated_lines += "\n"
                    translated_lines += block[f'translated_line_{i}']
                    i += 1
                chunk[block_index].translated_content = translated_lines
            logging.debug(f"Parsed JSON response:\n---RESPONSE---\n{response.text}\n-----END-----\n")            

        except json.JSONDecodeError:
            raise ChunkTranslationError(f"Failed to parse JSON response")

async def translate_all_chunks(
    context: str,
    sub: List[List[SubtitleBlock]],
    target_lang: str,
    speed_mode: str,
    client: Optional[genai.client.Client],
    settings: Settings,
    retry_max_attempts: int = None,
    normal_model: str = None,
    fast_model: str = None
) -> None:
    """
    Orchestrates the concurrent translation of multiple subtitle chunks.
    """
    system_prompt = f"""
    You're a video subtitle translator. {context} I'll give you content of srt subtitle blocks, including its index. You should translate it into {target_lang}.

    Make sure to return in structured JSON array [...]. Each item inside the array will be a JSON object {...} following the structure:
    "index": The original index of the subtitle block.
    "translated_line_1": The first line of the translation.
    "translated_line_2": The second line (if it exists).
    ... and so on for subsequent lines within the same block.
    """

    logging.info(f"Starting translation for {len(sub)} chunks...")
    tasks = []
    
    # Create tasks for each chunk
    for i, chunk in enumerate(sub):
        task = _translate_single_chunk(
            chunk_index=i,
            chunk=chunk,
            system_prompt=system_prompt,
            speed_mode=speed_mode,
            genai_client=client,
            settings=settings,
            retry_max_attempts=retry_max_attempts,
            normal_model=normal_model,
            fast_model=fast_model
        )
        tasks.append(task)
    
    # Run all tasks and collect errors
    failed_chunks = []
    try:
        # Return_exceptions=True means gather will complete all tasks even if some fail
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check results for exceptions
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_chunks.append((i, result))
                logging.error(f"Chunk {i} failed: {result}")
        
        if failed_chunks:
            error_details = "\n".join(f"Chunk {i}: {err}" for i, err in failed_chunks)
            raise ChunkTranslationError(f"Failed to translate chunks after all retries:\n{error_details}")
        
        logging.debug("All chunks processed successfully.")
    except Exception as e:
        # This will only happen for errors outside of the tasks themselves
        logging.error(f"Error during chunk translation orchestration: {e}")
        raise ChunkTranslationError(f"Failed to orchestrate chunk translation: {e}") from e
