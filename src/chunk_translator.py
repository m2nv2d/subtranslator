import asyncio
import tenacity
from typing import List, Optional
import json
import logging

from google import genai
from google.genai import types
from gemini_helper import FAST_MODEL, NORMAL_MODEL

from models import Config, SubtitleBlock
from exceptions import ChunkTranslationError

@tenacity.retry(
    stop=tenacity.stop_after_attempt(3), # Default value, will be set dynamically later
    wait=tenacity.wait_fixed(1), # Example: wait 1 second between retries
    retry=tenacity.retry_if_exception_type(Exception), # Retry on any exception for now
    reraise=True # Reraise the exception after retries are exhausted
)
async def _translate_single_chunk(
    chunk_index: int,
    chunk: List[SubtitleBlock],
    system_prompt: str,
    speed_mode: str,
    genai_client: Optional[genai.client.Client],
    config: Config
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

        logging.info(f"Chunk {chunk_index} sent for translation.")
        if speed_mode == "fast":
            response = await genai_client.aio.models.generate_content(
                model=FAST_MODEL,
                contents=[system_prompt, request_prompt],
                config=types.GenerateContentConfig(
                    response_mime_type='application/json',
                )
            )
        else:
            response = await genai_client.aio.models.generate_content(
                model=NORMAL_MODEL,
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
            logging.info(f"Chunk {chunk_index} processed successfully.")

        except json.JSONDecodeError:
            raise ChunkTranslationError(f"Failed to parse JSON response: {response}")

async def translate_all_chunks(
    context: str,
    sub: List[List[SubtitleBlock]],
    target_lang: str,
    speed_mode: str,
    genai_client: Optional[genai.client.Client], # Made optional
    config: Config
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

    logging.debug(f"Starting translation for {len(sub)} chunks...")
    try:
        async with asyncio.TaskGroup() as tg:
            for i, chunk in enumerate(sub):
                tg.create_task(
                    _translate_single_chunk(
                        chunk_index=i,
                        chunk=chunk,
                        system_prompt=system_prompt,
                        speed_mode=speed_mode,
                        genai_client=genai_client,
                        config=config
                    ),
                    name=f"translate_chunk_{i}"
            )

        logging.debug("All chunks processed successfully.")
    except Exception as e:
        # If any task fails (even after retries), gather will raise the first exception.
        logging.error(f"Error during chunk translation: {e}")
        raise ChunkTranslationError(f"Failed to translate one or more chunks: {e}") from e
