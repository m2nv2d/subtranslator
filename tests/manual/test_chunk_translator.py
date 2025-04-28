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
from translator import init_genai_client, parse_srt, detect_context, translate_all_chunks
from translator import ChunkTranslationError

logger = logging.getLogger(__name__)

async def main():
    parser = argparse.ArgumentParser(description="Manual test script for chunk_translator.")
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
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set the logging level (default: INFO)"
    )

    args = parser.parse_args()
    
    # Setup logging with user-specified level
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    srt_file_path = project_root / 'tests' / 'samples' / f"{args.name}.srt"
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

    # --- Parse SRT File ---
    try:
        subtitle_chunks = parse_srt(str(srt_file_path), settings.CHUNK_MAX_BLOCKS)
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
        logging.info("Detecting context...")
        detected_context = detect_context(
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
    logging.info(f"Starting chunk translation for {target_lang}...")
    try:
        await translate_all_chunks(
            context=context,
            sub=subtitle_chunks,
            target_lang=target_lang,
            speed_mode=args.speed_mode,
            client=genai_client if args.speed_mode != "mock" else None,
            settings=settings
        )
        logging.info("Chunk translation completed.")

        # --- Print Results (First 20 blocks) ---
        logging.info("--- Translation Results (First 20 blocks) ---")
        block_count = 0
        total_blocks = sum(len(chunk) for chunk in subtitle_chunks)
        print(f"Total blocks parsed: {total_blocks}")

        if not subtitle_chunks or not subtitle_chunks[0]:
            logging.error("No subtitle data to display.")
            return

        for chunk in subtitle_chunks:
            if block_count >= 20:
                break
            for block in chunk:
                if block_count >= 20:
                    break
                print(f"Block {block.index}:")
                print(f"  Original: {block.content}")
                print(f"  Translated: {block.translated_content if block.translated_content else '[No Translation]'}")
                block_count += 1

        if block_count == 0:
            print("No subtitle blocks were processed or found.")

    except ChunkTranslationError as e:
        logging.error(f"\n--- Chunk Translation Failed --- Error: {e}")
    except Exception as e:
        logging.exception(f"\n--- An unexpected error occurred during translation --- Error: {e}") # Use logging.exception for traceback

if __name__ == "__main__":    
    asyncio.run(main())
