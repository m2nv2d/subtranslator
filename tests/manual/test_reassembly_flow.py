import asyncio
import argparse
import sys
import logging
from pathlib import Path

# Add project root's src to sys.path
project_root = Path(__file__).resolve().parents[2]
src_root = project_root / 'src'
sys.path.insert(0, str(src_root))

from core.config import get_settings
from translator import init_genai_client, parse_srt, translate_all_chunks, detect_context, reassemble_srt
from translator import ChunkTranslationError

async def main():
    parser = argparse.ArgumentParser(description="Manual test script for reassembly flow.")
    parser.add_argument(
        "name",
        choices=['short', 'medium', 'long'],
        help="Name of the sample file to parse (short.srt, medium.srt, or long.srt)."
    )
    parser.add_argument(
        "--speed-mode",
        type=str,
        default="fast",
        choices=["mock", "fast", "normal"],
        help="Translation mode ('mock', 'fast', or 'normal')."
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        help="Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR, CRITICAL)."
    )

    args = parser.parse_args()
    
    srt_file_path = project_root / 'tests' / 'samples' / f"{args.name}.srt"

    # Setup logging with user-specified level
    logging.basicConfig(
        level=args.log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    for pkg in ["httpx", "google_genai"]:
        logging.getLogger(pkg).setLevel(logging.WARNING)


    logging.info(f"Running test with srt_file: {srt_file_path}, speed_mode: {args.speed_mode}")

    # --- Load Configuration ---
    try:
        settings = get_settings()
        target_lang = settings.TARGET_LANGUAGES[0]
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        return

    # --- Initialize GenAI Client ---
    genai_client = None
    if args.speed_mode != "mock":
        try:
            # Ensure API key is handled (e.g., via environment variables)
            genai_client = init_genai_client(settings)
            logging.info("Gemini client initialized.")
        except Exception as e:
            logging.error(f"Error initializing Gemini client: {e}. Cannot run 'real' mode.")
            return

    # --- Initialize Semaphore ---
    # Since this runs outside FastAPI, manually create the semaphore
    semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_TRANSLATIONS)
    logging.info(f"Manual test: Initialized semaphore with limit {settings.MAX_CONCURRENT_TRANSLATIONS}")

    # --- Parse SRT File ---
    try:
        subtitle_chunks = await parse_srt(str(srt_file_path), settings.CHUNK_MAX_BLOCKS)
        logging.info(f"Parsed {len(subtitle_chunks)} chunks from the file.")
        if not subtitle_chunks:
            logging.error("No subtitle chunks found in the file.")
            return
    except FileNotFoundError:
        logging.error(f"SRT file not found: {srt_file_path}")
        return
    except Exception as e:
        logging.error(f"Error parsing SRT file: {e}")
        return

    # --- Detect Context ---
    try:
        detected_context = await detect_context(
            sub=subtitle_chunks,
            speed_mode=args.speed_mode,
            genai_client=genai_client if args.speed_mode != "mock" else None,
            settings=settings
        )
        if detected_context:
            logging.info(f"Detected Context: {detected_context}")
            context = detected_context
        else:
            logging.warning("Could not detect context automatically. Using default prompts.")
            # Fallback to default context if detection fails
            context = f"Translate the following subtitles into {target_lang}. Maintain the timing and context."

    except Exception as e:
        logging.error(f"Error during context detection: {e}")


    # --- Run the translator ---
    try:
        await translate_all_chunks(
            context=context,
            sub=subtitle_chunks,
            target_lang=target_lang,
            speed_mode=args.speed_mode,
            client=genai_client if args.speed_mode != "mock" else None,
            settings=settings,
            semaphore=semaphore # Pass the manually created semaphore
        )
        logging.info("Chunk translation completed.")

    except ChunkTranslationError as e:
        raise RuntimeError("Chunk translation failed, cannot proceed to reassembly.")
    except Exception as e:
        raise RuntimeError("Translation failed, cannot proceed to reassembly.")

    # --- Run the reassembly ---
    logging.info(f"Starting reassembly...")
    try:
        reassembled_content = reassemble_srt(subtitle_chunks)
        # Save the reassembled content to the new SRT file
        output_filename = f"{args.name}_translated.srt"
        output_path = srt_file_path.parent / output_filename
        try:
            with open(output_path, 'wb') as f:
                f.write(reassembled_content)
            logging.info(f"Reassembled content saved to: {output_path}")
        except IOError as e:
            logging.error(f"Error writing reassembled content to file {output_path}: {e}")
    except Exception as e:
        logging.error(f"--- Reassembly Failed --- Error: {e}")

if __name__ == "__main__":    
    asyncio.run(main())