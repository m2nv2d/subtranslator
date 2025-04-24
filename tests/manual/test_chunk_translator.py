import asyncio
import argparse
import sys
import logging
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

from src.config_loader import load_config
from src.gemini_helper import init_genai_client
from src.chunk_translator import translate_all_chunks
from src.exceptions import ChunkTranslationError
from src.parser import parse_srt
from src.context_detector import detect_context

async def main():
    parser = argparse.ArgumentParser(description="Manual test script for chunk_translator.")
    parser.add_argument(
        "srt_file",
        type=str,
        help="Path to the input SRT file."
    )
    parser.add_argument(
        "--speed-mode",
        type=str,
        default="mock",
        choices=["mock", "fast", "normal"],
        help="Translation mode ('mock', 'fast', or 'normal')."
    )

    args = parser.parse_args()

    logging.info(f"Running test with srt_file: {args.srt_file}, speed_mode: {args.speed_mode}")

    # --- Load Configuration ---
    try:
        config = load_config()
        target_lang = config.target_languages[0]
    except Exception as e:
        logging.error(f"Error loading configuration: {e}")
        return

    # --- Initialize GenAI Client ---
    genai_client = None
    if args.speed_mode != "mock":
        try:
            # Ensure API key is handled (e.g., via environment variables)
            genai_client = init_genai_client(config=config)
            logging.info("Gemini client initialized.")
        except Exception as e:
            logging.error(f"Error initializing Gemini client: {e}. Cannot run 'real' mode.")
            return

    # --- Parse SRT File ---
    try:
        subtitle_chunks = parse_srt(args.srt_file, config.chunk_max_blocks)
        logging.info(f"Parsed {len(subtitle_chunks)} chunks from the file.")
        if not subtitle_chunks:
            logging.error("No subtitle chunks found in the file.")
            return
    except FileNotFoundError:
        logging.error(f"SRT file not found: {args.srt_file}")
        return
    except Exception as e:
        logging.error(f"Error parsing SRT file: {e}")
        return

    # --- Detect Context ---
    try:
        logging.info("\nDetecting context...")
        detected_context = detect_context(
            sub=subtitle_chunks,
            speed_mode=args.speed_mode,
            genai_client=genai_client if args.speed_mode != "mock" else None,
            config=config
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
    logging.info(f"\nStarting chunk translation for {target_lang}...")
    try:
        await translate_all_chunks(
            context=context,
            sub=subtitle_chunks,
            target_lang=target_lang,
            speed_mode=args.speed_mode,
            genai_client=genai_client if args.speed_mode != "mock" else None,
            config=config
        )
        logging.info("\nChunk translation completed.")

        # --- Print Results (First 20 blocks) ---
        logging.info("\n--- Translation Results (First 20 blocks) ---")
        block_count = 0
        total_blocks = sum(len(chunk) for chunk in subtitle_chunks)
        logging.info(f"Total blocks parsed: {total_blocks}")

        if not subtitle_chunks or not subtitle_chunks[0]:
            logging.error("No subtitle data to display.")
            return

        for chunk in subtitle_chunks:
            if block_count >= 20:
                break
            for block in chunk:
                if block_count >= 20:
                    break
                logging.info(f"\nBlock {block.index}:")
                logging.info(f"  Original: {block.content}")
                logging.info(f"  Translated: {block.translated_content if block.translated_content else '[No Translation]'}")
                block_count += 1

        if block_count == 0:
            print("No subtitle blocks were processed or found.")

    except ChunkTranslationError as e:
        logging.error(f"\n--- Chunk Translation Failed --- Error: {e}")
    except Exception as e:
        logging.exception(f"\n--- An unexpected error occurred during translation --- Error: {e}") # Use logging.exception for traceback

if __name__ == "__main__":
    # --- Logging Configuration --- 
    logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    asyncio.run(main())
