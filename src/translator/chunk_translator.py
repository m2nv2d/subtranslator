import asyncio
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type, before_sleep_log, RetryError
from functools import wraps

import json
import logging

from google import genai
from google.genai import types

from typing import Optional, Tuple
from pydantic import BaseModel, RootModel

from translator.models import SubtitleBlock
from translator.exceptions import ChunkTranslationError
from core.config import Settings

class TranslatedBlock(BaseModel):
    index: int
    translated_lines: list[str]

TranslatedChunk = RootModel[list[TranslatedBlock]]

def configurable_retry(f):
    @wraps(f)
    async def wrapper(*args, **kwargs):
        # Extract settings and chunk_index from the function arguments more safely
        settings = kwargs.get('settings')
        chunk_index = kwargs.get('chunk_index')
        
        if settings is None:
            # Should not happen if called correctly from translate_all_chunks
            logging.getLogger(__name__).error("Settings object missing in retry decorator call.")
            raise ValueError("Could not find settings in arguments")
        if chunk_index is None:
            logging.getLogger(__name__).error("chunk_index missing in retry decorator call.")
            raise ValueError("Could not find chunk_index in arguments")

        logger = logging.getLogger(__name__)
        max_attempts = settings.RETRY_MAX_ATTEMPTS
        
        current_attempt = 0
        failed = False

        @retry(
            stop=stop_after_attempt(max_attempts),
            wait=wait_fixed(1), # Consider making wait configurable settings.RETRY_WAIT_SECONDS
            retry=retry_if_exception_type(Exception),
            before_sleep=before_sleep_log(logger, logging.WARNING, exc_info=False), # Log before retry
            reraise=True # Reraise the last exception if all attempts fail
        )
        async def retry_target(*args, **kwargs):
            nonlocal current_attempt
            current_attempt += 1
            logger.debug(f"Chunk {chunk_index} starting attempt {current_attempt}/{max_attempts}")
            try:
                result = await f(*args, **kwargs)
                # Success on this attempt
                logger.info(f"Chunk {chunk_index} succeeded on attempt {current_attempt}/{max_attempts}")
                return result # Pass through the original result (which is None for _translate_single_chunk)
            except asyncio.CancelledError:
                logger.warning(f"Chunk {chunk_index} translation was cancelled on attempt {current_attempt}")
                raise # Re-raise CancelledError to stop retries immediately
            except Exception as e:
                if current_attempt >= max_attempts:
                    logger.error(f"Chunk {chunk_index} failed final attempt {current_attempt}/{max_attempts}")
                else:
                    logger.warning(f"Chunk {chunk_index} failed attempt {current_attempt}/{max_attempts}, retrying... Error: {e}")
                raise # Re-raise exception to trigger tenacity's retry or final failure

        try:
            await retry_target(*args, **kwargs)
            # If retry_target succeeds without raising final exception:
            failed = False
        except asyncio.CancelledError:
            logger.warning(f"Chunk {chunk_index} translation cancelled definitively.")
            # Decide how to report cancelled status? For now, treat as failure with max attempts?
            # Or re-raise? Re-raising seems more appropriate.
            raise
        except Exception as e: # Catches the final exception reraised by tenacity
            logger.error(f"Chunk {chunk_index} ultimately failed after {current_attempt} attempts. Final Error: {e}")
            failed = True
            # We don't need to return the original result of f, just the stats

        # Calculate retries (attempts - 1)
        retries = max(0, current_attempt - 1)
        return retries, failed # Return Tuple[int, bool]

    return wrapper

@configurable_retry
async def _translate_single_chunk(
    chunk_index: int,
    chunk: list[SubtitleBlock],
    system_prompt: str,
    response_schema: genai.types.Schema,
    speed_mode: str,
    genai_client: Optional[genai.client.Client],
    settings: Settings,
    semaphore: asyncio.Semaphore,
) -> None: # Original function still logically returns None, the decorator wraps this
    """
    Translates a single chunk of subtitle blocks.
    Applies retry logic based on the provided configuration.
    Currently implements 'mock' translation and has a placeholder for real translation.
    Acquires a semaphore slot before performing the translation.
    
    NOTE: This function's success/failure and retries are managed by the
          @configurable_retry decorator, which returns Tuple[int, bool].
          The function itself focuses on the translation logic for one attempt.
    """
    async with semaphore: # Acquire semaphore lock
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

            model_to_use = settings.FAST_MODEL if speed_mode == "fast" else settings.NORMAL_MODEL
                
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
                    response_mime_type='application/json',
                    response_schema=response_schema,
                    system_instruction=[
                        types.Part.from_text(text=system_prompt),
                    ],
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                )
            )

            # Parse response
            try:                
                # Validate JSON structure against TranslatedChunk model
                try:
                    validated_chunk = TranslatedChunk.model_validate_json(response.text)
                except Exception as e:
                    raise ChunkTranslationError(f"Response does not match expected schema: {str(e)}")
                
                # Process validated data
                for block_data in validated_chunk.model_dump():
                    block_index = block_data['index']
                    # Join all translated lines with newlines
                    translated_content = "\n".join(block_data['translated_lines'])
                    
                    # Ensure the block index is valid
                    if 0 <= block_index < len(chunk):
                        chunk[block_index].translated_content = translated_content
                    else:
                        raise ChunkTranslationError(f"Invalid block index {block_index} received in translation response for chunk {chunk_index}.")
                
                logging.debug(f"Parsed JSON response:\n---RESPONSE---\n{response.text}\n-----END-----\n")            

            except json.JSONDecodeError:
                raise ChunkTranslationError(f"Failed to parse JSON response")
            except IndexError:
                # Handle potential IndexError if block_index is out of bounds
                raise ChunkTranslationError(f"Invalid block index {block_index} received in translation response for chunk {chunk_index}.")
            except KeyError as e:
                 # Handle potential KeyError if 'index' or 'translated_line_x' is missing
                raise ChunkTranslationError(f"Missing key {e} in translation response for chunk {chunk_index}.")

async def translate_all_chunks(
    context: str,
    sub: list[list[SubtitleBlock]],
    target_lang: str,
    speed_mode: str,
    client: Optional[genai.client.Client],
    settings: Settings,
    semaphore: asyncio.Semaphore,
) -> Tuple[int, int]: # Updated return type
    """
    Orchestrates the concurrent translation of multiple subtitle chunks using TaskGroup.
    Returns aggregated statistics: (total_failed_attempts, total_chunks_with_failures).
    """
    system_prompt = f"""
    You're a video subtitle translator. {context} I'll give you content of srt subtitle blocks, including its index. You should translate it into {target_lang}.

    Make sure to return in structured JSON array [...]. Ignore timestamps if there are. The output JSON contains a list, where each item in the list is an object that contains two required properties: "index" and "translated_lines". The "index" property is the integer index as provided in the input. The "translated_lines" property is itself a list made up of text strings, one for each line in the translated subtitle block. Break up the lines just like the original blocks for readability. Don't merge two lines of the same blockinto one.
    """

    response_schema = genai.types.Schema(
        type = genai.types.Type.ARRAY,
        items = genai.types.Schema(
            type = genai.types.Type.OBJECT,
            required = ["index", "translated_lines"],
            properties = {
                "index": genai.types.Schema(
                    type = genai.types.Type.INTEGER,
                ),
                "translated_lines": genai.types.Schema(
                    type = genai.types.Type.ARRAY,
                    items = genai.types.Schema(
                        type = genai.types.Type.STRING,
                    ),
                ),
            },
        ),
    )

    logging.info(f"Starting translation for {len(sub)} chunks concurrently...")
    tasks = []
    try:
        async with asyncio.TaskGroup() as tg:
            # Create tasks for each chunk within the TaskGroup
            for i, chunk in enumerate(sub):
                task = tg.create_task(
                    _translate_single_chunk(
                        chunk_index=i,
                        chunk=chunk,
                        system_prompt=system_prompt,
                        response_schema=response_schema,
                        speed_mode=speed_mode,
                        genai_client=client,
                        settings=settings,
                        semaphore=semaphore,
                    )
                )
                tasks.append(task)
        
        # If TaskGroup finishes without exception, all tasks completed (possibly with failures handled by decorator)
        logging.info(f"All {len(tasks)} translation tasks completed or failed gracefully.")

    except* Exception as eg: # Catch potential ExceptionGroup
         # Some task(s) raised an exception not handled by the decorator (e.g., CancelledError)
         logging.error(f"ExceptionGroup caught during chunk translation: {eg.exceptions}")
         # We still try to collect stats from completed/failed tasks below
    
    # Aggregate results from tasks
    total_failed_attempts = 0
    total_chunks_with_failures = 0

    for i, task in enumerate(tasks):
        if task.done():
            try:
                # Accessing task.result() re-raises exception if task failed unexpectedly
                # Or returns the (retries, failed_flag) tuple if decorator handled it
                retries, failed_flag = task.result()
                total_failed_attempts += retries
                if failed_flag:
                    total_chunks_with_failures += 1
                    logging.warning(f"Chunk {i} reported failure (failed_flag=True) with {retries} retries.")
                else:
                    logging.debug(f"Chunk {i} reported success with {retries} retries.")
            except asyncio.CancelledError:
                 logger.warning(f"Task for chunk {i} was cancelled.")
                 # Treat cancellation as a failure for stats?
                 # Let's count it as a failure, attempts unknown (or assume max?)
                 total_chunks_with_failures += 1
                 # total_failed_attempts += settings.RETRY_MAX_ATTEMPTS -1 # Optionally add max retries
            except Exception as e:
                # Unexpected exception from task.result() (shouldn't happen if decorator handles all)
                logger.error(f"Unexpected error getting result for chunk {i}: {e}", exc_info=True)
                total_chunks_with_failures += 1 # Count as failure
                # total_failed_attempts += settings.RETRY_MAX_ATTEMPTS -1 # Optionally add max retries
        else:
             # This case should ideally not happen if TaskGroup completes
             logger.error(f"Task for chunk {i} was not done after TaskGroup finished.")

    logging.info(f"Aggregated translation stats: Total Failed Attempts={total_failed_attempts}, Chunks With Failures={total_chunks_with_failures}")

    # Modify the subtitle list 'sub' in-place (already done by _translate_single_chunk)
    
    # Return the aggregated statistics
    return total_failed_attempts, total_chunks_with_failures
